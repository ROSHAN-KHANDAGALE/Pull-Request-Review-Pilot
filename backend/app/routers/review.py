from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.db import get_db
from app.schemas.review import ReviewCreate, ReviewOut
from app.services.review import ReviewService
from app.services.scorer import ScorerService
from app.models.review import Review

from app.middleware.rate_limit import limiter
from fastapi import Request


router = APIRouter(prefix="/reviews", tags=["Reviews"])


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


@router.post("/", response_model=ReviewOut)
@limiter.limit("10/hour")
async def create_review(request: Request, payload: ReviewCreate, db: AsyncSession = Depends(get_db)):
    service = ReviewService(db)
    try:
        review = await service.run_full_review(payload.pr_url, payload.include_benchmark)

        # Re-fetch with relationships eagerly loaded
        result = await db.execute(
            select(Review)
            .options(
                selectinload(Review.issues),
                selectinload(Review.benchmark_runs)
            )
            .filter(Review.id == review.id)
        )
        final_review = result.scalar_one()
        return build_review_response(final_review)

    finally:
        await service.shutdown()


@router.get("/{review_id}", response_model=ReviewOut)
async def get_review(review_id: str, db: AsyncSession = Depends(get_db)):
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