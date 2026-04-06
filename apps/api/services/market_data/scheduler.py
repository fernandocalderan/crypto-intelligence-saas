import logging

from apscheduler.schedulers.background import BackgroundScheduler

from config import get_settings
from db.session import SessionLocal
from services.alert_engine import process_alert_pipeline
from services.market_data import ingest_market_snapshots
from services.setup_engine import create_setups_from_views, list_active_setups, update_setups_status
from services.setup_view import build_setup_views
from services.signal_engine import compute_signal_and_setup_payloads
from services.signal_persistence import persist_signals

logger = logging.getLogger(__name__)
_scheduler: BackgroundScheduler | None = None


def run_market_data_job() -> None:
    try:
        settings = get_settings()
        logger.info(
            "scheduler_tick_started enable_market_data_scheduler=%s alerts_process_on_scheduler=%s enable_alerts=%s",
            settings.enable_market_data_scheduler,
            settings.alerts_process_on_scheduler,
            settings.enable_alerts,
        )
        snapshots = ingest_market_snapshots()
        logger.info("snapshots_persisted_count=%s", len(snapshots))
        if not snapshots:
            return

        detected_signals, detected_setups = compute_signal_and_setup_payloads(market_snapshots=snapshots)
        if not detected_signals:
            logger.info("Signal pipeline completed with no active signals")
        logger.info("Confluence pipeline produced %s setups", len(detected_setups))

        snapshot_index = {str(snapshot["symbol"]).upper(): snapshot for snapshot in snapshots}
        with SessionLocal() as session:
            active_setups = list_active_setups(session)
            if active_setups:
                setup_update_result = update_setups_status(active_setups, snapshot_index, session)
                logger.info(
                    "Setup lifecycle result updated=%s expired=%s",
                    setup_update_result["updated"],
                    setup_update_result["expired"],
                )

            new_signals = (
                persist_signals(
                    session,
                    detected_signals,
                    snapshot_index=snapshot_index,
                )
                if detected_signals
                else []
            )
            if not new_signals:
                logger.info("No new signals persisted for this scheduler run")
            else:
                logger.info("Signal pipeline persisted %s new signals", len(new_signals))
            logger.info("new_signals_persisted_count=%s", len(new_signals))

            setup_views = build_setup_views(detected_setups, snapshots, plan="pro") if detected_setups else []
            new_setups = create_setups_from_views(setup_views, session) if setup_views else []
            if new_setups:
                logger.info("Setup pipeline persisted %s new executable setups", len(new_setups))

            if settings.alerts_process_on_scheduler and new_signals:
                alert_result = process_alert_pipeline(
                    session,
                    new_signals,
                    detected_signals=detected_signals,
                    market_snapshots=snapshots,
                )
                logger.info(
                    "alerts_candidates_count=%s",
                    alert_result.get("candidates", 0),
                )
                logger.info(
                    "alert_deliveries_created_count=%s",
                    alert_result.get("alert_deliveries_created_count", alert_result.get("deliveries_created", 0)),
                )
                logger.info(
                    "alert_deliveries_sent_count=%s",
                    alert_result["sent"],
                )
                logger.info(
                    "alert_deliveries_failed_count=%s",
                    alert_result["failed"],
                )
                logger.info("alert_deliveries_skipped_count=%s", alert_result["skipped"])
                logger.info("alert_skip_reasons=%s", alert_result.get("skip_reasons", {}))
            elif not settings.alerts_process_on_scheduler:
                logger.info("scheduler_alert_processing_skipped reason=ALERTS_PROCESS_ON_SCHEDULER_false")
            else:
                logger.info("scheduler_alert_processing_skipped reason=no_new_signals")
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
