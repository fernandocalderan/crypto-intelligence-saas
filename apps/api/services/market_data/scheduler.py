import logging

from apscheduler.schedulers.background import BackgroundScheduler

from config import get_settings
from services.market_data import ingest_market_snapshots

logger = logging.getLogger(__name__)
_scheduler: BackgroundScheduler | None = None


def run_market_data_job() -> None:
    try:
        snapshots = ingest_market_snapshots()
        logger.info("Market data job completed with %s snapshots", len(snapshots))
    except Exception as exc:
        logger.warning("Market data job failed: %s", exc)


def start_market_data_scheduler() -> None:
    global _scheduler

    if _scheduler is not None and _scheduler.running:
        return

    settings = get_settings()
    _scheduler = BackgroundScheduler(timezone="UTC", daemon=True)
    _scheduler.add_job(
        run_market_data_job,
        "interval",
        minutes=settings.market_data_schedule_minutes,
        id="market-data-ingestion",
        replace_existing=True,
        max_instances=1,
    )
    _scheduler.start()
    logger.info(
        "Market data scheduler started with %s minute interval",
        settings.market_data_schedule_minutes,
    )


def stop_market_data_scheduler() -> None:
    global _scheduler

    if _scheduler is None:
        return

    if _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Market data scheduler stopped")

    _scheduler = None
