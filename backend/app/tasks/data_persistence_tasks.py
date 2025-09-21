"""
Celery tasks for data persistence operations

Handles automated backup scheduling, data validation, and maintenance tasks.
"""

from celery import Celery
from datetime import datetime, timedelta
import logging
from typing import Dict, Any

from app.core.data_persistence import data_persistence_service
from app.core.database import SessionLocal
from app.models.user import User

logger = logging.getLogger(__name__)

# Get Celery app instance (assuming it's configured in core/celery.py)
try:
    from app.core.celery import celery_app
except ImportError:
    # Fallback if celery isn't configured yet
    celery_app = Celery('galactic_empire')


@celery_app.task(bind=True, name='data_persistence.create_automated_backup')
def create_automated_backup(self, backup_type: str = "daily", include_data: bool = True) -> Dict[str, Any]:
    """
    Create an automated backup based on schedule
    
    Args:
        backup_type: Type of backup (daily, weekly, monthly)
        include_data: Whether to include data or just schema
        
    Returns:
        Dict with backup information
    """
    try:
        # Generate backup name with timestamp and type
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"auto_{backup_type}_{timestamp}"
        
        # Create backup
        backup_info = data_persistence_service.create_backup(
            backup_name=backup_name,
            include_data=include_data
        )
        
        logger.info(f"Automated {backup_type} backup created: {backup_name}")
        
        return {
            "task_id": self.request.id,
            "backup_type": backup_type,
            "backup_info": backup_info,
            "status": "completed"
        }
        
    except Exception as e:
        logger.error(f"Automated backup failed: {e}")
        raise self.retry(exc=e, countdown=300, max_retries=3)  # Retry after 5 minutes


@celery_app.task(bind=True, name='data_persistence.validate_data_integrity')
def validate_data_integrity_task(self) -> Dict[str, Any]:
    """
    Run automated data integrity validation
    
    Returns:
        Dict with validation results
    """
    try:
        validation_results = data_persistence_service.validate_data_integrity()
        
        # Log critical issues
        if validation_results["summary"]["total_errors"] > 0:
            logger.warning(f"Data integrity validation found {validation_results['summary']['total_errors']} errors")
            for error in validation_results["errors"]:
                logger.error(f"Data integrity error: {error}")
        
        logger.info(f"Data integrity validation completed: {validation_results['summary']['overall_status']}")
        
        return {
            "task_id": self.request.id,
            "validation_results": validation_results,
            "status": "completed"
        }
        
    except Exception as e:
        logger.error(f"Data integrity validation failed: {e}")
        raise self.retry(exc=e, countdown=300, max_retries=2)


@celery_app.task(bind=True, name='data_persistence.cleanup_old_backups')
def cleanup_old_backups_task(self, days_to_keep: int = 30) -> Dict[str, Any]:
    """
    Clean up old backup files
    
    Args:
        days_to_keep: Number of days to keep backups
        
    Returns:
        Dict with cleanup information
    """
    try:
        cleanup_info = data_persistence_service.cleanup_old_backups(days_to_keep)
        
        if cleanup_info["files_deleted"] > 0:
            logger.info(f"Backup cleanup completed: {cleanup_info['files_deleted']} files deleted, {cleanup_info['size_freed_mb']} MB freed")
        else:
            logger.info("Backup cleanup completed: no old files to delete")
        
        return {
            "task_id": self.request.id,
            "cleanup_info": cleanup_info,
            "status": "completed"
        }
        
    except Exception as e:
        logger.error(f"Backup cleanup failed: {e}")
        raise self.retry(exc=e, countdown=300, max_retries=2)


@celery_app.task(bind=True, name='data_persistence.export_game_state')
def export_game_state_task(self, export_type: str = "weekly", include_all: bool = True) -> Dict[str, Any]:
    """
    Create automated game state export
    
    Args:
        export_type: Type of export (daily, weekly, monthly)
        include_all: Whether to include all data types
        
    Returns:
        Dict with export information
    """
    try:
        # Generate export name with timestamp and type
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_name = f"auto_export_{export_type}_{timestamp}"
        
        # Create export
        export_info = data_persistence_service.export_game_state(
            export_name=export_name,
            include_users=include_all,
            include_ships=include_all,
            include_planets=include_all,
            include_teams=include_all,
            include_communications=include_all
        )
        
        logger.info(f"Automated {export_type} export created: {export_name}")
        
        return {
            "task_id": self.request.id,
            "export_type": export_type,
            "export_info": export_info,
            "status": "completed"
        }
        
    except Exception as e:
        logger.error(f"Automated export failed: {e}")
        raise self.retry(exc=e, countdown=300, max_retries=3)


