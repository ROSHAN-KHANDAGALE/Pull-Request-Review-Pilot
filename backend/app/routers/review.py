from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from uuid import UUID, uuid4
from app.db import get_db
from app.schemas.review import ReviewCreate, ReviewOut
from app.services.scorer import ScorerService
from app.models.review import Review
from app.config import settings
from app.middleware.rate_limit import rate_limit
from fastapi import Request
from app.services.review import ReviewService
import logging


router = APIRouter(prefix="/reviews", tags=["Reviews"])
logger = logging.getLogger(__name__)


def build_review_response(review: Review) -> dict:
    """Shared helper to build the ReviewOut-compatible dict."""
    benchmark = review.benchmark_runs[0] if review.benchmark_runs else None
    total_score = ScorerService.calculate_total_score(
        [{"severity": i.severity, "category": i.category} for i in review.issues]
    )
    return {
        **review.__dict__,
        "issues": review.issues,
        "benchmark": benchmark,
        "total_score": total_score,
    }


@router.get("/options")
async def get_review_options():
    return {
        "queue_enabled": settings.use_celery,
        "rate_limiting_enabled": settings.enable_rate_limiting,
    }


@router.post("/", response_model=ReviewOut)
@rate_limit("10/hour")
async def create_review(request: Request, payload: ReviewCreate, db: AsyncSession = Depends(get_db)):
    if payload.execution_mode == "queued" and not settings.use_celery:
        raise HTTPException(
            status_code=503,
            detail="Queued reviews are disabled. Select direct processing or enable USE_CELERY."
        )

    review = Review(
        id=uuid4(),
        pr_url=payload.pr_url,
        raw_diff="",
        status="pending" if payload.execution_mode == "queued" else "processing"
    )
    db.add(review)
    await db.commit()
    await db.refresh(review)
    review_id = review.id

    if payload.execution_mode == "queued":
        try:
            from app.task import run_review_task

            run_review_task.delay(
                str(review_id),
                payload.pr_url,
                payload.include_benchmark
            )
        except Exception as exc:
            logger.exception("Could not queue review %s", review_id)
            review.status = "failed"
            await db.commit()
            raise HTTPException(
                status_code=503,
                detail="Could not queue the review. Check that Redis and the review worker are running."
            ) from exc

        return {
            **review.__dict__,
            "issues": [],
            "benchmark": None,
            "total_score": None,
        }

    service = None
    try:
        service = ReviewService(db)
        await service.run_analysis_only(
            review_id,
            payload.pr_url,
            payload.include_benchmark
        )
    except Exception as exc:
        logger.exception("Direct review failed for review %s", review_id)
        await db.rollback()
        failed_review = await db.get(Review, review_id)
        if failed_review:
            failed_review.status = "failed"
            await db.commit()

        if isinstance(exc, HTTPException):
            raise
        raise HTTPException(
            status_code=502,
            detail="Review processing failed. Check the backend logs for details."
        ) from exc
    finally:
        if service is not None:
            await service.shutdown()

    result = await db.execute(
        select(Review)
        .options(
            selectinload(Review.issues),
            selectinload(Review.benchmark_runs)
        )
        .filter(Review.id == review_id)
    )
    completed_review = result.scalar_one()
    return build_review_response(completed_review)


@router.get("/{review_id}", response_model=ReviewOut)
async def get_review(review_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Review)
        .options(
            selectinload(Review.issues),
            selectinload(Review.benchmark_runs)
        )
        .filter(Review.id == review_id)
    )
    review = result.scalar_one_or_none()

    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    return build_review_response(review)