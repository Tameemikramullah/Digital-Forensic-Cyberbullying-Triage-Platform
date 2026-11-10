from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any


class ClassificationResultRead(BaseModel):
    id: int
    evidence_id: int
    model_name: str
    model_version: str = "1.0"
    prediction: str
    confidence_score: float
    risk_level: Optional[str] = None
    threshold: float = 0.7
    processing_time_ms: Optional[int] = None
    preprocessing_steps: Optional[str] = None
    explanation_method: Optional[str] = None
    explanation_summary: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ExplanationResponse(BaseModel):
    prediction: str
    confidence: float
    risk_level: str
    requires_further_review: bool
    top_features: List[Dict[str, Any]]


class TriageRequest(BaseModel):
    model_name: str = "svm"

    model_config = {"protected_namespaces": ()}


class TriageResponse(BaseModel):
    evidence_id: int
    prediction: str
    confidence: float = Field(description="This model's output probability for its predicted class; calibration varies by model.")
    risk_score: float = Field(description="This model's output probability mass summed across the five cyberbullying classes; calibration varies by model.")
    risk_level: str
    requires_further_review: bool
    model_version: str = "1.0"
    threshold: float = 0.7
    processing_time_ms: Optional[int] = None
    preprocessing_steps: Optional[str] = None
    explanation_method: Optional[str] = None
    explanation_reason: Optional[str] = None
    explanation_summary: str
    top_features: List[Dict[str, Any]]
    model_agreement: Optional[Dict[str, Any]] = None


class EnsembleRequest(BaseModel):
    model_names: List[str] = ["svm", "logistic", "naive_bayes", "cnn", "bert"]

    model_config = {"protected_namespaces": ()}


class ModelVote(BaseModel):
    model_name: str
    prediction: str
    confidence: float = Field(description="This model's top-class output probability, shown for context and not weighted across models; calibration varies by model.")
    explanation_available: bool = False
    explanation_method: Optional[str] = None
    explanation_reason: Optional[str] = None


class EnsembleResponse(BaseModel):
    evidence_id: int
    prediction: str
    confidence: float = Field(description="Winning label vote share: votes for the plurality label divided by successful model votes; stored as 0 when there are no valid votes and risk_level is UNKNOWN.")
    risk_score: float = Field(description="Cyberbullying vote share: successful votes for any label except not_cyberbullying divided by successful model votes; stored as 0 when risk_level is UNKNOWN because there are no valid votes.")
    risk_level: str
    requires_further_review: bool
    threshold: float
    processing_time_ms: Optional[int] = None
    preprocessing_steps: Optional[str] = None
    explanation_method: Optional[str] = None
    explanation_summary: str
    top_features: List[Dict[str, Any]]
    votes: List[ModelVote]
    model_agreement: Dict[str, Any]
