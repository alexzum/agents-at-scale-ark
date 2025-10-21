"""Pydantic models for AB Experiment resources."""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from enum import Enum


class ABExperimentStatus(str, Enum):
    """Status of an AB experiment."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    APPLIED = "applied"


class ABExperimentTargetType(str, Enum):
    """Type of target being modified."""
    AGENT = "agent"
    TEAM = "team"


class ABExperimentWinner(str, Enum):
    """Winner of the AB experiment."""
    BASELINE = "baseline"
    EXPERIMENT = "experiment"
    TIE = "tie"


class MetricsData(BaseModel):
    """Performance metrics data from metrics evaluator."""
    evaluatorName: str = Field(alias="evaluatorName")
    cost: float
    executionTime: str = Field(alias="executionTime")
    tokens: int


class ABExperimentTargetChanges(BaseModel):
    """Changes to apply to a target."""
    model: Optional[str] = None
    instructions: Optional[str] = None


class ABExperimentModifications(BaseModel):
    """Modifications made in the experiment variant."""
    input: Optional[str] = None
    targetType: Optional[ABExperimentTargetType] = None
    targetName: Optional[str] = None
    targetChanges: Optional[ABExperimentTargetChanges] = None


class ABExperimentVariantResults(BaseModel):
    """Results for a single variant (baseline or experiment)."""
    overallScore: float
    criteria: Dict[str, float]
    cost: Optional[float] = None
    latency: Optional[float] = None
    metrics: Optional[MetricsData] = None


class ABExperimentResults(BaseModel):
    """Aggregated results comparing baseline and experiment."""
    baseline: ABExperimentVariantResults
    experiment: ABExperimentVariantResults
    winner: ABExperimentWinner
    improvement: float
    qualityWinner: Optional[ABExperimentWinner] = Field(alias="qualityWinner", default=None)
    performanceWinner: Optional[ABExperimentWinner] = Field(alias="performanceWinner", default=None)


class ABExperimentEvaluations(BaseModel):
    """Evaluation resource names for both variants."""
    baseline: List[str]
    experiment: List[str]


class ABExperiment(BaseModel):
    """Complete AB experiment definition."""
    id: str
    status: ABExperimentStatus
    createdAt: str
    createdBy: Optional[str] = None
    variantQuery: str
    variantAgent: Optional[str] = None
    modifications: ABExperimentModifications
    evaluations: Optional[ABExperimentEvaluations] = None
    results: Optional[ABExperimentResults] = None
    appliedAt: Optional[str] = None
    appliedWinner: Optional[ABExperimentWinner] = None


class CreateABExperimentRequest(BaseModel):
    """Request to create a new AB experiment."""
    modifications: ABExperimentModifications
    createdBy: Optional[str] = None


class UpdateABExperimentRequest(BaseModel):
    """Request to update an AB experiment."""
    status: Optional[ABExperimentStatus] = None
    results: Optional[ABExperimentResults] = None


class ApplyWinnerRequest(BaseModel):
    """Request to apply the winning variant."""
    winner: ABExperimentWinner
