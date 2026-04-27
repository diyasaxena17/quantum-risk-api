"""
Quantum risk engine using Qiskit.

Approach (deliberately simple and transparent):
1. Discretise the observed return distribution into N buckets (bins).
2. Encode the probability distribution into a quantum state using
   RY rotations — each amplitude^2 = probability of that bucket.
3. Mark "loss" states (bins corresponding to negative returns) with
   a phase flip (Z gate), then measure.
4. Use the measurement frequencies of loss states to estimate the
   probability that a return falls below a loss threshold.
5. Invert this probability to approximate VaR and CVaR.

This demonstrates real quantum circuit construction and simulation
without requiring full Quantum Amplitude Estimation (QAE).
"""

import numpy as np
from typing import Tuple

# ---------------------------------------------------------------------------
# Qiskit imports — all within try/except for graceful degradation
# ---------------------------------------------------------------------------
try:
    from qiskit import QuantumCircuit, transpile
    from qiskit_aer import AerSimulator
    QISKIT_AVAILABLE = True
except ImportError:
    QISKIT_AVAILABLE = False


# ---------------------------------------------------------------------------
# Distribution encoding helpers
# ---------------------------------------------------------------------------

def _discretise_distribution(
    returns: list[float],
    n_qubits: int = 3
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Bin the observed returns into 2^n_qubits buckets.

    Returns:
        bin_centers : midpoint return value for each bin
        probabilities: empirical probability for each bin (sums to 1)
    """
    n_bins = 2 ** n_qubits
    counts, edges = np.histogram(returns, bins=n_bins, density=False)
    probs = counts / counts.sum()
    centers = 0.5 * (edges[:-1] + edges[1:])
    return centers, probs


def _build_distribution_circuit(probabilities: np.ndarray) -> "QuantumCircuit":
    """
    Build a quantum circuit that encodes `probabilities` into amplitudes.

    Strategy: use Qiskit's built-in initialize() to set the state vector
    directly to sqrt(p_i) amplitudes.  This is equivalent to what a
    full amplitude-encoding circuit would produce, and lets us focus on
    the measurement / estimation layer rather than the encoding layer.

    For n_qubits = 3 we get an 8-dimensional state space (8 bins).
    """
    n = len(probabilities)
    n_qubits = int(np.ceil(np.log2(n)))
    # Pad to next power of 2 if needed
    padded = np.zeros(2 ** n_qubits)
    padded[:n] = probabilities
    padded = padded / padded.sum()          # renormalise after padding

    amplitudes = np.sqrt(padded)            # amplitude = sqrt(probability)

    qc = QuantumCircuit(n_qubits, n_qubits)
    qc.initialize(amplitudes, list(range(n_qubits)))
    return qc


def _mark_loss_states(
    qc: "QuantumCircuit",
    loss_bin_indices: list[int],
    n_qubits: int
) -> "QuantumCircuit":
    """
    Apply a Z (phase-flip) to each 'loss' basis state.

    This doesn't change measurement probabilities, but it's a clean way
    to demonstrate how we'd mark states in a Grover-style oracle.
    In a full QAE pipeline, this oracle would feed into amplitude estimation.

    Here, we simply track which bins are loss bins and tally
    their measurement frequencies directly.
    """
    # Z gate on the least-significant qubit for illustrative purposes
    # (In a real QAE oracle, you'd use a multi-controlled-Z on each loss state)
    if loss_bin_indices:
        qc.barrier()
        qc.z(0)   # lightweight marker — doesn't affect outcome probabilities
    return qc


# ---------------------------------------------------------------------------
# Main quantum computation
# ---------------------------------------------------------------------------

def run_quantum(
    portfolio: list[float],
    metric: str,
    confidence: float,
    n_qubits: int = 3,
    shots: int = 8192
) -> Tuple[float, dict]:
    """
    Main entry point for quantum computation.

    Returns (risk_value, details_dict).
    """
    if not QISKIT_AVAILABLE:
        raise RuntimeError(
            "Qiskit / qiskit-aer is not installed. "
            "Run: pip install qiskit qiskit-aer"
        )

    returns = np.array(portfolio)
    n_bins = 2 ** n_qubits

    # ------------------------------------------------------------------ #
    # Step 1: Discretise the return distribution
    # ------------------------------------------------------------------ #
    bin_centers, probabilities = _discretise_distribution(returns, n_qubits)

    # ------------------------------------------------------------------ #
    # Step 2: Identify which bins represent losses
    #         (return < 0 or below a threshold derived from confidence)
    # ------------------------------------------------------------------ #
    # VaR threshold = percentile of the (classical) distribution
    # We use this to label "loss" bins in the quantum circuit
    var_threshold = float(np.percentile(returns, (1 - confidence) * 100))
    loss_bin_indices = [i for i, c in enumerate(bin_centers) if c < var_threshold]

    # ------------------------------------------------------------------ #
    # Step 3: Build and run the quantum circuit
    # ------------------------------------------------------------------ #
    qc = _build_distribution_circuit(probabilities)
    qc = _mark_loss_states(qc, loss_bin_indices, n_qubits)

    # Add measurements
    qc.barrier()
    qc.measure(list(range(n_qubits)), list(range(n_qubits)))

    # ------------------------------------------------------------------ #
    # Step 4: Simulate on Aer
    # ------------------------------------------------------------------ #
    simulator = AerSimulator()
    compiled = transpile(qc, simulator)
    job = simulator.run(compiled, shots=shots)
    result = job.result()
    counts = result.get_counts()

    # ------------------------------------------------------------------ #
    # Step 5: Estimate risk from measurement probabilities
    # ------------------------------------------------------------------ #
    # Each bitstring corresponds to a bin index
    # P(loss) = sum of measurement frequencies for loss bins
    total_shots = sum(counts.values())
    loss_prob_quantum = 0.0

    for bitstring, count in counts.items():
        # Qiskit returns bitstrings in little-endian order
        bin_idx = int(bitstring[::-1], 2)  # reverse bits → bin index
        if bin_idx < len(bin_centers) and bin_centers[bin_idx] < var_threshold:
            loss_prob_quantum += count / total_shots

    # ------------------------------------------------------------------ #
    # Step 6: Convert quantum loss probability → risk metric
    # ------------------------------------------------------------------ #
    # We use the quantum-estimated loss probability to recalibrate VaR/CVaR
    # relative to the empirical distribution.
    #
    # Interpretation:
    #   quantum_loss_prob ≈ P(return < var_threshold)
    #   We map this back to a return quantile for VaR,
    #   or compute the conditional mean of loss bins for CVaR.

    loss_bins_mask = np.array([c < var_threshold for c in bin_centers])
    loss_returns = bin_centers[loss_bins_mask]
    loss_probs = probabilities[loss_bins_mask]

    if metric == "VaR":
        # VaR estimate: expected bin center of the worst (1-confidence) tail,
        # weighted by quantum measurement frequencies
        if loss_prob_quantum > 0 and len(loss_returns) > 0:
            # Re-weight by quantum measurement to get quantum-adjusted VaR
            quantum_counts_loss = np.array([
                counts.get(format(i, f'0{n_qubits}b')[::-1], 0)
                for i in range(n_bins)
                if i < len(bin_centers) and bin_centers[i] < var_threshold
            ], dtype=float)
            if quantum_counts_loss.sum() > 0:
                quantum_counts_loss /= quantum_counts_loss.sum()
                value = float(-np.dot(loss_returns, quantum_counts_loss))
            else:
                value = float(-loss_returns.min()) if len(loss_returns) > 0 else 0.0
        else:
            value = float(-var_threshold)

    elif metric == "CVaR":
        # CVaR: expected loss in the tail, quantum-probability-weighted
        if len(loss_returns) > 0 and loss_probs.sum() > 0:
            w = loss_probs / loss_probs.sum()
            cvar_return = float(np.dot(loss_returns, w))
            # Scale by quantum-estimated tail probability
            value = float(-cvar_return * (1 + loss_prob_quantum))
        else:
            value = float(-var_threshold)
    else:
        raise ValueError(f"Unknown metric: {metric}")

    # ------------------------------------------------------------------ #
    # Step 7: Build details payload
    # ------------------------------------------------------------------ #
    details = {
        "n_qubits": n_qubits,
        "n_bins": n_bins,
        "shots": shots,
        "circuit_depth": qc.depth(),
        "circuit_gates": qc.count_ops(),
        "quantum_loss_probability": round(loss_prob_quantum, 6),
        "var_threshold_used": round(var_threshold, 6),
        "loss_bins_count": int(loss_bins_mask.sum()),
        "top_measurement_counts": dict(
            sorted(counts.items(), key=lambda x: -x[1])[:5]
        ),
        "note": (
            "Distribution encoded as quantum amplitudes via initialize(); "
            "measurement probabilities used to estimate tail risk."
        )
    }

    return value, details