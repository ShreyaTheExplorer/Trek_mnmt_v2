import os
import sys

# Ensure tma directory is on sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from celery import Celery
from celery.schedules import crontab

def make_celery(app=None):
    """
    Celery factory integrating with Flask application context.
    Configures Beat schedules for daily reminders and monthly report.
    """
    if app is None:
        from app import create_app
        app = create_app()

    celery = Celery(
        app.import_name,
        backend=app.config.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/2'),
        broker=app.config.get('CELERY_BROKER_URL', 'redis://localhost:6379/1'),
        include=['tasks']
    )

    # Celery Beat schedule configuration
    # Default daily reminder time: 08:00 UTC (configurable via env)
    reminder_hour = int(os.environ.get('REMINDER_CRON_HOUR', 8))
    reminder_minute = int(os.environ.get('REMINDER_CRON_MINUTE', 0))

    celery.conf.update(
        timezone='UTC',
        enable_utc=True,
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        task_track_started=True,
        beat_schedule={
            # Scheduled job 1: daily_reminders (default 08:00 daily)
            'daily-trek-reminders': {
                'task': 'tasks.daily_reminders',
                'schedule': crontab(hour=reminder_hour, minute=reminder_minute),
            },
            # Scheduled job 2: monthly_report (1st of every month at 00:00 UTC)
            'monthly-admin-report': {
                'task': 'tasks.monthly_report',
                'schedule': crontab(day_of_month=1, hour=0, minute=0),
            }
        }
    )

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery

# Global Celery application instance
from app import create_app
flask_app = create_app()
celery = make_celery(flask_app)
