import logging

from apscheduler.schedulers.background import BackgroundScheduler

from config import get_settings
from db.session import SessionLocal
from services.alert_engine import process_alert_pipeline
from services.market_data import ingest_market_snapshots
from services.signal_engine import compute_signal_payloads
from services.signal_persistence import persist_signals

logger = logging.getLogger(__name__)
_scheduler: BackgroundScheduler | None = None


def run_market_data_job() -> None:
    try:
        snapshots = ingest_market_snapshots()
        logger.info("Market data job completed with %s snapshots", len(snapshots))
        if not snapshots:
            return

        detected_signals = compute_signal_payloads(market_snapshots=snapshots)
        if not detected_signals:
            logger.info("Signal pipeline completed with no active signals")
            return

        snapshot_index = {str(snapshot["symbol"]).upper(): snapshot for snapshot in snapshots}
        with SessionLocal() as session:
            new_signals = persist_signals(
                session,
                detected_signals,
                snapshot_index=snapshot_index,
            )
            if not new_signals:
                logger.info("No new signals persisted for this scheduler run")
                return

            logger.info("Signal pipeline persisted %s new signals", len(new_signals))
            settings = get_settings()
            if settings.alerts_process_on_scheduler:
                alert_result = process_alert_pipeline(
                    session,
                    new_signals,
                    market_snapshots=snapshots,
                )
                logger.info(
                    "Alert pipeline result sent=%s failed=%s skipped=%s",
                    alert_result["sent"],
                    alert_result["failed"],
                    alert_result["skipped"],
                )
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
