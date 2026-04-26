from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.db import get_db
from app.schemas.review import ReviewCreate, ReviewOut
from app.services.scorer import ScorerService
from app.models.review import Review

from app.middleware.rate_limit import limiter
from fastapi import Request

from app.task import run_review_task
from app.models.review import Review
import uuid


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
    # Create review record immediately with pending status
    review = Review(
        id=uuid.uuid4(),
        pr_url=payload.pr_url,
        raw_diff="",
        status="pending"
    )
    db.add(review)
    await db.commit()
    await db.refresh(review)

    # Queue background task
    run_review_task.delay(
        str(review.id),
        payload.pr_url,
        payload.include_benchmark
    )

    # Return immediately — frontend will poll GET /reviews/{id}
    return {
        **review.__dict__,
        "issues": [],
        "benchmark": None,
        "total_score": None,
    }


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