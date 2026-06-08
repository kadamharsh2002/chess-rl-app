import chess
import random
import torch
import torch.nn as nn
import numpy as np
import os
import json

MODEL_PATH = "model_weights/chess_rl.pt"
STATS_PATH = "model_weights/training_stats.json"

# ── Neural Network ─────────────────────────────────────
class ChessNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(768, 512),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Linear(128, 1),
            nn.Tanh()
        )

    def forward(self, x):
        return self.network(x)

# ── Board to tensor ────────────────────────────────────
def board_to_tensor(board: chess.Board) -> torch.Tensor:
    tensor = np.zeros(768, dtype=np.float32)
    piece_map = {
        chess.PAWN: 0, chess.KNIGHT: 1, chess.BISHOP: 2,
        chess.ROOK: 3, chess.QUEEN: 4, chess.KING: 5
    }
    for square, piece in board.piece_map().items():
        idx = piece_map[piece.piece_type]
        if piece.color == chess.WHITE:
            tensor[square * 12 + idx] = 1.0
        else:
            tensor[square * 12 + idx + 6] = 1.0
    return torch.FloatTensor(tensor)

# ── Training Stats (tracks if AI is learning) ─────────
def load_stats():
    if os.path.exists(STATS_PATH):
        with open(STATS_PATH, 'r') as f:
            return json.load(f)
    return {
        "total_games": 0,
        "wins": 0,
        "losses": 0,
        "draws": 0,
        "epsilon": 1.0,        # starts fully random!
        "loss_history": [],
        "reward_history": [],
        "win_rate_history": []
    }

def save_stats(stats):
    os.makedirs("model_weights", exist_ok=True)
    with open(STATS_PATH, 'w') as f:
        json.dump(stats, f, indent=2)

# ── Load or create model ───────────────────────────────
def load_model():
    model = ChessNet()
    if os.path.exists(MODEL_PATH):
        model.load_state_dict(
            torch.load(MODEL_PATH, map_location="cpu")
        )
        print("✅ Loaded existing model weights!")
    else:
        print("🆕 No model found — starting fresh (random play)")
    model.eval()
    return model

# Global instances
_model = None
_stats = None

def get_model():
    global _model
    if _model is None:
        _model = load_model()
    return _model

def get_stats():
    global _stats
    if _stats is None:
        _stats = load_stats()
    return _stats

def get_epsilon():
    """
    Epsilon controls exploration vs exploitation:
    - High epsilon = more random moves (exploration)
    - Low epsilon = more model moves (exploitation)
    
    Starts at 1.0 (100% random) and decays toward 0.1
    This means early games are random, later games use the model
    """
    stats = get_stats()
    return stats.get("epsilon", 1.0)

# ── AI Move Selection ──────────────────────────────────
def get_ai_move(board: chess.Board) -> chess.Move:
    legal_moves = list(board.legal_moves)
    if not legal_moves:
        return None

    epsilon = get_epsilon()

    # Exploration — random move
    if random.random() < epsilon:
        return random.choice(legal_moves)

    # Exploitation — use neural network
    model = get_model()
    best_move = None
    best_score = float("-inf")

    # Don't evaluate ALL moves every time — too slow
    # Sample up to 20 moves for efficiency
    moves_to_check = random.sample(
        legal_moves, min(20, len(legal_moves))
    )

    for move in moves_to_check:
        board.push(move)
        tensor = board_to_tensor(board)
        with torch.no_grad():
            score = model(tensor.unsqueeze(0)).item()
        board.pop()

        if not board.turn:
            score = -score

        if score > best_score:
            best_score = score
            best_move = move

    return best_move if best_move else random.choice(legal_moves)