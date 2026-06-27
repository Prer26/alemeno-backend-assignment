from celery import Celery

celery = Celery(
    "alemeno",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/0"
)

celery.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"]
)