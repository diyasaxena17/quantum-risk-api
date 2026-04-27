"""
Classical Monte Carlo risk engine.

Fits a normal distribution to the observed portfolio returns,
simulates N paths, then computes VaR and CVaR from the empirical
loss distribution.
"""

import numpy as np
from typing import Tuple


def simulate_returns(
    observed_returns: list[float],
    num_simulations: int = 10_000,
    seed: int = 42
) -> np.ndarray:
    """
    Fit a Gaussian to the observed returns and draw num_simulations samples.

    Returns an array of simulated returns (negative = loss).
    """
    returns = np.array(observed_returns)
    mu = returns.mean()
    sigma = returns.std(ddof=1)  # sample std deviation

    rng = np.random.default_rng(seed)
    simulated = rng.normal(loc=mu, scale=sigma, size=num_simulations)
    return simulated


def compute_var(simulated_returns: np.ndarray, confidence: float) -> float:
    """
    Value at Risk: the loss not exceeded at the given confidence level.

    Convention: VaR is expressed as a positive number representing the loss.
    e.g. VaR = 0.03 means "we expect to lose no more than 3% with 95% confidence."

    Internally, losses are the negative of returns.
    """
    losses = -simulated_returns  # flip sign so losses are positive
    var = float(np.percentile(losses, confidence * 100))
    return var


def compute_cvar(simulated_returns: np.ndarray, confidence: float) -> float:
    """
    Conditional VaR (Expected Shortfall): the expected loss *given* that
    the loss exceeds the VaR threshold. Always >= VaR.
    """
    losses = -simulated_returns
    var = np.percentile(losses, confidence * 100)
    tail_losses = losses[losses >= var]

    if len(tail_losses) == 0:
        return float(var)  # edge case: all losses below threshold

    cvar = float(tail_losses.mean())
    return cvar


def run_classical(
    portfolio: list[float],
    metric: str,
    confidence: float,
    num_simulations: int = 10_000
) -> Tuple[float, dict]:
    """
    Main entry point for classical computation.

    Returns (risk_value, details_dict).
    """
    simulated = simulate_returns(portfolio, num_simulations=num_simulations)

    mu = float(np.mean(portfolio))
    sigma = float(np.std(portfolio, ddof=1))

    if metric == "VaR":
        value = compute_var(simulated, confidence)
    elif metric == "CVaR":
        value = compute_cvar(simulated, confidence)
    else:
        raise ValueError(f"Unknown metric: {metric}")

    details = {
        "input_observations": len(portfolio),
        "num_simulations": num_simulations,
        "fitted_mean": round(mu, 6),
        "fitted_std": round(sigma, 6),
        "note": "Monte Carlo simulation with Gaussian fit to observed returns"
    }

    return value, details