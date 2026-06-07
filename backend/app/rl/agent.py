import chess
import random
import torch
import torch.nn as nn
import numpy as np
import os

MODEL_PATH="model_weights/chess_r1.pt"

#Neural Network
class ChessNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.network=nn.Sequential(
            nn.Linear(768,512),
            nn.ReLU(),
            nn.Dropout(0,3),
            nn.Linear(512,256),
            nn.ReLU(),
            nn.Dropout(0,3),
            nn.Linear(256,128),
            nn.ReLU(),
            nn.Linear(128,1),
            nn.Tanh() #Output Between -1 and 1

        )
    def forward(self,x):
        return self.network(x)

#Board to Tensor
def board_to_tensor(board:chess.Board)->torch.Tensor:
    tensor =np.zeros(768,dtype=np.float32)
    piece_map = {
        chess.PAWN: 0, chess.KNIGHT: 1, chess.BISHOP: 2,
        chess.ROOK: 3, chess.QUEEN: 4, chess.KING: 5
    }
    for square,piece in board.piece_map().items():
        idx = piece_map[piece.piece_type]
        if piece.color == chess.WHITE:
            tensor[square*12+idx]=1.0
        else:
            tensor[square*12+idx+6]=1.0
    return torch.FloatTensor(tensor)
#Load or create model
def load_model():
    model=ChessNet()
    if os.path.exists(MODEL_PATH):
        model.load_state_dict(torch.load(MODEL_PATH, map_location="cpu"))
        print("✅ Loaded existing model weights!")
    else:
        print("🆕 No model found — starting fresh (random play)")
    model.eval()
    return model

# Global model instance
_model = None

def get_model():
    global _model
    if _model is None:
        _model = load_model()
    return _model

# ── AI Move Selection ──────────────────────────────────
def get_ai_move(board: chess.Board, epsilon: float = 0.3) -> chess.Move:
    """
    Epsilon-greedy move selection:
    - epsilon % of the time: pick a RANDOM move (exploration)
    - (1-epsilon) % of the time: pick the BEST move (exploitation)
    
    As the model trains more, epsilon decreases → less random, smarter!
    """
    legal_moves = list(board.legal_moves)

    if not legal_moves:
        return None

    # Exploration — random move
    if random.random() < epsilon:
        return random.choice(legal_moves)

    # Exploitation — use neural network
    model = get_model()
    best_move = None
    best_score = float("-inf")

    # Evaluate each legal move
    for move in legal_moves:
        board.push(move)
        tensor = board_to_tensor(board)
        with torch.no_grad():
            score = model(tensor.unsqueeze(0)).item()
        board.pop()

        # AI plays as black, so negate score
        if not board.turn:
            score = -score

        if score > best_score:
            best_score = score
            best_move = move

    return best_move if best_move else random.choice(legal_moves)