# ⚛️ Quantum Risk API

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110-green?logo=fastapi)
![Qiskit](https://img.shields.io/badge/Qiskit-1.1-purple?logo=ibm)
![Streamlit](https://img.shields.io/badge/Streamlit-1.32-red?logo=streamlit)
![License](https://img.shields.io/badge/License-MIT-yellow)

A **hybrid classical-quantum financial risk analysis system** that computes
**VaR** and **CVaR** using either Monte Carlo simulation or Qiskit-based
quantum circuit estimation.

🚀 **[Live Demo → quantum-risk-api.streamlit.app](https://quantum-risk-api.streamlit.app/)**

---

## 📁 Project Structure

```
quantum-risk-api/
├── backend/
│   ├── main.py              # FastAPI app entrypoint
│   ├── requirements.txt
│   ├── api/
│   │   └── routes.py        # POST /risk, GET /health, GET /example
│   ├── services/
│   │   ├── risk_engine.py   # Orchestrator — routes to classical or quantum
│   │   ├── classical.py     # Monte Carlo VaR/CVaR
│   │   └── quantum.py       # Qiskit Aer quantum circuit estimator
│   ├── models/
│   │   └── schemas.py       # Pydantic request/response models
│   └── utils/
│       └── helpers.py       # Shared utilities
│
└── frontend/
    ├── app.py               # Streamlit demo UI
    └── requirements.txt
```

---

## 🚀 Quick Start

### 1. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

uvicorn main:app --reload --port 8000
```

Swagger UI → http://localhost:8000/docs  
Health check → http://localhost:8000/health

---

### 2. Frontend (separate terminal)

```bash
cd frontend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

streamlit run app.py
```

Opens at → http://localhost:8501

---

## 🔌 API Reference

### `POST /risk`

**Request body:**
```json
{
  "portfolio": [-0.021, 0.013, -0.008, 0.025, -0.032, 0.011, -0.005, 0.018],
  "method": "classical",
  "metric": "VaR",
  "confidence": 0.95,
  "num_simulations": 10000
}
```

| Field | Type | Description |
|-------|------|-------------|
| `portfolio` | `float[]` | Historical return observations (decimal, e.g. -0.02 = −2%) |
| `method` | `"classical" \| "quantum"` | Computation engine |
| `metric` | `"VaR" \| "CVaR"` | Risk metric |
| `confidence` | `float [0.50, 0.9999]` | Confidence level |
| `num_simulations` | `int [100, 100000]` | Monte Carlo paths (classical only) |

**Response:**
```json
{
  "metric": "VaR",
  "value": 0.028431,
  "method": "classical",
  "confidence": 0.95,
  "details": {
    "input_observations": 8,
    "num_simulations": 10000,
    "fitted_mean": -0.002125,
    "fitted_std": 0.018234,
    "note": "Monte Carlo simulation with Gaussian fit to observed returns"
  }
}
```

> A **positive** `value` represents a **loss**.  
> e.g. `0.028` → "2.8% loss at 95% confidence"

---

### Quick curl test

```bash
curl -X POST http://localhost:8000/risk \
  -H "Content-Type: application/json" \
  -d '{
    "portfolio": [-0.02, 0.01, -0.015, 0.03, -0.005, 0.02, -0.01],
    "method": "classical",
    "metric": "VaR",
    "confidence": 0.95
  }'
```

---

## ⚛️ How the Quantum Method Works

1. **Discretise** the observed return distribution into 8 bins (2³ — using 3 qubits).
2. **Encode** bin probabilities as quantum amplitudes using Qiskit's `initialize()`.
3. **Mark** loss states (bins with return < VaR threshold) with a phase oracle (Z gate).
4. **Simulate** the circuit on the Aer statevector/shot simulator (8 192 shots).
5. **Tally** measurement frequencies of loss-state bitstrings → quantum loss probability.
6. **Map** the quantum loss probability back to a risk value.

This demonstrates real quantum circuit construction and Aer simulation without requiring
the full complexity of Quantum Amplitude Estimation (QAE).

---

## 🧪 Example Test Inputs

### Conservative portfolio (low volatility)
```json
{
  "portfolio": [0.005, -0.003, 0.008, -0.002, 0.006, 0.001, -0.004, 0.007],
  "method": "classical",
  "metric": "CVaR",
  "confidence": 0.99
}
```

### Volatile portfolio
```json
{
  "portfolio": [-0.05, 0.04, -0.03, 0.06, -0.07, 0.02, -0.04, 0.05, -0.02, 0.03],
  "method": "quantum",
  "metric": "VaR",
  "confidence": 0.95
}
```

---

## 🛠 Architecture Notes

- **Frontend → Backend**: HTTP only via `requests.post`. No shared code.
- **Backend is independently runnable**: test it with curl or the Swagger UI.
- **Quantum engine degrades gracefully**: if Qiskit is unavailable, a 503 is returned with a clear message.
- **Pydantic v2**: all request validation is declarative in `schemas.py`.