from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.core.bots import resolve_bot_trade_offers
from app.core.clock import now_utc
from app.core.daily_cycle import run_daily_cycle
from app.core.database import SessionLocal
from app.core.game_data import LEAGUE_TIMEZONE, MATCH_HOUR

scheduler = BackgroundScheduler(timezone=LEAGUE_TIMEZONE)

# Bots reply to a trade offer within a random 0-4h window (trades.py:
# BOT_RESPONSE_WINDOW_HOURS) -- checked this often so that actually shows up
# as "within a few hours", not just once a day alongside match resolution.
BOT_TRADE_CHECK_MINUTES = 15


def _run_daily_cycle_job() -> None:
    db = SessionLocal()
    try:
        run_daily_cycle(db)
    finally:
        db.close()


def _resolve_bot_trade_offers_job() -> None:
    db = SessionLocal()
    try:
        resolve_bot_trade_offers(db, now_utc(db))
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
