from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ReviewStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class CodeQualityFinding(BaseModel):
    file: str
    line: int | None = None
    severity: Severity
    issue: str
    suggestion: str | None = None


class CodeQualityReview(BaseModel):
    findings: list[CodeQualityFinding] = Field(default_factory=list)
    summary: str


class FunctionalityAlignment(str, Enum):
    GOOD = "good"
    PARTIAL = "partial"
    POOR = "poor"
    UNABLE_TO_VERIFY = "unable-to-verify"


class FunctionalityReview(BaseModel):
    alignment: FunctionalityAlignment
    covered_requirements: list[str] = Field(default_factory=list)
    missing_requirements: list[str] = Field(default_factory=list)
    out_of_scope: list[str] = Field(default_factory=list)
    summary: str
    jira_available: bool = True


class PRReviewRequest(BaseModel):
    repository: str
    pr_number: int
    branch_name: str
    commit_sha: str | None = None


class PRReviewResponse(BaseModel):
    review_id: str
    status: ReviewStatus
    created_at: datetime
    message: str


class PRReviewResult(BaseModel):
    review_id: str
    repository: str
    pr_number: int
    branch_name: str
    jira_ticket: str | None
    status: ReviewStatus
    code_quality: CodeQualityReview | None = None
    functionality: FunctionalityReview | None = None
    execution_time_ms: int
    created_at: datetime
    completed_at: datetime | None = None
    error: str | None = None
    ark_query_name: str | None = None


class JiraTicket(BaseModel):
    key: str
    summary: str
    description: str | None = None
    status: str
    labels: list[str] = Field(default_factory=list)
    acceptance_criteria: str | None = None


class PRMetadata(BaseModel):
    number: int
    title: str
    body: str | None
    head_branch: str
    base_branch: str
    commit_sha: str
    files_changed: list[str] = Field(default_factory=list)
    diff: str
    additions: int
    deletions: int
    changed_files_count: int

