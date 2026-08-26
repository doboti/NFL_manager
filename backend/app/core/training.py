from datetime import timedelta

from sqlalchemy.orm import Session

from app.core.clock import now_utc
from app.core.config import settings
from app.core.game_data import BASE_TRAINING_XP, age_xp_multiplier
from app.models.player import Player
from app.models.training import TrainingSession


class TrainingError(Exception):
    pass


def active_slot_count(db: Session, team_id: int) -> int:
    return (
        db.query(TrainingSession)
        .join(Player, Player.id == TrainingSession.player_id)
        .filter(Player.team_id == team_id, TrainingSession.collected.is_(False))
        .count()
    )


def training_player_ids(db: Session, team_id: int, now) -> set[int]:
    """Players currently mid-session (collected doesn't matter yet if the
    clock hasn't reached ends_at) -- these can't be picked as a starter."""
    rows = (
        db.query(TrainingSession.player_id)
        .join(Player, Player.id == TrainingSession.player_id)
        .filter(Player.team_id == team_id, TrainingSession.collected.is_(False), TrainingSession.ends_at > now)
        .all()
    )
    return {player_id for (player_id,) in rows}


def start_training(db: Session, team_id: int, player_id: int) -> TrainingSession:
    player = db.query(Player).filter(Player.id == player_id, Player.team_id == team_id).first()
    if player is None:
        raise TrainingError("Player not found on this team")

    existing = (
        db.query(TrainingSession)
        .filter(TrainingSession.player_id == player_id, TrainingSession.collected.is_(False))
        .first()
    )
    if existing is not None:
        raise TrainingError("Player is already training")

    if active_slot_count(db, team_id) >= settings.training_slots_per_day:
        raise TrainingError("No free training slots")

    now = now_utc(db)
    session = TrainingSession(
        player_id=player_id,
        started_at=now,
        ends_at=now + timedelta(hours=settings.training_duration_hours),
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def collect_training(db: Session, team_id: int, session_id: int) -> TrainingSession:
    session = (
        db.query(TrainingSession)
        .join(Player, Player.id == TrainingSession.player_id)
        .filter(TrainingSession.id == session_id, Player.team_id == team_id)
        .first()
    )
    if session is None:
        raise TrainingError("Training session not found")
    if session.collected:
        raise TrainingError("Training already collected")

    now = now_utc(db)
    if now < session.ends_at:
        raise TrainingError("Training is not finished yet")

    player = session.player
    xp_gain = round(BASE_TRAINING_XP * age_xp_multiplier(player.age))

    # xp is a cosmetic career-total stat only -- it no longer gates the
    # level-up. It used to (xp >= ovr*100, scaled down hard by age), which
    # meant a veteran or high-OVR player could need 50-90+ sessions for a
    # single point, well outside a 17-day season. A completed session now
    # always earns the point it promises.
    player.xp += xp_gain
    if player.overall < 99:
        player.overall += 1

    session.xp_awarded = xp_gain
    session.completed = True
    session.collected = True

    db.commit()
    db.refresh(session)
    return session
