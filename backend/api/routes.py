"""
API route definitions.

All routes are collected here and mounted into the FastAPI app in main.py.
Keeping routes separate from the app entrypoint makes testing easier.
"""

from fastapi import APIRouter, HTTPException
from models.schemas import RiskRequest, RiskResponse, HealthResponse
from services.risk_engine import compute_risk

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """
    Simple liveness probe.
    Returns 200 OK with service version when the API is running.
    """
    return HealthResponse(status="ok", version="1.0.0")


@router.post("/risk", response_model=RiskResponse, tags=["Risk"])
async def compute_risk_endpoint(request: RiskRequest):
    """
    Compute a financial risk metric for a given portfolio.

    - **portfolio**: list of historical return observations (decimal, e.g. -0.02 = -2%)
    - **method**: `classical` (Monte Carlo) or `quantum` (Qiskit Aer)
    - **metric**: `VaR` or `CVaR`
    - **confidence**: confidence level, e.g. 0.95 for 95% VaR
    - **num_simulations**: Monte Carlo paths (classical only, default 10 000)

    Returns the computed risk value along with method metadata.
    A **positive** value represents a loss (e.g. 0.025 = 2.5% loss at 95% confidence).
    """
    try:
        result = compute_risk(request)
        return result
    except RuntimeError as e:
        # e.g. Qiskit not installed
        raise HTTPException(status_code=503, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/example", tags=["Risk"])
async def get_example_input():
    """
    Returns an example request payload so users can quickly test the API.
    """
    return {
        "description": "Example portfolio of 20 daily returns",
        "example_request": {
            "portfolio": [
                -0.021, 0.013, -0.008, 0.025, -0.032,
                0.011, -0.005, 0.018, -0.027, 0.009,
                0.004, -0.014, 0.031, -0.006, 0.022,
                -0.019, 0.007, -0.011, 0.016, -0.003
            ],
            "method": "classical",
            "metric": "VaR",
            "confidence": 0.95,
            "num_simulations": 10000
        },
        "curl_example": (
            'curl -X POST http://localhost:8000/risk '
            '-H "Content-Type: application/json" '
            '-d \'{"portfolio":[-0.02,0.01,-0.015,0.03],'
            '"method":"classical","metric":"VaR","confidence":0.95}\''
        )
    }