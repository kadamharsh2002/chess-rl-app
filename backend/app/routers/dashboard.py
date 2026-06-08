from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from ..db.database import get_db
from ..db.models import Game, Move, ModelMetric, ActiveSession

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    # Total games
    total_games = await db.execute(select(func.count(Game.id)))
    total = total_games.scalar() or 0

    # Wins losses draws
    wins = await db.execute(
        select(func.count(Game.id)).where(Game.winner == "ai")
    )
    losses = await db.execute(
        select(func.count(Game.id)).where(Game.winner == "human")
    )
    draws = await db.execute(
        select(func.count(Game.id)).where(Game.winner == "draw")
    )

    ai_wins = wins.scalar() or 0
    ai_losses = losses.scalar() or 0
    ai_draws = draws.scalar() or 0

    win_rate = round((ai_wins / total * 100), 1) if total > 0 else 0

    # Average game length
    avg_moves = await db.execute(
        select(func.avg(Game.total_moves)).where(Game.total_moves > 0)
    )
    avg_length = round(avg_moves.scalar() or 0, 1)

    # Latest model metrics
    latest_metric = await db.execute(
        select(ModelMetric).order_by(ModelMetric.id.desc()).limit(1)
    )
    metric = latest_metric.scalar_one_or_none()

    # Recent games
    recent = await db.execute(
        select(Game).order_by(Game.id.desc()).limit(10)
    )
    recent_games = recent.scalars().all()

    # Active sessions
    active = await db.execute(
        select(ActiveSession).where(ActiveSession.is_active == True)
    )
    active_sessions = active.scalars().all()

    # Win rate history for graph
    all_games = await db.execute(
        select(Game).where(Game.winner != None).order_by(Game.id.asc())
    )
    games_list = all_games.scalars().all()

    win_rate_history = []
    for i, g in enumerate(games_list):
        wins_so_far = sum(1 for x in games_list[:i+1] if x.winner == "ai")
        rate = round(wins_so_far / (i+1) * 100, 1)
        win_rate_history.append({
            "game": i+1,
            "win_rate": rate,
            "winner": g.winner
        })

    return {
        "total_games": total,
        "ai_wins": ai_wins,
        "ai_losses": ai_losses,
        "ai_draws": ai_draws,
        "win_rate": win_rate,
        "avg_game_length": avg_length,
        "ai_version": metric.ai_version if metric else 1,
        "avg_reward": round(metric.avg_reward if metric else 0, 3),
        "active_players": len(active_sessions),
        "active_sessions": [
            {
                "player_name": s.player_name,
                "current_move": s.current_move,
                "started_at": s.started_at.isoformat()
            } for s in active_sessions
        ],
        "recent_games": [
            {
                "id": g.id,
                "winner": g.winner,
                "total_moves": g.total_moves,
                "duration_secs": g.duration_secs
            } for g in recent_games
        ],
        "win_rate_history": win_rate_history
    }

@router.get("/training")
async def get_training_stats():
    """Returns the training stats file directly"""
    from ..rl.agent import get_stats, get_epsilon
    stats = get_stats()
    return {
        "total_games": stats.get("total_games", 0),
        "wins": stats.get("wins", 0),
        "losses": stats.get("losses", 0),
        "draws": stats.get("draws", 0),
        "epsilon": round(get_epsilon(), 3),
        "exploration_pct": round(get_epsilon() * 100, 1),
        "loss_history": stats.get("loss_history", []),
        "reward_history": stats.get("reward_history", []),
        "win_rate_history": stats.get("win_rate_history", []),
        "is_learning": (
            stats["loss_history"][-1] < stats["loss_history"][0]
            if len(stats.get("loss_history", [])) > 1
            else False
        )
    }