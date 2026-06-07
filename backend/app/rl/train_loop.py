import torch
import torch.nn as nn
import torch.optim as optim
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..db.models import Move, Game
from .agent import ChessNet, board_to_tensor, MODEL_PATH, get_model
import chess
import os
from sqlalchemy import select, func
from ..db.models import Move, Game
from ..db import crud

# ── Piece Values ───────────────────────────────────────
# Standard chess piece values used by all major engines
PIECE_VALUES = {
    chess.PAWN:   1.0,
    chess.KNIGHT: 3.0,
    chess.BISHOP: 3.0,
    chess.ROOK:   5.0,
    chess.QUEEN:  9.0,
    chess.KING:   0.0   # King capture = game over, handled separately
}

def calculate_move_reward(board: chess.Board, move: chess.Move, player: str) -> float:
    """
    Calculate instant reward for a single move BEFORE it is played.
    
    AI captures enemy piece  → POSITIVE reward (piece value)
    Enemy captures AI piece  → NEGATIVE reward (piece value)
    Check                    → small bonus
    Normal move              → 0
    """
    reward = 0.0

    # ── Capture reward ─────────────────────────────────
    if board.is_capture(move):
        captured_piece = board.piece_at(move.to_square)
        
        # En passant — captured pawn is not on to_square
        if board.is_en_passant(move):
            captured_piece_type = chess.PAWN
        elif captured_piece:
            captured_piece_type = captured_piece.piece_type
        else:
            captured_piece_type = chess.PAWN

        piece_value = PIECE_VALUES.get(captured_piece_type, 0.0)

        if player == "ai":
            reward += piece_value      # AI captured enemy piece → GOOD
            print(f"🤖 AI captured piece worth +{piece_value}")
        else:
            reward -= piece_value      # Human captured AI piece → BAD for AI
            print(f"😤 Human captured AI piece worth -{piece_value}")

    # ── Check bonus ────────────────────────────────────
    # Make the move temporarily to check if it results in check
    board.push(move)
    if board.is_check():
        if player == "ai":
            reward += 0.5              # AI put human in check → small bonus
        else:
            reward -= 0.5              # Human put AI in check → small penalty
    board.pop()

    # ── Promotion bonus ────────────────────────────────
    if move.promotion:
        if player == "ai":
            reward += 8.0              # Pawn promoted! Big bonus (queen - pawn value)
        else:
            reward -= 8.0

    return reward


def calculate_game_end_reward(winner: str) -> float:
    """
    Massive reward/penalty at game end.
    This is the most important signal for learning!
    """
    if winner == "ai":
        return 100.0      # WIN — huge positive reward
    elif winner == "human":
        return -100.0     # LOSS — huge negative penalty
    else:
        return 10.0       # DRAW — small positive (better than losing)


async def train_after_game(db: AsyncSession, game_id: int):
    """Called after every game ends — this is where the AI learns!"""
    print(f"🧠 Training on game {game_id}...")

    # Get all moves from this game
    result = await db.execute(
        select(Move).where(Move.game_id == game_id).order_by(Move.move_number)
    )
    moves = result.scalars().all()

    if len(moves) < 5:
        print("⚠️ Too few moves to train on")
        return

    # Get game result
    game_result = await db.execute(select(Game).where(Game.id == game_id))
    game = game_result.scalar_one_or_none()
    if not game:
        return

    # Game end reward
    game_end_reward = calculate_game_end_reward(game.winner)
    print(f"🏆 Game end reward: {game_end_reward} (winner: {game.winner})")

    # Build training data using stored rewards + game end signal
    states = []
    targets = []
    board = chess.Board()
    discount = 0.99     # future rewards worth slightly less than immediate ones

    for i, move in enumerate(moves):
        try:
            chess_move = chess.Move.from_uci(move.move_uci)
            tensor = board_to_tensor(board)

            # Combine:
            # 1. Instant piece capture reward (stored in DB)
            # 2. Discounted game end reward
            steps_from_end = len(moves) - i
            discounted_end = game_end_reward * (discount ** steps_from_end)
            total_reward = move.reward + discounted_end

            states.append(tensor)
            targets.append(total_reward)

            board.push(chess_move)
        except Exception as e:
            print(f"⚠️ Skipping move {move.move_uci}: {e}")
            continue

    if not states:
        return

    # Train the neural network
    model = get_model()
    model.train()
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    criterion = nn.MSELoss()

    states_tensor = torch.stack(states)
    targets_tensor = torch.FloatTensor(targets).unsqueeze(1)

    total_loss = 0
    for epoch in range(20):      # 20 passes over this game's data
        optimizer.zero_grad()
        predictions = model(states_tensor)
        loss = criterion(predictions, targets_tensor)
        loss.backward()
        optimizer.step()
        total_loss = loss.item()

    # Save updated weights
    os.makedirs("model_weights", exist_ok=True)
    torch.save(model.state_dict(), MODEL_PATH)
    model.eval()
    print(f"✅ Training complete! Final loss: {total_loss:.4f}")

    # Save metrics to database
    try:
        total_games_result = await db.execute(
            select(func.count(Game.id))
        )
        total_games_count = total_games_result.scalar() or 0

        wins_result = await db.execute(
            select(func.count(Game.id)).where(Game.winner == "ai")
        )
        losses_result = await db.execute(
            select(func.count(Game.id)).where(Game.winner == "human")
        )
        draws_result = await db.execute(
            select(func.count(Game.id)).where(Game.winner == "draw")
        )

        await crud.save_model_metrics(
            db=db,
            ai_version=1,
            total_games=total_games_count,
            wins=wins_result.scalar() or 0,
            losses=losses_result.scalar() or 0,
            draws=draws_result.scalar() or 0,
            avg_reward=float(sum(targets) / len(targets)) if targets else 0.0,
            avg_game_length=float(len(moves))
        )
        print("📊 Metrics saved to database!")
    except Exception as e:
        print(f"⚠️ Could not save metrics: {e}")