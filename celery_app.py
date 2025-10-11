import os
import logging
from dotenv import load_dotenv
from celery import Celery

# ---------------- Load environment ----------------
load_dotenv()

# ---------------- Setup logging ----------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------- Celery Config ----------------
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")


def create_celery_app() -> Celery:
    """Create and configure the Celery app."""
    logger.info(f"Initializing Celery with broker: {CELERY_BROKER_URL}")

    celery = Celery(
        "blog_app_worker",
        broker=CELERY_BROKER_URL,
        backend=CELERY_RESULT_BACKEND,
        include=["celery_tasks"],
    )

    celery.conf.update(
        # Core settings
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        broker_connection_retry_on_startup=True,

        task_acks_late=True,
        worker_prefetch_multiplier=1,

        task_routes={
            "celery_tasks.send_verification_email": {"queue": "emails"},
            "celery_tasks.send_password_reset_email": {"queue": "emails"},
        },

        task_default_queue="emails",
    )

    logger.info("Celery initialized successfully.")
    return celery


celery_app = create_celery_app()

if __name__ == "__main__":
    logger.info("Starting Celery worker...")
    celery_app.start()

