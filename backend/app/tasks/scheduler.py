"""Scheduled tasks for report generation and alert evaluation."""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta
import logging

from app.db.session import SessionLocal
from app.services.alert_service import AlertService
from app.services.report_service import ReportService
from app.services.metric_service import MetricService
from app.core.config import settings

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def evaluate_alerts():
    """Scheduled task to evaluate alert rules."""
    logger.info("Running alert evaluation...")
    db = SessionLocal()
    try:
        # Evaluate metric-based alerts
        new_alerts = AlertService.evaluate_rules(db)
        logger.info(f"Created {len(new_alerts)} new alerts")
        
        # Check for heartbeat/offline alerts
        heartbeat_alerts = AlertService.check_heartbeat_alerts(db)
        logger.info(f"Created {len(heartbeat_alerts)} heartbeat alerts")
    
    except Exception as e:
        logger.error(f"Error evaluating alerts: {e}")
    finally:
        db.close()


def generate_periodic_report():
    """Scheduled task to generate periodic reports."""
    logger.info("Generating periodic report...")
    db = SessionLocal()
    try:
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=settings.REPORT_INTERVAL_MINUTES)
        
        report = ReportService.generate_report(
            db,
            start_time,
            end_time,
            report_type="periodic"
        )
        
        logger.info(f"Generated periodic report: {report.id}")
    
    except Exception as e:
        logger.error(f"Error generating report: {e}")
    finally:
        db.close()


def cleanup_old_metrics():
    """Scheduled task to cleanup old metrics."""
    logger.info("Cleaning up old metrics...")
    db = SessionLocal()
    try:
        deleted = MetricService.cleanup_old_metrics(db, settings.METRICS_RETENTION_DAYS)
        logger.info(f"Cleaned up {deleted} old metrics")
    except Exception as e:
        logger.error(f"Error cleaning up metrics: {e}")
    finally:
        db.close()


def start_scheduler():
    """Start the scheduler."""
    # Alert evaluation every minute
    scheduler.add_job(
        evaluate_alerts,
        trigger=IntervalTrigger(seconds=settings.ALERT_CHECK_INTERVAL_SECONDS),
        id='alert_evaluation',
        name='Evaluate alert rules',
        replace_existing=True
    )
    
    # Report generation every 5 minutes
    scheduler.add_job(
        generate_periodic_report,
        trigger=IntervalTrigger(minutes=settings.REPORT_INTERVAL_MINUTES),
        id='report_generation',
        name='Generate periodic report',
        replace_existing=True
    )
    
    # Cleanup old metrics daily at 2 AM
    scheduler.add_job(
        cleanup_old_metrics,
        trigger='cron',
        hour=2,
        minute=0,
        id='metric_cleanup',
        name='Cleanup old metrics',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("Scheduler started")


def stop_scheduler():
    """Stop the scheduler."""
    scheduler.shutdown()
    logger.info("Scheduler stopped")
