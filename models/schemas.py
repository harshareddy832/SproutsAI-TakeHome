from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


class CandidateResult(BaseModel):
    name: str
    filename: str
    similarity_score: float
    match_percentage: float
    ai_summary: Optional[str] = None
    ai_provider: Optional[str] = None
    ai_generated: Optional[bool] = False
    resume_text: Optional[str] = None  # Include resume text for AI processing


class RecommendationRequest(BaseModel):
    job_description: str
    files: List[str]


class RecommendationResponse(BaseModel):
    success: bool
    message: str
    candidates: List[CandidateResult]
    total_processed: int
    processing_time: float


class AIConfiguration(BaseModel):
    provider: str
    model: Optional[str] = None  # Auto-selected based on provider
    api_key: str
    custom_endpoint: Optional[str] = None
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 200


class AIConfigResponse(BaseModel):
    success: bool
    message: str
    provider_info: Optional[Dict[str, Any]] = None


class GenerateSummariesRequest(BaseModel):
    job_description: str
    candidates: List[Dict[str, Any]]
    max_summaries: Optional[int] = 5


class GenerateSummariesResponse(BaseModel):
    success: bool
    message: str
    candidates: List[CandidateResult]
    stats: Optional[Dict[str, Any]] = None


class ProvidersResponse(BaseModel):
    providers: Dict[str, List[str]]


class HealthCheck(BaseModel):
    status: str
    timestamp: datetime