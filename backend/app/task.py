import asyncio
from uuid import UUID
from app.worker import celery_app
from app.db import AsyncSessionLocal, engine
from app.models.review import Review
from sqlalchemy import select
import logging

logger = logging.getLogger(__name__)

@celery_app.task(name="run_review_task")
def run_review_task(review_id, pr_url, include_benchmark):
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_async_run_review(review_id, pr_url, include_benchmark))
    finally:
        try:
            loop.run_until_complete(engine.dispose())
        finally:
            loop.close()
            asyncio.set_event_loop(None)


async def _async_run_review(review_id: str, pr_url: str, include_benchmark: bool):
    async with AsyncSessionLocal() as db:
        service = None
        try:
            review_uuid = UUID(review_id)
            result = await db.execute(select(Review).where(Review.id == review_uuid))
            review = result.scalar_one_or_none()

            if not review:
                logger.error(f"Review {review_id} not found in DB")
                return

            review.status = "processing"
            await db.commit()

            from app.services.review import ReviewService
            service = ReviewService(db)
            await service.run_analysis_only(review_uuid, pr_url, include_benchmark)

        except Exception:
            logger.exception("Task failed for review %s", review_id)
            
            try:
                await db.rollback()
                result = await db.execute(select(Review).where(Review.id == UUID(review_id)))
                review = result.scalar_one_or_none()
                if review:
                    review.status = "failed"
                    await db.commit()
            except Exception:
                logger.exception("Could not mark review %s as failed", review_id)
        finally:
            if service is not None:
                await service.shutdown()