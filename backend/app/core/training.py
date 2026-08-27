from datetime import timedelta

from sqlalchemy.orm import Session

from app.core.clock import now_utc
from app.core.config import settings
from app.core.game_data import sessions_required_for_next_point
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


def cancel_training(db: Session, team_id: int, session_id: int) -> None:
    """Stops a training session before it's collected -- no partial credit,
    the banked xp for this session is simply discarded, but it immediately
    frees the slot so the manager can start training someone else instead."""
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

    db.delete(session)
    db.commit()


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
    potential = player.potential if player.potential is not None else 99
    xp_gain = 0

    # A session banks progress toward the next point; how many sessions
    # that takes grows sharply as overall climbs (see
    # game_data.sessions_required_for_next_point) -- fast early growth, a
    # real grind approaching 90+, and nothing at all once potential is hit
    # (#20 -- the flat "always +1" fix from #15 was too generous long-term).
    if player.overall < potential:
        required = sessions_required_for_next_point(player.overall)
        player.xp += 1
        xp_gain = 1
        if player.xp >= required:
            player.xp = 0
            player.overall = min(potential, player.overall + 1)

    session.xp_awarded = xp_gain
    session.completed = True
    session.collected = True

    db.commit()
    db.refresh(session)
    return session
