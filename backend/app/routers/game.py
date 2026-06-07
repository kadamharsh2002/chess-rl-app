from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from ..db.database import get_db
from ..db import crud
from ..rl.train_loop import calculate_move_reward
import chess
import uuid
import time

router = APIRouter(prefix="/game", tags=["game"])

active_games = {}

@router.post("/start")
async def start_game(player_name: str = "Anonymous", db: AsyncSession = Depends(get_db)):
    session_id = str(uuid.uuid4())
    board = chess.Board()
    game = await crud.create_game(db, session_id, player_name)
    active_games[session_id] = {
        "board": board,
        "game_id": game.id,
        "move_number": 0,
        "start_time": time.time()
    }
    return {
        "session_id": session_id,
        "game_id": game.id,
        "fen": board.fen(),
        "message": "Game started! You play as White."
    }

@router.post("/move")
async def make_move(session_id: str, move_uci: str, db: AsyncSession = Depends(get_db)):
    if session_id not in active_games:
        return {"error": "Game not found"}

    game_data = active_games[session_id]
    board = game_data["board"]

    # Validate human move
    try:
        move = chess.Move.from_uci(move_uci)
        if move not in board.legal_moves:
            return {"error": "Illegal move"}
    except:
        return {"error": "Invalid move format"}

    # Calculate reward for human move BEFORE applying it
    # Human capturing AI piece = negative reward for AI
    human_reward = calculate_move_reward(board, move, "human")

    fen_before = board.fen()
    board.push(move)
    game_data["move_number"] += 1

    await crud.save_move(
        db, game_data["game_id"], "human",
        move_uci, fen_before, board.fen(),
        game_data["move_number"],
        reward=human_reward      # store the reward!
    )

    if board.is_game_over():
        return await end_game_response(session_id, board, db, game_data)

    # AI move
    from ..rl.agent import get_ai_move
    ai_move = get_ai_move(board)

    # Calculate reward for AI move BEFORE applying it
    ai_reward = calculate_move_reward(board, ai_move, "ai")

    fen_before_ai = board.fen()
    board.push(ai_move)
    game_data["move_number"] += 1

    await crud.save_move(
        db, game_data["game_id"], "ai",
        ai_move.uci(), fen_before_ai, board.fen(),
        game_data["move_number"],
        reward=ai_reward         # store the reward!
    )

    if board.is_game_over():
        return await end_game_response(session_id, board, db, game_data)

    return {
        "fen": board.fen(),
        "ai_move": ai_move.uci(),
        "move_number": game_data["move_number"],
        "is_check": board.is_check(),
        "game_over": False,
        "ai_reward": ai_reward   # send to frontend for display!
    }

async def end_game_response(session_id, board, db, game_data):
    result = board.result()
    winner = "human" if result == "1-0" else "ai" if result == "0-1" else "draw"
    duration = int(time.time() - game_data["start_time"])

    await crud.end_game(db, game_data["game_id"], winner,
                        game_data["move_number"], duration)

    from ..rl.train_loop import train_after_game
    await train_after_game(db, game_data["game_id"])

    del active_games[session_id]
    return {
        "fen": board.fen(),
        "game_over": True,
        "winner": winner,
        "result": result,
        "total_moves": game_data["move_number"]
    }

@router.get("/state/{session_id}")
async def get_game_state(session_id: str):
    if session_id not in active_games:
        return {"error": "Game not found"}
    board = active_games[session_id]["board"]
    return {
        "fen": board.fen(),
        "legal_moves": [m.uci() for m in board.legal_moves],
        "is_check": board.is_check(),
        "move_number": active_games[session_id]["move_number"]
    }