@celery_app.task(bind=True, name='data_persistence.monitor_system_health')
def monitor_system_health_task(self) -> Dict[str, Any]:
    """
    Monitor system health and database performance
    
    Returns:
        Dict with system health information
    """
    try:
        db = SessionLocal()
        try:
            # Basic health checks
            health_info = {
                "checked_at": datetime.now().isoformat(),
                "checks": [],
                "status": "healthy"
            }
            
            # Check database connection
            try:
                db.execute("SELECT 1")
                health_info["checks"].append({
                    "check": "database_connection",
                    "status": "passed",
                    "message": "Database connection successful"
                })
            except Exception as e:
                health_info["checks"].append({
                    "check": "database_connection",
                    "status": "failed",
                    "message": f"Database connection failed: {str(e)}"
                })
                health_info["status"] = "unhealthy"
            
            # Check user count
            try:
                user_count = db.query(User).count()
                health_info["checks"].append({
                    "check": "user_count",
                    "status": "passed",
                    "message": f"Found {user_count} users",
                    "value": user_count
                })
            except Exception as e:
                health_info["checks"].append({
                    "check": "user_count",
                    "status": "failed",
                    "message": f"Failed to count users: {str(e)}"
                })
                health_info["status"] = "unhealthy"
            
            # Check for recent activity (users logged in within last 24 hours)
            try:
                from datetime import timedelta
                recent_threshold = datetime.utcnow() - timedelta(hours=24)
                recent_users = db.query(User).filter(User.last_login > recent_threshold).count()
                health_info["checks"].append({
                    "check": "recent_activity",
                    "status": "passed",
                    "message": f"Found {recent_users} recently active users",
                    "value": recent_users
                })
            except Exception as e:
                health_info["checks"].append({
                    "check": "recent_activity",
                    "status": "failed",
                    "message": f"Failed to check recent activity: {str(e)}"
                })
                health_info["status"] = "unhealthy"
            
            # Log health status
            if health_info["status"] == "healthy":
                logger.info("System health check passed")
            else:
                logger.warning("System health check found issues")
            
            return {
                "task_id": self.request.id,
                "health_info": health_info,
                "status": "completed"
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"System health monitoring failed: {e}")
        raise self.retry(exc=e, countdown=300, max_retries=2)


@celery_app.task(bind=True, name='data_persistence.schedule_backup_cleanup')
def schedule_backup_cleanup(self) -> Dict[str, Any]:
    """
    Schedule backup cleanup task
    
    Returns:
        Dict with scheduling information
    """
    try:
        # Schedule cleanup for backups older than 30 days
        cleanup_task = cleanup_old_backups_task.delay(days_to_keep=30)
        
        logger.info(f"Backup cleanup task scheduled: {cleanup_task.id}")
        
        return {
            "task_id": self.request.id,
            "cleanup_task_id": cleanup_task.id,
            "status": "scheduled"
        }
        
    except Exception as e:
        logger.error(f"Failed to schedule backup cleanup: {e}")
        raise


# Schedule periodic tasks (these would be configured in celery beat)
def schedule_periodic_tasks():
    """
    Configure periodic tasks for data persistence operations
    This would typically be called during application startup
    """
    from celery.schedules import crontab
    
    # Daily backup at 2 AM
    celery_app.conf.beat_schedule['daily-backup'] = {
        'task': 'data_persistence.create_automated_backup',
        'schedule': crontab(hour=2, minute=0),
        'args': ('daily', True)
    }
    
    # Weekly backup on Sunday at 3 AM
    celery_app.conf.beat_schedule['weekly-backup'] = {
        'task': 'data_persistence.create_automated_backup',
        'schedule': crontab(hour=3, minute=0, day_of_week=0),
        'args': ('weekly', True)
    }
    
    # Monthly backup on the 1st at 4 AM
    celery_app.conf.beat_schedule['monthly-backup'] = {
        'task': 'data_persistence.create_automated_backup',
        'schedule': crontab(hour=4, minute=0, day_of_month=1),
        'args': ('monthly', True)
    }
    
    # Data integrity validation every 6 hours
    celery_app.conf.beat_schedule['data-validation'] = {
        'task': 'data_persistence.validate_data_integrity',
        'schedule': crontab(minute=0, hour='*/6'),
    }
    
    # System health monitoring every hour
    celery_app.conf.beat_schedule['system-health'] = {
        'task': 'data_persistence.monitor_system_health',
        'schedule': crontab(minute=0),
    }
    
    # Weekly export on Monday at 1 AM
    celery_app.conf.beat_schedule['weekly-export'] = {
        'task': 'data_persistence.export_game_state',
        'schedule': crontab(hour=1, minute=0, day_of_week=1),
        'args': ('weekly', True)
    }
    
    # Backup cleanup every Sunday at 5 AM
    celery_app.conf.beat_schedule['backup-cleanup'] = {
        'task': 'data_persistence.cleanup_old_backups',
        'schedule': crontab(hour=5, minute=0, day_of_week=0),
        'args': (30,)
    }
    
    logger.info("Periodic data persistence tasks scheduled")
