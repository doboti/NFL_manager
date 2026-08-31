import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.core.bots import resolve_bot_trade_offers
from app.core.clock import now_utc
from app.core.daily_cycle import run_daily_cycle
from app.core.database import SessionLocal
from app.core.game_data import LEAGUE_TIMEZONE, MATCH_HOUR

logger = logging.getLogger("app.scheduler")

scheduler = BackgroundScheduler(timezone=LEAGUE_TIMEZONE)

# Bots reply to a trade offer within a random 0-4h window (trades.py:
# BOT_RESPONSE_WINDOW_HOURS) -- checked this often so that actually shows up
# as "within a few hours", not just once a day alongside match resolution.
BOT_TRADE_CHECK_MINUTES = 15


def _run_daily_cycle_job() -> None:
    db = SessionLocal()
    try:
        run_daily_cycle(db)
    except Exception:
        # A silently-dying scheduled job (APScheduler logs to its own
        # logger, which may not surface in `docker compose logs` depending
        # on logging config) looks identical to "the scheduler never ran
        # at all" from the outside -- print explicitly so it's visible in
        # plain container logs no matter what.
        logger.exception("daily_cycle job failed")
    finally:
        db.close()


def _resolve_bot_trade_offers_job() -> None:
    db = SessionLocal()
    try:
        resolve_bot_trade_offers(db, now_utc(db))
    except Exception:
        logger.exception("resolve_bot_trade_offers job failed")
    finally:
        db.close()


def start_scheduler() -> None:
    if not scheduler.running:
        scheduler.add_job(
            _run_daily_cycle_job,
            CronTrigger(hour=MATCH_HOUR, minute=0, timezone=LEAGUE_TIMEZONE),
            id="daily_cycle",
            replace_existing=True,
        )
        scheduler.add_job(
            _resolve_bot_trade_offers_job,
            IntervalTrigger(minutes=BOT_TRADE_CHECK_MINUTES),
            id="resolve_bot_trade_offers",
            replace_existing=True,
        )
        scheduler.start()
