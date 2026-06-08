import torch
import torch.nn as nn
import torch.optim as optim
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from ..db.models import Move, Game
from ..db import crud
from .agent import (ChessNet, board_to_tensor, MODEL_PATH,
                    get_model, get_stats, save_stats)
import chess
import os
import random

# ── Piece Values ───────────────────────────────────────
PIECE_VALUES = {
    chess.PAWN:   1.0,
    chess.KNIGHT: 3.0,
    chess.BISHOP: 3.0,
    chess.ROOK:   5.0,
    chess.QUEEN:  9.0,
    chess.KING:   0.0
}

def calculate_move_reward(board: chess.Board,
                           move: chess.Move,
                           player: str) -> float:
    reward = 0.0

    if board.is_capture(move):
        captured_piece = board.piece_at(move.to_square)
        if board.is_en_passant(move):
            captured_piece_type = chess.PAWN
        elif captured_piece:
            captured_piece_type = captured_piece.piece_type
        else:
            captured_piece_type = chess.PAWN

        piece_value = PIECE_VALUES.get(captured_piece_type, 0.0)

        if player == "ai":
            reward += piece_value
            print(f"🤖 AI captured piece worth +{piece_value}")
        else:
            reward -= piece_value
            print(f"😤 Human captured AI piece -{piece_value}")

    board.push(move)
    if board.is_check():
        if player == "ai":
            reward += 0.5
        else:
            reward -= 0.5
    board.pop()

    if move.promotion:
        if player == "ai":
            reward += 8.0
        else:
            reward -= 8.0

    return reward


def calculate_game_end_reward(winner: str) -> float:
    if winner == "ai":
        return 100.0
    elif winner == "human":
        return -100.0
    else:
        return 10.0


async def train_after_game(db: AsyncSession, game_id: int):
    print(f"🧠 Training on game {game_id}...")

    # Get moves
    result = await db.execute(
        select(Move).where(
            Move.game_id == game_id
        ).order_by(Move.move_number)
    )
    moves = result.scalars().all()

    if len(moves) < 5:
        print("⚠️ Too few moves to train on")
        return

    # Get game result
    game_result = await db.execute(
        select(Game).where(Game.id == game_id)
    )
    game = game_result.scalar_one_or_none()
    if not game:
        return

    final_reward = calculate_game_end_reward(game.winner)
    print(f"🏆 Game end reward: {final_reward} (winner: {game.winner})")

    # Build training data
    states = []
    targets = []
    board = chess.Board()
    discount = 0.99

    for i, move in enumerate(moves):
        try:
            chess_move = chess.Move.from_uci(move.move_uci)
            tensor = board_to_tensor(board)
            steps_from_end = len(moves) - i
            discounted_end = final_reward * (discount ** steps_from_end)
            total_reward = move.reward + discounted_end
            states.append(tensor)
            targets.append(total_reward)
            board.push(chess_move)
        except Exception as e:
            print(f"⚠️ Skipping move {move.move_uci}: {e}")
            continue

    if not states:
        return

    # ── Train the model ────────────────────────────────
    model = get_model()
    model.train()
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    criterion = nn.MSELoss()

    states_tensor = torch.stack(states)
    targets_tensor = torch.FloatTensor(targets).unsqueeze(1)

    # Normalize targets to prevent exploding gradients
    targets_mean = targets_tensor.mean()
    targets_std = targets_tensor.std() + 1e-8
    targets_normalized = (targets_tensor - targets_mean) / targets_std

    total_loss = 0
    # More epochs = more learning per game!
    for epoch in range(50):
        optimizer.zero_grad()
        predictions = model(states_tensor)
        loss = criterion(predictions, targets_normalized)
        loss.backward()
        # Clip gradients to prevent instability
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        total_loss = loss.item()

    # Save model
    os.makedirs("model_weights", exist_ok=True)
    torch.save(model.state_dict(), MODEL_PATH)
    model.eval()

    # ── Update training stats ──────────────────────────
    stats = get_stats()
    stats["total_games"] += 1

    if game.winner == "ai":
        stats["wins"] += 1
    elif game.winner == "human":
        stats["losses"] += 1
    else:
        stats["draws"] += 1

    # Decay epsilon — less random as more games played
    # Starts at 1.0, decays to minimum 0.1
    old_epsilon = stats["epsilon"]
    stats["epsilon"] = max(0.1, stats["epsilon"] * 0.95)

    # Track loss and reward history
    avg_reward = float(sum(targets) / len(targets))
    stats["loss_history"].append(round(total_loss, 4))
    stats["reward_history"].append(round(avg_reward, 4))

    total = stats["total_games"]
    win_rate = round(stats["wins"] / total * 100, 1)
    stats["win_rate_history"].append(win_rate)

    save_stats(stats)

    print(f"✅ Training complete!")
    print(f"📉 Loss: {total_loss:.4f}")
    print(f"🎯 Epsilon: {old_epsilon:.3f} → {stats['epsilon']:.3f}")
    print(f"📊 Win rate: {win_rate}% ({stats['wins']}/{total})")
    print(f"💾 Model saved!")

    # Save metrics to DB
    try:
        wins_result = await db.execute(
            select(func.count(Game.id)).where(Game.winner == "ai")
        )
        losses_result = await db.execute(
            select(func.count(Game.id)).where(Game.winner == "human")
        )
        draws_result = await db.execute(
            select(func.count(Game.id)).where(Game.winner == "draw")
        )
        total_result = await db.execute(select(func.count(Game.id)))

        await crud.save_model_metrics(
            db=db,
            ai_version=1,
            total_games=total_result.scalar() or 0,
            wins=wins_result.scalar() or 0,
            losses=losses_result.scalar() or 0,
            draws=draws_result.scalar() or 0,
            avg_reward=avg_reward,
            avg_game_length=float(len(moves))
        )
        print("📊 Metrics saved to DB!")
    except Exception as e:
        print(f"⚠️ Metrics save error: {e}")