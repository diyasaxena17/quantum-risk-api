"""
Quantum Risk API — FastAPI application entrypoint.

Run with:
    uvicorn main:app --reload --port 8000

Interactive docs available at:
    http://localhost:8000/docs   (Swagger UI)
    http://localhost:8000/redoc  (ReDoc)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router

# ---------------------------------------------------------------------------
# App instantiation
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Quantum Risk API",
    description=(
        "A hybrid classical-quantum financial risk analysis service. "
        "Compute VaR and CVaR using Monte Carlo simulation or "
        "Qiskit-based quantum circuit estimation."
    ),
    version="1.0.0",
    contact={
        "name": "Quantum Risk API",
    },
    license_info={"name": "MIT"},
)

# ---------------------------------------------------------------------------
# CORS — allow the Streamlit frontend (and any local dev tool) to call the API
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Mount routes
# ---------------------------------------------------------------------------
app.include_router(router)


# ---------------------------------------------------------------------------
# Root redirect to docs
# ---------------------------------------------------------------------------
@app.get("/", include_in_schema=False)
async def root():
    return {
        "message": "Quantum Risk API is running.",
        "docs": "/docs",
        "health": "/health",
        "risk_endpoint": "POST /risk",
        "example": "/example"
    }