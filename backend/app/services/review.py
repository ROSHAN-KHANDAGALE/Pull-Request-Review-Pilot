from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.review import Review, Issue, BenchmarkRun
from app.services.github import GitHubService
from app.services.llm import LLMService
from app.services.scorer import ScorerService
from sqlalchemy import select


class ReviewService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.github = GitHubService()
        self.llm = LLMService()
        self.scorer = ScorerService()

    async def run_full_review(self, pr_url: str, include_benchmark: bool):
        # 1. Get Diff
        diff_text = await self.github.fetch_diff(pr_url)

        # 2. Create Initial Review Record
        review = Review(pr_url=pr_url, raw_diff=diff_text, status="processing")
        self.db.add(review)
        await self.db.flush() # Gets us the review.id

        # 3. Get AI Analysis
        analysis = await self.llm.analyze_diff(diff_text)

        # 4. Create Issue Objects
        issues_data = analysis.get("issues", [])
        for data in issues_data:
            issue = Issue(
                review_id=review.id,
                **data # Maps severity, category, etc.
            )
            self.db.add(issue)

        # 5. Handle Benchmark
        if include_benchmark and "benchmark" in analysis:
            bench = BenchmarkRun(
                review_id=review.id,
                **analysis["benchmark"]
            )
            self.db.add(bench)

        # 6. Finalize Review
        review.status = "completed"
        review.completed_at = datetime.now(timezone.utc)
        
        await self.db.commit()
        await self.db.refresh(review)
        return review


    async def shutdown(self):
        await self.github.close()


    async def run_analysis_only(self, review_id: str, pr_url: str, include_benchmark: bool):

        # Fetch existing review record
        result = await self.db.execute(select(Review).where(Review.id == review_id))
        review = result.scalar_one_or_none()

        if not review:
            raise ValueError(f"Review {review_id} not found")

        # Fetch diff from GitHub
        diff_text = await self.github.fetch_diff(pr_url)
        review.raw_diff = diff_text

        # Run LLM analysis
        analysis = await self.llm.analyze_diff(diff_text)
        issues_data = analysis.get("issues", [])

        # Persist issues
        for data in issues_data:
            issue = Issue(
                review_id=review.id,
                severity=data.get("severity", "info"),
                category=data.get("category", "maintainability"),
                title=data.get("title", "Untitled"),
                description=data.get("description", ""),
                file_path=data.get("file_path"),
                line_number=data.get("line_number"),
                suggestion=data.get("suggestion"),
            )
            self.db.add(issue)

        # Calculate scores
        issue_dicts = [
            {
                "severity": d.get("severity", "info"),
                "category": d.get("category", "maintainability")
            }
            for d in issues_data
        ]

        if include_benchmark:
            agent_score = ScorerService.calculate_total_score(issue_dicts)
            baseline_score = ScorerService.calculate_baseline_score(issue_dicts)
            bench = BenchmarkRun(
                review_id=review.id,
                agent_score=agent_score,
                baseline_score=baseline_score,
                agent_issue_count=len(issues_data),
                baseline_issue_count=len(issues_data),
            )
            self.db.add(bench)

        # Mark complete
        review.status = "completed"
        review.completed_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(review)
        return review