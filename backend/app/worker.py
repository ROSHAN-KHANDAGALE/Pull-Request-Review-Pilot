from app.config import settings
from celery import Celery

redis_url = settings.redis_url

celery_app = Celery("reviewpilot", include=['app.task'])

celery_app.conf.update(
    broker_url=redis_url,
    result_backend=redis_url,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    worker_pool="solo", 
)