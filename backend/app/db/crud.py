from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from .models import Game,Move,ActiveSession,ModelMetric
from datetime import datetime


#Game Operations

async def create_game(db:AsyncSession,session_id:str,player_name:str="Anonymous"):
    game = Game(session_id=session_id)
    db.add(game)
    await db.commit()
    await db.refresh(game)

    #Also create an active session for the player
    active=ActiveSession(
        session_id=session_id,
        player_name=player_name
    )
    db.add(active)
    await db.commit()
    return game
async def end_game(db: AsyncSession,game_id:int,winner:str,total_moves:int,duration:int):
    result="White" if winner =="human" else "black"
    await db.execute(
        update(Game)
        .where(Game.id=game_id)
        .values(
            winner=winner,
            result=result,
            total_moves=total_moves,
            duration_secs=duration
        )
    )
    await db.commit()


#Move Operations
async def save_more(db:AsyncSession,game_id:int,player:str,move_uci:str,fen_before:str,fen_after:str,move_number:int,reward:float=0.0):
    move=Move(
        game_id=game_id,
        player=player,
        move_uci=move_uci,
        fen_before=fen_before,
        fen_after=fen_after,
        move_number=move_number,
        reward=reward
    )
    db.add(move)
    await db.commit()
    await db.refresh(move)
    return move

#Dashboard Operations

async def get_active_sessions(db:AsyncSession):
    result=await db.execute(
        select(ActiveSession).where(ActiveSession.is_active==True)
    )
    return result.scalars().all()
async def get_latest_metrics(db: AsyncSession):
    result=await db.execute(
        select(ModelMetric).order_by(ModelMetric.id.desc()).limit(10)
    )
    return result.scalars().all()
async def save_model_metrics(db: AsyncSession, ai_version: int, total_games: int,
                              wins: int, losses: int, draws: int,
                              avg_reward: float, avg_game_length: float):
    win_rate = wins / total_games if total_games > 0 else 0.0
    metric = ModelMetric(
        ai_version=ai_version,
        total_games=total_games,
        wins=wins,
        losses=losses,
        draws=draws,
        win_rate=win_rate,
        avg_reward=avg_reward,
        avg_game_length=avg_game_length
    )
    db.add(metric)
    await db.commit()
    return metric