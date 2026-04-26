import asyncio
from app.worker import celery_app
from app.db import AsyncSessionLocal
from app.models.review import Review
from sqlalchemy import select
import logging

logger = logging.getLogger(__name__)

@celery_app.task(name="run_review_task")
def run_review_task(review_id: str, pr_url: str, include_benchmark: bool):
    asyncio.run(_async_run_review(review_id, pr_url, include_benchmark))


async def _async_run_review(review_id: str, pr_url: str, include_benchmark: bool):
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(select(Review).where(Review.id == review_id))
            review = result.scalar_one_or_none()

            if not review:
                logger.error(f"Review {review_id} not found in DB")
                return

            review.status = "processing"
            await db.commit()

            from app.services.review import ReviewService
            service = ReviewService(db)
            await service.run_analysis_only(review_id, pr_url, include_benchmark)

        except Exception as e:
            logger.error(f"Task failed for review {review_id}: {type(e).__name__}: {e}")
            
            try:
                result = await db.execute(select(Review).where(Review.id == review_id))
                review = result.scalar_one_or_none()
                if review:
                    review.status = "failed"
                    await db.commit()
            except Exception as inner_e:
                logger.error(f"Could not mark review as failed: {inner_e}")
        finally:
            await db.close()

# Register as Celery task
run_review_task = celery_app.task(name="run_review_task")(run_review_task)