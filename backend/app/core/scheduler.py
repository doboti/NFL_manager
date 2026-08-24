from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.daily_cycle import run_daily_cycle
from app.core.database import SessionLocal
from app.core.game_data import LEAGUE_TIMEZONE, MATCH_HOUR

scheduler = BackgroundScheduler(timezone=LEAGUE_TIMEZONE)


def _run_daily_cycle_job() -> None:
    db = SessionLocal()
    try:
        run_daily_cycle(db)
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
        scheduler.start()
