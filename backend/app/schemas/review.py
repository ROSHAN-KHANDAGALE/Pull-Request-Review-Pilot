from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from uuid import UUID


class ReviewCreate(BaseModel):
    pr_url: str 
    include_benchmark: bool = False
    
    @field_validator("pr_url")
    @classmethod
    def validate_github_url(cls, v: str) -> str:
        if not v.startswith("https://github.com/"):
            raise ValueError("pr_url must start with https://github.com/")
        return v


class IssueOut(BaseModel):
    id: UUID
    severity: str
    category: str
    title: str
    description: str
    file_path: str | None
    line_number: int | None
    suggestion: str | None
    model_config = {"from_attributes": True}


class BenchmarkOut(BaseModel):
    agent_score: int
    baseline_score: int
    agent_issue_count: int
    baseline_issue_count: int
    model_config = {"from_attributes": True}


class ReviewOut(BaseModel):
    id: UUID
    pr_url: str
    status: str
    created_at: datetime
    completed_at: datetime | None
    issues: list[IssueOut] = Field(default_factory=list)
    benchmark: BenchmarkOut | None
    total_score: int | None
    model_config = {"from_attributes": True}