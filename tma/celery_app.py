from celery import Celery
from celery.schedules import crontab

def make_celery(app=None):
    """
    Celery application factory.
    Configures Celery with Flask app settings and wraps task execution in app.app_context().
    """
    if app is None:
        from app import create_app
        app = create_app()

    celery = Celery(
        app.import_name,
        backend=app.config.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/2'),
        broker=app.config.get('CELERY_BROKER_URL', 'redis://localhost:6379/1')
    )

    celery.conf.update(
        timezone='UTC',
        enable_utc=True,
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        task_track_started=True,
        beat_schedule={
            # Scheduled Task 1: Daily Trek Reminder (Every day at 08:00 UTC)
            'daily-trek-reminders': {
                'task': 'tasks.send_daily_reminders',
                'schedule': crontab(hour=8, minute=0),
            },
            # Scheduled Task 2: Monthly Admin Activity Report (1st day of every month at 00:00 UTC)
            'monthly-admin-report': {
                'task': 'tasks.generate_monthly_admin_report',
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

# Global celery instance for CLI usage: celery -A celery_app.celery worker --loglevel=info
from app import create_app
flask_app = create_app()
celery = make_celery(flask_app)
