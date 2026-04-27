"""
Quantum Risk API — Streamlit Frontend Demo

Calls the backend API via HTTP (requests.post).
Run with:
    streamlit run app.py

Make sure the backend is running at http://localhost:8000 first.
"""

import streamlit as st
import requests
import json
import time

# ------------------------------------------------------------------ #
# Configuration
# ------------------------------------------------------------------ #
API_BASE_URL = "http://localhost:8000"
RISK_ENDPOINT = f"{API_BASE_URL}/risk"

# ------------------------------------------------------------------ #
# Page setup
# ------------------------------------------------------------------ #
st.set_page_config(
    page_title="Quantum Risk API",
    page_icon="⚛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------------------------------------------------------ #
# Custom CSS — clean, professional dark theme with quantum accents
# ------------------------------------------------------------------ #
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Inter:wght@300;400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .stApp {
        background: #0a0e1a;
        color: #e0e6f0;
    }

    h1, h2, h3 {
        font-family: 'Space Mono', monospace !important;
    }

    .metric-card {
        background: linear-gradient(135deg, #0d1f3c 0%, #0a1628 100%);
        border: 1px solid #1e3a5f;
        border-radius: 12px;
        padding: 28px 32px;
        text-align: center;
        box-shadow: 0 0 30px rgba(0, 120, 255, 0.08);
    }

    .metric-label {
        font-family: 'Space Mono', monospace;
        font-size: 11px;
        letter-spacing: 3px;
        text-transform: uppercase;
        color: #4a9eff;
        margin-bottom: 10px;
    }

    .metric-value {
        font-family: 'Space Mono', monospace;
        font-size: 52px;
        font-weight: 700;
        color: #00d4ff;
        text-shadow: 0 0 20px rgba(0, 212, 255, 0.3);
        line-height: 1;
        margin-bottom: 6px;
    }

    .metric-sub {
        font-size: 13px;
        color: #5a7a9a;
        font-family: 'Space Mono', monospace;
    }

    .badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 11px;
        font-family: 'Space Mono', monospace;
        letter-spacing: 1px;
        text-transform: uppercase;
        font-weight: 700;
    }

    .badge-classical {
        background: rgba(0, 200, 100, 0.15);
        border: 1px solid #00c864;
        color: #00c864;
    }

    .badge-quantum {
        background: rgba(0, 180, 255, 0.15);
        border: 1px solid #00b4ff;
        color: #00b4ff;
    }

    .details-box {
        background: #050d1a;
        border: 1px solid #1a2a40;
        border-radius: 8px;
        padding: 16px 20px;
        font-family: 'Space Mono', monospace;
        font-size: 12px;
        color: #4a7a9a;
        line-height: 1.8;
    }

    .header-title {
        font-family: 'Space Mono', monospace;
        font-size: 28px;
        font-weight: 700;
        color: #ffffff;
        letter-spacing: -0.5px;
    }

    .header-sub {
        font-family: 'Inter', sans-serif;
        color: #3a6a9a;
        font-size: 14px;
        margin-top: 4px;
    }

    .quantum-pill {
        display: inline-block;
        background: linear-gradient(90deg, #0030ff22, #00d4ff22);
        border: 1px solid #00d4ff44;
        border-radius: 4px;
        padding: 2px 10px;
        font-family: 'Space Mono', monospace;
        font-size: 10px;
        color: #00d4ff;
        letter-spacing: 2px;
    }

    .stButton > button {
        background: linear-gradient(135deg, #0040c0, #0070ff);
        color: white;
        border: none;
        border-radius: 8px;
        font-family: 'Space Mono', monospace;
        font-weight: 700;
        font-size: 14px;
        letter-spacing: 1px;
        padding: 12px 28px;
        width: 100%;
        transition: all 0.2s;
        box-shadow: 0 4px 20px rgba(0, 100, 255, 0.3);
    }

    .stButton > button:hover {
        background: linear-gradient(135deg, #0050d0, #0080ff);
        box-shadow: 0 6px 28px rgba(0, 120, 255, 0.45);
        transform: translateY(-1px);
    }

    .stTextArea textarea {
        font-family: 'Space Mono', monospace !important;
        font-size: 12px !important;
        background: #050d1a !important;
        color: #4a9eff !important;
        border: 1px solid #1a3a5a !important;
    }

    div[data-testid="stSidebar"] {
        background: #060c18;
        border-right: 1px solid #0f1e33;
    }

    .error-box {
        background: rgba(255, 50, 50, 0.08);
        border: 1px solid #ff3232;
        border-radius: 8px;
        padding: 16px;
        font-family: 'Space Mono', monospace;
        font-size: 12px;
        color: #ff6060;
    }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------ #
# Sidebar — inputs
# ------------------------------------------------------------------ #
with st.sidebar:
    st.markdown('<div class="header-title">⚛️ Quantum<br/>Risk API</div>', unsafe_allow_html=True)
    st.markdown('<div class="header-sub">Hybrid classical-quantum financial risk</div>', unsafe_allow_html=True)
    st.markdown("---")

    # --- Method selector
    st.markdown("##### COMPUTATION METHOD")
    method = st.radio(
        label="method",
        options=["classical", "quantum"],
        format_func=lambda x: f"{'📊' if x=='classical' else '⚛️'} {x.capitalize()}",
        label_visibility="collapsed"
    )

    if method == "quantum":
        st.markdown('<div class="quantum-pill">QISKIT · AER SIMULATOR</div>', unsafe_allow_html=True)
        st.caption("Encodes returns as quantum amplitudes. Measurement probabilities estimate tail risk.")
    else:
        st.caption("Gaussian fit + Monte Carlo sampling of the return distribution.")

    st.markdown("---")

    # --- Metric
    st.markdown("##### RISK METRIC")
    metric = st.selectbox(
        label="metric",
        options=["VaR", "CVaR"],
        format_func=lambda x: f"{'📉' if x=='VaR' else '📊'} {x}  {'(Value at Risk)' if x=='VaR' else '(Conditional VaR)'}",
        label_visibility="collapsed"
    )

    # --- Confidence
    st.markdown("##### CONFIDENCE LEVEL")
    confidence = st.slider(
        label="confidence",
        min_value=0.50,
        max_value=0.999,
        value=0.95,
        step=0.005,
        format="%.3f",
        label_visibility="collapsed"
    )
    st.caption(f"α = {confidence:.1%}  →  tail = {(1-confidence):.1%}")

    # --- Simulations (classical only)
    if method == "classical":
        st.markdown("##### MONTE CARLO PATHS")
        num_simulations = st.select_slider(
            label="simulations",
            options=[1000, 5000, 10000, 50000, 100000],
            value=10000,
            label_visibility="collapsed"
        )
    else:
        num_simulations = 10000

    st.markdown("---")

    # --- Backend health check
    if st.button("🔗 Check API Health", use_container_width=True):
        try:
            r = requests.get(f"{API_BASE_URL}/health", timeout=3)
            if r.status_code == 200:
                st.success(f"✓ API online — v{r.json().get('version','?')}")
            else:
                st.error(f"API returned {r.status_code}")
        except Exception:
            st.error("Cannot reach API at localhost:8000")

# ------------------------------------------------------------------ #
# Main panel
# ------------------------------------------------------------------ #
col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    st.markdown("### PORTFOLIO INPUT")
    st.caption("Enter daily return observations, one per line (decimal format, e.g. -0.02 = −2%)")

    default_returns = """-0.021
0.013
-0.008
0.025
-0.032
0.011
-0.005
0.018
-0.027
0.009
0.004
-0.014
0.031
-0.006
0.022
-0.019
0.007
-0.011
0.016
-0.003"""

    raw_input = st.text_area(
        label="returns",
        value=default_returns,
        height=340,
        label_visibility="collapsed",
        placeholder="Enter returns, one per line..."
    )

    # Parse portfolio
    portfolio = []
    parse_error = None
    for i, line in enumerate(raw_input.strip().splitlines()):
        line = line.strip()
        if not line:
            continue
        try:
            portfolio.append(float(line))
        except ValueError:
            parse_error = f"Line {i+1}: '{line}' is not a valid number"
            break

    if parse_error:
        st.markdown(f'<div class="error-box">⚠ Parse error: {parse_error}</div>', unsafe_allow_html=True)
    else:
        st.caption(f"✓ {len(portfolio)} observations loaded   |   "
                   f"mean: {sum(portfolio)/len(portfolio):.4f}   |   "
                   f"min: {min(portfolio):.4f}   max: {max(portfolio):.4f}")

    # Load example button
    if st.button("↩ Load example portfolio", use_container_width=True):
        st.rerun()

with col_right:
    st.markdown("### RISK OUTPUT")

    run_disabled = bool(parse_error) or len(portfolio) < 2

    if st.button(
        f"{'📊' if method=='classical' else '⚛️'}  COMPUTE {metric}",
        disabled=run_disabled,
        use_container_width=True
    ):
        payload = {
            "portfolio": portfolio,
            "method": method,
            "metric": metric,
            "confidence": confidence,
            "num_simulations": num_simulations
        }

        with st.spinner(f"Running {'quantum circuit simulation' if method=='quantum' else 'Monte Carlo'}..."):
            t0 = time.time()
            try:
                response = requests.post(
                    RISK_ENDPOINT,
                    json=payload,
                    timeout=60
                )
                elapsed = time.time() - t0

                if response.status_code == 200:
                    data = response.json()
                    st.session_state["last_result"] = data
                    st.session_state["last_elapsed"] = elapsed
                else:
                    detail = response.json().get("detail", response.text)
                    st.session_state["last_error"] = f"API Error {response.status_code}: {detail}"
                    st.session_state.pop("last_result", None)

            except requests.exceptions.ConnectionError:
                st.session_state["last_error"] = (
                    "Could not connect to the backend at localhost:8000.\n"
                    "Start it with: uvicorn main:app --reload --port 8000"
                )
                st.session_state.pop("last_result", None)
            except Exception as e:
                st.session_state["last_error"] = str(e)
                st.session_state.pop("last_result", None)

    # ---- Display result
    if "last_result" in st.session_state:
        data = st.session_state["last_result"]
        elapsed = st.session_state.get("last_elapsed", 0)
        value = data["value"]
        badge_class = "badge-quantum" if data["method"] == "quantum" else "badge-classical"

        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{data['metric']} · {data['confidence']:.1%} confidence</div>
            <div class="metric-value">{value:.4f}</div>
            <div class="metric-sub">{value*100:.2f}% portfolio loss threshold</div>
            <br/>
            <span class="badge {badge_class}">{data['method']}</span>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"<div style='text-align:right; font-family:Space Mono; font-size:11px; color:#2a4a6a; margin-top:8px;'>computed in {elapsed:.2f}s</div>", unsafe_allow_html=True)

        # Interpretation
        st.markdown("---")
        if data["metric"] == "VaR":
            st.info(
                f"**Interpretation:** With {data['confidence']:.0%} confidence, "
                f"the maximum expected loss is **{value:.2%}** over one period. "
                f"There is a {(1-data['confidence']):.0%} chance of losing more than this."
            )
        else:
            st.info(
                f"**Interpretation:** Given that losses exceed the VaR threshold, "
                f"the expected loss (CVaR / Expected Shortfall) is **{value:.2%}**. "
                f"This is the average loss in the worst {(1-data['confidence']):.0%} of scenarios."
            )

        # Details expander
        with st.expander("🔬 Technical details"):
            st.markdown('<div class="details-box">', unsafe_allow_html=True)
            for k, v in data.get("details", {}).items():
                if isinstance(v, dict):
                    st.markdown(f"**{k}:**")
                    st.json(v)
                else:
                    st.markdown(f"**{k}:** `{v}`")
            st.markdown('</div>', unsafe_allow_html=True)

        # Raw JSON
        with st.expander("📋 Raw API response"):
            st.code(json.dumps(data, indent=2), language="json")

    elif "last_error" in st.session_state:
        st.markdown(f'<div class="error-box">❌ {st.session_state["last_error"]}</div>', unsafe_allow_html=True)

    else:
        # Placeholder before first run
        st.markdown("""
        <div class="metric-card" style="opacity:0.4;">
            <div class="metric-label">awaiting computation</div>
            <div class="metric-value" style="font-size:36px; color:#1a3a5a;">— —</div>
            <div class="metric-sub">configure inputs and click Compute</div>
        </div>
        """, unsafe_allow_html=True)

# ------------------------------------------------------------------ #
# Footer
# ------------------------------------------------------------------ #
st.markdown("---")
st.markdown(
    '<div style="text-align:center; font-family:Space Mono; font-size:11px; '
    'color:#1a3a5a; letter-spacing:2px;">QUANTUM RISK API · HYBRID CLASSICAL-QUANTUM · '
    'POWERED BY QISKIT + FASTAPI</div>',
    unsafe_allow_html=True
)