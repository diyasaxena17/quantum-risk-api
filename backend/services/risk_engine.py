"""
Risk engine — the single point of dispatch.

Accepts a validated RiskRequest and routes to either the classical
Monte Carlo engine or the quantum Qiskit engine.
"""

from models.schemas import RiskRequest, RiskResponse
from services.classical import run_classical
from services.quantum import run_quantum


def compute_risk(request: RiskRequest) -> RiskResponse:
    """
    Orchestrate risk computation based on the requested method.

    Args:
        request: A validated RiskRequest Pydantic model.

    Returns:
        A RiskResponse with the computed metric value and metadata.
    """
    method = request.method.value
    metric = request.metric.value

    if method == "classical":
        value, details = run_classical(
            portfolio=request.portfolio,
            metric=metric,
            confidence=request.confidence,
            num_simulations=request.num_simulations
        )
    elif method == "quantum":
        value, details = run_quantum(
            portfolio=request.portfolio,
            metric=metric,
            confidence=request.confidence,
            n_qubits=3,    # 8 bins — enough for demo without deep circuits
            shots=8192     # sufficient for stable probability estimates
        )
    else:
        raise ValueError(f"Unknown method: {method}")

    return RiskResponse(
        metric=metric,
        value=round(value, 6),
        method=method,
        confidence=request.confidence,
        details=details
    )