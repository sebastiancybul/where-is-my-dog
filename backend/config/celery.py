import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("config")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "check-expired-listings-every-2-hours": {
        "task": "listings.tasks.check_and_expire_listings",
        "schedule": crontab(minute=0, hour="*/2"),
    },
    "notify-expiring-listings-hourly": {
        "task": "listings.tasks.notify_expiring_listings",
        "schedule": crontab(minute=30),
    },
}
app.conf.timezone = "Europe/Warsaw"


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for testing Celery"""
    print(f"Request: {self.request!r}")
