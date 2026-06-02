from pydantic import BaseModel
from datetime import datetime
from typing import Optional

## Game Schemas

class GameCreate(BaseModel):
    session_id : str
    player_name : Optional[str] = "Anonymous"
class GameResponse(BaseModel):
    id : int
    session_id : str
    result : Optional[str]=None
    winner : Optional[str]=None
    total_moves:int
    ai_version : int
    created_at : datetime
    class Config:
        from_attributes=True
##Move Schemas 

class MoveCreate(BaseModel):
    game_id : int
    move_uci : str  #e2e4, g8f6
    player : str  #Human or AI
class MoveResponse(BaseModel):
    id : int
    game_id:int
    move_number:int
    player:str
    move_uci:str
    fen_after:str
    reward:float

    class Config:
        from_attributes=True
##Dash Board Schemas

class ActiveSessionResponse(BaseModel):
    session_id:str
    player_name:str
    current_move:int
    started_at:datetime

    class Config:
        from_attributes=True
class ModelMetricResponse(BaseModel):
    ai_version : int
    total_games:int
    win_rate:float
    avg_reward:float
    avg_game_length:float
    recorded_at:datetime

    class Config:
        from_attributes=True