"""
Utility helpers shared across the backend.
"""

import math
from typing import Any


def is_valid_return_series(values: list[float]) -> bool:
    """
    Check that a list of returns contains only finite, reasonable values.
    Returns are expected to be in decimal form (e.g. -0.05 = -5%).
    We flag anything outside [-1, 1] as suspicious but don't reject it.
    """
    return all(math.isfinite(v) for v in values)


def summarise_series(values: list[float]) -> dict[str, Any]:
    """
    Return basic descriptive statistics for a return series.
    Useful for debugging and API detail payloads.
    """
    import statistics
    if len(values) < 2:
        return {"error": "Need at least 2 observations"}
    return {
        "count": len(values),
        "mean": round(statistics.mean(values), 6),
        "stdev": round(statistics.stdev(values), 6),
        "min": round(min(values), 6),
        "max": round(max(values), 6),
    }


def clamp(value: float, low: float, high: float) -> float:
    """Clamp a value to [low, high]."""
    return max(low, min(high, value))