import uuid
from sqlalchemy import DateTime
from sqlalchemy import Text, String, Integer, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import mapped_column, relationship
from app.db import Base

class Review(Base):
    __tablename__ = 'reviews'

    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pr_url = mapped_column(String, nullable=False)
    raw_diff = mapped_column(String, nullable=False)
    status = mapped_column(String, nullable=False, default='pending')  # pending, running, completed, failed
    created_at = mapped_column(DateTime(timezone=True), nullable=False, default=func.now())
    completed_at = mapped_column(DateTime(timezone=True), nullable=True)

    issues = relationship("Issue", back_populates="review", cascade="all, delete-orphan")
    benchmark_runs = relationship("BenchmarkRun", back_populates="review")


class Issue(Base):
    __tablename__ = 'issues'

    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    review_id = mapped_column(UUID(as_uuid=True), ForeignKey('reviews.id'), nullable=False)
    severity = mapped_column(String, nullable=False)  # critical, major, minor, info
    category = mapped_column(String, nullable=False)  # correctness, security, maintainability, test_coverage, documentation
    title = mapped_column(String, nullable=False)
    description = mapped_column(Text, nullable=False)
    file_path = mapped_column(String, nullable=True)
    line_number = mapped_column(Integer, nullable=True)
    suggestion = mapped_column(Text, nullable=True)

    review = relationship("Review", back_populates="issues")


class BenchmarkRun(Base):
    __tablename__ = 'benchmark_runs'

    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    review_id = mapped_column(UUID(as_uuid=True), ForeignKey('reviews.id'), nullable=False)
    agent_score = mapped_column(Integer)
    baseline_score = mapped_column(Integer)
    agent_issue_count = mapped_column(Integer)
    baseline_issue_count = mapped_column(Integer)
    created_at = mapped_column(DateTime(timezone=True), nullable=False, default=func.now())

    review = relationship("Review", back_populates="benchmark_runs")
