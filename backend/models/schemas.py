"""
Pydantic models for request validation and response serialization.
Keeps the API contract explicit and self-documenting.
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Literal
from enum import Enum


class RiskMethod(str, Enum):
    classical = "classical"
    quantum = "quantum"


class RiskMetric(str, Enum):
    VaR = "VaR"
    CVaR = "CVaR"


class RiskRequest(BaseModel):
    """
    Input model for the /risk endpoint.

    portfolio: list of historical returns (e.g. [-0.02, 0.01, 0.03, ...])
               OR portfolio weights if combined with market scenario generation.
               For this demo, we treat each value as a daily return observation.
    method:    "classical" uses Monte Carlo; "quantum" uses Qiskit Aer simulation.
    metric:    "VaR" (Value at Risk) or "CVaR" (Conditional VaR / Expected Shortfall).
    confidence: confidence level, e.g. 0.95 means 95% VaR.
    num_simulations: number of Monte Carlo paths (classical only).
    """
    portfolio: List[float] = Field(
        ...,
        min_length=2,
        description="List of historical return observations (e.g. [-0.02, 0.01, ...])"
    )
    method: RiskMethod = Field(
        default=RiskMethod.classical,
        description="Computation method: 'classical' or 'quantum'"
    )
    metric: RiskMetric = Field(
        default=RiskMetric.VaR,
        description="Risk metric to compute: 'VaR' or 'CVaR'"
    )
    confidence: float = Field(
        default=0.95,
        ge=0.50,
        le=0.9999,
        description="Confidence level between 0.50 and 0.9999"
    )
    num_simulations: int = Field(
        default=10000,
        ge=100,
        le=100000,
        description="Number of Monte Carlo simulations (classical method only)"
    )

    @field_validator("portfolio")
    @classmethod
    def portfolio_must_be_finite(cls, v):
        import math
        if any(not math.isfinite(x) for x in v):
            raise ValueError("All portfolio values must be finite numbers")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "portfolio": [-0.02, 0.01, -0.015, 0.03, -0.005, 0.02, -0.01, 0.005],
                "method": "classical",
                "metric": "VaR",
                "confidence": 0.95,
                "num_simulations": 10000
            }
        }
    }


class RiskResponse(BaseModel):
    """
    Output model returned by the /risk endpoint.
    """
    metric: str = Field(..., description="The risk metric computed: VaR or CVaR")
    value: float = Field(..., description="Computed risk value (negative = loss)")
    method: str = Field(..., description="Method used for computation")
    confidence: float = Field(..., description="Confidence level used")
    details: dict = Field(
        default_factory=dict,
        description="Additional details (e.g. distribution stats, circuit info)"
    )


class HealthResponse(BaseModel):
    status: str
    version: str