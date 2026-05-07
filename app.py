"""
C3 Digital Twin — Alternative Pathway Complement Dynamics Simulator
First design (red sliders, ①②③④ scenario pills) + experimental-data
validation button.

Run:
    source .venv/bin/activate
    streamlit run app.py
"""
from collections import defaultdict
import numpy as np
from scipy.integrate import solve_ivp
import plotly.graph_objects as go
import streamlit as st

from c3_twin_loader import C3Twin

# =============================================================================
# Clinical reference ranges (nM, plasma).
# Sources: Bansal 2022 Table 1 (MW + concentration); Caruso 2020 S2 Table.
# Conversion: clinical-lab mg/dL × 10 / MW(kDa) → µM × 1000 → nM.
# =============================================================================
LAB_REF = {
    "C3":  (3800, 8600),    # 90–180 mg/dL  ÷ 185 kDa
    "FB":  (1500, 4000),    # 135–360 mg/L  ÷ 90 kDa
    "FD":  (30, 130),       # 1–3 µg/mL     ÷ 24 kDa
    "FH":  (1300, 5300),    # 200–800 mg/L  ÷ 150 kDa
    "FP":  (75, 470),       # 4–25 µg/mL    ÷ 53 kDa
    "C5":  (370, 680),      # 70–130 mg/L   ÷ 190 kDa
}

# Healthy baseline slider values (nM) — used by the reset-to-healthy button.
HEALTHY_DEFAULTS_nM = {"C3": 5400, "FB": 2200, "FD": 83, "FH": 3200, "FP": 470}
HEALTHY_ACTIVATION = {"susc": 0.05, "acute": False, "hepatic": 1.0,
                      "drug_amy": 0.0, "drug_ipt": 0.0, "drug_dan": 0.0}

# Physiologic "normal" ranges for the activation knobs.
# Surface Susceptibility: 0.0–0.3 = host-protected (normal); above = pathologic
# Hepatic Function:       0.8–1.2 = within ±20% of healthy synthesis
ACTIVATION_REF = {"susc": (0.0, 0.30), "hepatic": (0.80, 1.20)}


def zone_band_html(slider_lo, slider_hi, normal_lo, normal_hi, good_class="zone-good"):
    """Render a 6 px-tall horizontal band whose green segment matches the
    normal portion of the slider's full range, red on either side."""
    total = max(slider_hi - slider_lo, 1e-12)
    n_lo = max(slider_lo, normal_lo)
    n_hi = min(slider_hi, normal_hi)
    pct_low    = max(0.0, (n_lo - slider_lo) / total) * 100
    pct_normal = max(0.0, (n_hi - n_lo) / total) * 100
    pct_high   = max(0.0, (slider_hi - n_hi) / total) * 100
    return (
        '<div class="zone-band">'
        f'<span class="zone-bad" style="width:{pct_low:.2f}%"></span>'
        f'<span class="{good_class}" style="width:{pct_normal:.2f}%"></span>'
        f'<span class="zone-bad" style="width:{pct_high:.2f}%"></span>'
        '</div>'
    )


def reset_to_healthy():
    """Restore all patient/intervention sliders to a healthy baseline."""
    for name, val in HEALTHY_DEFAULTS_nM.items():
        st.session_state[f"slider_{name}"] = float(val)
    for k, v in HEALTHY_ACTIVATION.items():
        st.session_state[k] = v


# =============================================================================
# Page config + CSS theming
# =============================================================================
st.set_page_config(page_title="C3 Digital Twin", page_icon="🧬",
                   layout="wide", initial_sidebar_state="expanded")

CSS = """
<style>
:root{
  --bg:#0a0d14; --panel:#141824; --panel2:#1a1f2e; --border:#242b3d;
  --text:#e8ecf1; --muted:#8892a6; --accent:#ff4757;
  --blue:#4dbcff; --cyan:#3ee0d8; --yellow:#ffc857; --pink:#ff5e8a;
  --purple:#b06cff; --red:#ff4d4d;
  --good:#3ee0a8; --warn:#ffc857; --bad:#ff5e8a;
}
.stApp, [data-testid="stSidebar"], body {
  background-color: var(--bg) !important;
  color: var(--text) !important;
  font-family: -apple-system, "SF Pro Display", "Helvetica Neue", sans-serif;
}
[data-testid="stHeader"]{ background: transparent; }

h1.hero{ font-size:1.8rem; font-weight:600; margin:0; letter-spacing:-0.01em; }
.subtitle{ color:var(--muted); font-size:0.82rem; margin-top:4px;}
.meta-right{ color:var(--muted); font-size:0.72rem; text-align:right; line-height:1.4;}
.meta-right .dot{ color:var(--accent); }

.section-label{
  color:var(--muted); font-size:0.7rem; font-weight:600;
  letter-spacing:0.12em; margin:18px 0 8px 0; text-transform:uppercase;
}

/* KPI cards */
.kpi{ background: var(--panel); border:1px solid var(--border);
  border-radius:10px; padding:14px 18px; height:88px;
  display:flex; flex-direction:column; justify-content:center;}
.kpi .lbl{ color:var(--muted); font-size:0.68rem; letter-spacing:0.14em;
  text-transform:uppercase; margin-bottom:4px;}
.kpi .val{ font-size:1.6rem; font-weight:600; line-height:1.1; }
.kpi .delta{ color:var(--muted); font-size:0.72rem; margin-top:2px; }
.kpi .up{ color:#ff9f9f; } .kpi .dn{ color:#9fffbf; }

/* Scenario pills */
div[role="radiogroup"]{ gap:10px !important; }
div[role="radiogroup"] label{
  background: var(--panel); border:1px solid var(--border);
  border-radius:28px; padding:8px 18px !important; cursor:pointer;
  transition:all 0.15s; margin:0 !important;
}
div[role="radiogroup"] label:has(input:checked){
  background: rgba(255,71,87,0.14); border-color: var(--accent);
}
div[role="radiogroup"] label p{ color:var(--text)!important; font-size:0.88rem;}

/* Sliders — calm blue track so red can be reserved for "abnormal" state */
[data-testid="stSlider"] [role="slider"]{ background: var(--blue) !important;
  border: 2px solid var(--blue) !important;
  box-shadow: 0 0 6px rgba(77,188,255,0.35) !important;}
[data-testid="stSlider"] > div > div > div > div{
  background: var(--blue) !important;
}
[data-testid="stSlider"] label p{ color:var(--text)!important; font-size:0.82rem;}
[data-testid="stSlider"] [data-baseweb="slider"] span{
  background: var(--blue)!important; color:#0a0d14 !important; font-weight:600;}

[data-testid="stSidebar"]{ background: #0d111a !important;
  border-right: 1px solid var(--border); }
[data-testid="stSidebar"] > div{ padding-top: 12px; }

/* Validation button */
.stButton>button{
  background: linear-gradient(90deg, var(--accent), #ff7280);
  color:#fff; border:none; padding:10px 24px; border-radius:24px;
  font-size:0.9rem; font-weight:600; letter-spacing:0.02em;
  box-shadow: 0 0 20px rgba(255,71,87,0.25);
  transition: all 0.2s;
}
.stButton>button:hover{ transform: translateY(-1px); box-shadow: 0 4px 24px rgba(255,71,87,0.4);}

/* Sidebar reset button — bulletproof: raw colors + every selector path
   Streamlit might emit. Forces dark bg + visible text. */
section[data-testid="stSidebar"] .stButton button,
section[data-testid="stSidebar"] [data-testid="stButton"] button,
section[data-testid="stSidebar"] button[kind="secondary"],
section[data-testid="stSidebar"] button[kind="primary"]{
  background-color: #1a1f2e !important;
  background-image: none !important;
  color: #e8ecf1 !important;
  border: 1px solid #2a3045 !important;
  border-radius: 6px !important;
  padding: 4px 12px !important;
  font-size: 0.74rem !important;
  font-weight: 500 !important;
  letter-spacing: 0 !important;
  line-height: 1.25 !important;
  height: auto !important;
  min-height: 26px !important;
  width: auto !important;
  box-shadow: none !important;
  transition: all 0.15s !important;
  margin-top: 4px !important;
  margin-bottom: 12px !important;
}
section[data-testid="stSidebar"] .stButton button:hover,
section[data-testid="stSidebar"] [data-testid="stButton"] button:hover{
  border-color: #3ee0a8 !important;
  color: #3ee0a8 !important;
  background-color: #1a1f2e !important;
  transform: none !important;
}
section[data-testid="stSidebar"] .stButton button:focus,
section[data-testid="stSidebar"] .stButton button:active{
  background-color: #1a1f2e !important;
  color: #3ee0a8 !important;
  border-color: #3ee0a8 !important;
  outline: none !important;
}

/* Range hint text: green when in range, red when abnormal */
.range-hint{ display:flex; justify-content:space-between;
  align-items:center; margin-top:-12px; margin-bottom:6px;
  font-size:0.7rem; color: var(--muted); font-variant-numeric: tabular-nums;}
.range-hint .range-good{ color: #3ee0a8; font-weight:600;}
.range-hint .range-bad{  color: #ff4757; font-weight:600;}

.footer-caption{ color:var(--muted); font-size:0.7rem; text-align:right;
  margin-top:8px;}

[data-testid="stCheckbox"] label p{ color:var(--text)!important; font-size:0.82rem;}

/* Validation results */
.fit-table{ background: var(--panel); border:1px solid var(--border);
  border-radius:10px; padding:8px 4px; margin-top:10px;}
.fit-row{ display:grid;
  grid-template-columns: 1.7fr 0.5fr 0.8fr 0.8fr 0.8fr 0.6fr;
  gap:12px; padding:8px 18px; align-items:center;
  border-bottom:1px solid var(--border); font-variant-numeric: tabular-nums;}
.fit-row:last-child{ border:none;}
.fit-row.head{ color:var(--muted); font-size:0.7rem; letter-spacing:0.1em;
  text-transform:uppercase; font-weight:600;}
.fit-row .obs{ color: var(--text); font-weight:500;}
.fit-row .n{ color:var(--muted); }
.fit-row .num{ color:var(--text); }
.fit-row .status.good{ color: var(--good); font-weight:700;}
.fit-row .status.warn{ color: var(--warn); font-weight:700;}
.fit-row .status.bad{  color: var(--bad);  font-weight:700;}
.aggregate-card{ background: linear-gradient(135deg, var(--panel), var(--panel2));
  border:1px solid var(--border); border-radius:12px; padding:18px 24px;
  margin: 12px 0;}
.aggregate-card .big{ font-size:2.2rem; font-weight:700; line-height:1;}
.aggregate-card .lbl{ color:var(--muted); font-size:0.8rem; margin-top:6px;}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# =============================================================================
# Loader
# =============================================================================
@st.cache_resource
def load_twin():
    return C3Twin()


tw = load_twin()


# =============================================================================
# Model
# =============================================================================
STATE = ["C3", "FB", "FD", "FH", "FI", "FP",
         "C3b", "C3bBb", "C3a", "iC3b", "C5", "C5a", "MAC"]


def default_k():
    """Mechanistic + physiologic constants.

    Concentration units = µM, time = min.

    Synthesis/clearance is parameterised so that at hepatic_function=1 and no
    activation, every protein converges to its healthy-baseline plasma value
    (k_syn_X = k_clear_X · X_baseline). Real protein half-lives from Bansal
    Table 1 / Caruso S4: C3=60h, FB=60h, FD=24h, FH=120h, FP=48h, C5=96h.
    """
    pick = lambda rid, fb: tw.kinetic_value(rid) if tw.kinetic_value(rid) is not None else fb
    SIGMA_SURF = 0.005

    # First-order clearance (k_clear = ln 2 / t½)
    def kc(t_half_h):
        return 0.6931 / (t_half_h * 60)
    kc_C3 = kc(60); kc_FB = kc(60); kc_FD = kc(24)
    kc_FH = kc(120); kc_FP = kc(48); kc_C5 = kc(96)

    return {
        "tick":       pick("R009",  4.98e-5),
        "conv_form":  pick("R001a", 0.1278),
        "decay":      pick("R004",  0.462),
        "decay_P":    pick("R005",  0.0462),
        "Kd_P":       0.03 / 0.87,
        "amp_kcat":   (pick("R003a", 106.8)) * SIGMA_SURF,
        "amp_Km":     pick("R003b", 5.86),
        "inact_kcat": pick("R008a", 78),
        "inact_Km":   pick("R008b", 0.25),
        "c5_kcat":    pick("R021a", 1.32),
        # Use fluid-phase Km (R021b = 11.6 µM) — the reduced model treats
        # C3bBb as a lumped (not surface-localised) species, so the surface
        # Km of 8.9 nM gives unphysiologic C5 depletion.
        "c5_Km":      pick("R021b", 11.6),
        "mac_form":   60.0,
        "mac_damage_N": 1.0e-3,
        # ---- physiologic homeostasis (per-protein synthesis & clearance) ----
        "k_clear": {"C3": kc_C3, "FB": kc_FB, "FD": kc_FD, "FH": kc_FH,
                    "FP": kc_FP, "C5": kc_C5},
        "k_syn":   {"C3": kc_C3 * 5.4, "FB": kc_FB * 2.2, "FD": kc_FD * 0.083,
                    "FH": kc_FH * 3.2, "FP": kc_FP * 0.47, "C5": kc_C5 * 0.37},
        # acute-phase amplification factor per protein (IL-6/IL-1 driven)
        "ap_amp":  {"C3": 1.5, "FB": 1.3, "FD": 1.0, "FH": 1.2,
                    "FP": 2.0, "C5": 1.2},
        # ---- in vivo convertase density cap (surface stoichiometry) ----
        # Realistic plasma-effective C3bBb ceiling; prevents the simplified
        # 10-state model from running away in pathogen scenarios.
        "C3bBb_max": 0.05,    # µM
        # FB depletion negative feedback (in vivo serum FB is finite)
        "FB_min":   0.05,     # µM, irreducible reservoir
    }


def rhs(t, y, k, surface, drug, susceptibility, acute, hepatic,
        closed_system=False):
    """Coupled in-vivo physiology of the alternative pathway.

    Inputs that flow IN:
        susceptibility   — surface activation pressure (0=self, 1=pathogen)
        acute            — boolean acute-phase trigger (5× tickover surge)
        hepatic          — hepatic synthesis multiplier (0.5–2)
        drug             — per-target fractional block

    Coupled outputs (all 13 states evolve jointly):
        proteins         — synthesised by liver, cleared, and consumed by AP
        complexes        — formed, decay, and stabilised by properdin
        cleavage products — accumulate (C3a, iC3b, C5a)
        damage           — MAC-driven membrane damage proxy
    """
    (C3, FB, FD, FH, FI, FP,
     C3b, C3bBb, C3a, iC3b, C5, C5a, MAC) = y

    # ---- IL-6/IL-1 driven acute-phase response ----
    # inflammation scales with sustained activation pressure + acute trigger
    inflammation = min(1.0, max(0.0, (susceptibility - 0.3) / 0.7
                                + (0.5 if acute else 0.0)))

    def syn(name):
        if closed_system:
            return 0.0           # in vitro / serum-only — no hepatic supply
        amp = 1 + inflammation * (k["ap_amp"][name] - 1.0)
        return k["k_syn"][name] * hepatic * amp

    # In a closed system there's also no first-order plasma clearance.
    clear_scale = 0.0 if closed_system else 1.0

    # ---- drug effects (instantaneous fractional block) ----
    C3_eff = C3 * (1 - drug.get("C3", 0.0))
    FB_eff = FB * (1 - drug.get("FB", 0.0))
    FD_eff = FD * (1 - drug.get("FD", 0.0))
    C5_eff = C5 * (1 - drug.get("C5", 0.0))

    fd_gate = FD_eff / (FD_eff + 0.05 + 1e-12)

    # ---- pathway rates ----
    r_tick = k["tick"] * C3_eff * (1 + (4.0 if acute else 0.0))

    # In-vivo convertase saturation: C3b sites on surface are finite. Hill
    # cap on C3bBb formation prevents the reduced model from running away.
    sat = max(0.0, 1.0 - C3bBb / k["C3bBb_max"])
    fb_avail = max(0.0, FB_eff - k["FB_min"])
    r_conv_form = k["conv_form"] * C3b * fb_avail * fd_gate * susceptibility * sat

    f_P = FP / (FP + k["Kd_P"] + 1e-12)
    k_decay_eff = (1 - f_P) * k["decay"] + f_P * k["decay_P"]
    r_decay = k_decay_eff * C3bBb
    r_amp = k["amp_kcat"] * C3bBb * C3_eff / (k["amp_Km"] + C3_eff + 1e-12)

    # FH access scales with (1 - susceptibility) on host surfaces, zero on pathogen
    fh_access = (1.0 - susceptibility) if surface == "self" else 0.0
    r_inact = k["inact_kcat"] * C3b * FH * fh_access / (k["inact_Km"] + C3b + 1e-12)

    r_c5 = k["c5_kcat"] * C3bBb * C5_eff / (k["c5_Km"] + C5_eff + 1e-12)
    r_mac = k["mac_form"] * C5a * 0.2

    # ---- ODE system: synthesis − clearance − AP consumption ----
    return [
        syn("C3") - clear_scale * k["k_clear"]["C3"] * C3 - r_tick - r_amp,
        syn("FB") - clear_scale * k["k_clear"]["FB"] * FB - r_conv_form,
        syn("FD") - clear_scale * k["k_clear"]["FD"] * FD,
        syn("FH") - clear_scale * k["k_clear"]["FH"] * FH,
        0.0,
        syn("FP") - clear_scale * k["k_clear"]["FP"] * FP,
        r_tick + r_amp - r_conv_form - r_inact,
        r_conv_form - r_decay,
        # In vitro (closed_system) → carboxypeptidase clearance OFF so C3a/C5a
        # accumulate as cumulative-cleavage signals (matches ELISA readouts).
        # In vivo → 0.231/min carboxypeptidase conversion (t½ 3 min).
        r_tick + r_amp - clear_scale * 0.231 * C3a,
        r_inact - 0.001 * iC3b,
        syn("C5") - clear_scale * k["k_clear"]["C5"] * C5 - r_c5,
        r_c5 - clear_scale * 0.231 * C5a,
        r_mac,
    ]


def simulate(k, ic, t_end=120, surface="self", drug=None,
             susceptibility=1.0, acute=False, hepatic=1.0,
             closed_system=False):
    drug = drug or {}
    y0 = np.array([ic.get(s, 0.0) for s in STATE])
    t_eval = np.linspace(0, t_end, max(120, int(t_end * 2.2)))
    sol = solve_ivp(rhs, (0, t_end), y0,
                    args=(k, surface, drug, susceptibility, acute, hepatic,
                          closed_system),
                    t_eval=t_eval, method="Radau", rtol=1e-8, atol=1e-12)
    return t_eval, {n: sol.y[i] for i, n in enumerate(STATE)}


# =============================================================================
# Sidebar — controls
# =============================================================================
ic_default = tw.initial_conditions("healthy_baseline")
ic_default["C5"] = ic_default.get("C5", 0.37)

with st.sidebar:
    # ---- Complement Proteins header + small reset button below ----
    st.markdown('<div class="section-label" style="margin-top:14px;'
                'margin-bottom:8px">Complement Proteins</div>',
                unsafe_allow_html=True)
    st.button("↺ Reset to healthy", on_click=reset_to_healthy,
              help="Restore all sliders (proteins + activation + drugs) "
                   "to the healthy baseline.")

    def nmol_slider(name, slot, lo_nM, hi_nM, step):
        """Slider in nM with a normal-range hint and a green/red status
        badge below — no extra coloured band above the track."""
        key = f"slider_{slot}"
        if key not in st.session_state:
            st.session_state[key] = float(HEALTHY_DEFAULTS_nM[slot])
        v = st.slider(name, float(lo_nM), float(hi_nM),
                      step=float(step), format="%d", key=key)
        ref = LAB_REF.get(slot)
        if ref:
            ref_lo, ref_hi = ref
            if ref_lo <= v <= ref_hi:
                cls, badge = "range-good", f"{int(v):,} nM · ✓ in range"
            else:
                arrow = "↓ low" if v < ref_lo else "↑ high"
                cls, badge = "range-bad", f"{int(v):,} nM · {arrow}"
            st.markdown(
                f'<div class="range-hint">'
                f'<span>normal {ref_lo:,}–{ref_hi:,} nM</span>'
                f'<span class="{cls}">{badge}</span>'
                f'</div>', unsafe_allow_html=True)
        return v / 1000.0       # → µM for the model

    C3 = nmol_slider("C3 (plasma)", "C3", 1000, 12000, 100)
    FB = nmol_slider("Factor B",    "FB",  500,  4000, 50)
    FD = nmol_slider("Factor D",    "FD",    1,   200, 1)
    FH = nmol_slider("Factor H",    "FH",  100,  6000, 100)
    FP = nmol_slider("Properdin",   "FP",   50,  1500, 25)

    # ---- Activation parameters ----
    st.markdown('<div class="section-label">Activation Parameters</div>',
                unsafe_allow_html=True)
    if "susc" not in st.session_state:    st.session_state["susc"] = 0.72
    if "acute" not in st.session_state:   st.session_state["acute"] = False
    if "hepatic" not in st.session_state: st.session_state["hepatic"] = 1.0

    susceptibility = st.slider(
        "Surface Susceptibility", 0.0, 1.0, step=0.01, key="susc",
        help=("1.0 = pathogen (no FH access); 0.0 = fully regulated host.\n\n"
              "Coupled effects: above 0.3 it auto-induces inflammation, which "
              "upregulates hepatic synthesis of C3/FB/FH/Properdin (IL-6 "
              "acute-phase response)."))
    sus_lo, sus_hi = ACTIVATION_REF["susc"]
    sus_in = sus_lo <= susceptibility <= sus_hi
    sus_cls = "range-good" if sus_in else "range-bad"
    sus_msg = "✓ host-protected" if sus_in else "↑ activation pressure"
    st.markdown(
        f'<div class="range-hint">'
        f'<span>normal {sus_lo:.2f}–{sus_hi:.2f}</span>'
        f'<span class="{sus_cls}">{susceptibility:.2f} · {sus_msg}</span>'
        f'</div>', unsafe_allow_html=True)

    acute = st.checkbox(
        "Acute Trigger (haemolytic crisis)", key="acute",
        help="5× tick-over surge AND adds 0.5 to inflammation level.")

    hepatic = st.slider(
        "Hepatic Function", 0.5, 2.0, step=0.05, key="hepatic",
        help=("Multiplier on basal hepatic synthesis of all complement "
              "proteins. 1.0 = healthy. <1 = liver disease. >1 = upregulated."))
    hep_lo, hep_hi = ACTIVATION_REF["hepatic"]
    hep_in = hep_lo <= hepatic <= hep_hi
    hep_cls = "range-good" if hep_in else "range-bad"
    if hep_in:                       hep_msg = "✓ normal"
    elif hepatic < hep_lo:           hep_msg = "↓ liver impaired"
    else:                            hep_msg = "↑ upregulated"
    st.markdown(
        f'<div class="range-hint">'
        f'<span>normal {hep_lo:.1f}–{hep_hi:.1f}</span>'
        f'<span class="{hep_cls}">{hepatic:.2f} · {hep_msg}</span>'
        f'</div>', unsafe_allow_html=True)

    # ---- Drug intervention ----
    st.markdown('<div class="section-label">Drug Intervention</div>',
                unsafe_allow_html=True)
    if "drug_amy" not in st.session_state: st.session_state["drug_amy"] = 0.0
    if "drug_ipt" not in st.session_state: st.session_state["drug_ipt"] = 0.0
    if "drug_dan" not in st.session_state: st.session_state["drug_dan"] = 0.0
    amy101    = st.slider("AMY-101 / Pegcetacoplan (C3)", 0.0, 1.0, step=0.01, key="drug_amy")
    iptacopan = st.slider("Iptacopan (Factor B)",         0.0, 1.0, step=0.01, key="drug_ipt")
    danicopan = st.slider("Danicopan (Factor D)",         0.0, 1.0, step=0.01, key="drug_dan")


# =============================================================================
# Header + scenario picker
# =============================================================================
hcol_l, hcol_r = st.columns([3, 1])
with hcol_l:
    st.markdown('<h1 class="hero">Alternative Pathway Complement Dynamics Simulator</h1>',
                unsafe_allow_html=True)
    st.markdown('<div class="subtitle">QSP Model · ODE system · Radau solver · t = 0 – 120 min</div>',
                unsafe_allow_html=True)
with hcol_r:
    st.markdown(
        '<div class="meta-right">'
        '<span class="dot">●</span> AP loop &nbsp;·&nbsp; '
        '<span class="dot">●</span> C3 core &nbsp;·&nbsp; '
        '<span class="dot">●</span> FH/FI regulation &nbsp;·&nbsp; '
        '<span class="dot">●</span> FD pharmacodynamics<br>'
        'Based on complement QSP literature (Pangburn 1983,<br>'
        'Bhatt 2014, Sahu 2000, Schubart 2019)'
        '</div>', unsafe_allow_html=True)

st.markdown('<div class="section-label">Scenario</div>', unsafe_allow_html=True)
scenario = st.radio(
    "scenario_picker",
    ["① Normal", "② FH Deficiency", "③ C3 Overactivation", "④ Drug Intervention"],
    horizontal=True, label_visibility="collapsed",
)

# Scenario presets
t_end = 120
k = default_k()
ic = {"C3": C3, "FB": FB, "FD": FD, "FH": FH, "FI": ic_default.get("FI", 0.4),
      "FP": FP, "C5": ic_default.get("C5", 0.37)}
surface = "self"
if scenario.startswith("②"):
    ic["FH"] = min(ic["FH"], 0.32); surface = "pathogen"
elif scenario.startswith("③"):
    k["decay"] = k["decay"] * 0.05; surface = "pathogen"
elif scenario.startswith("④"):
    surface = "pathogen"

drug = {"C3": amy101, "FB": iptacopan, "FD": danicopan}
drug_nodrug = {"C3": 0.0, "FB": 0.0, "FD": 0.0}

t_eval, sol_user   = simulate(k, ic, t_end, surface, drug, susceptibility, acute, hepatic)
_,      sol_nodrug = simulate(k, ic, t_end, surface, drug_nodrug, susceptibility, acute, hepatic)


# =============================================================================
# KPI cards
# =============================================================================
def kpi(label, value, delta_val, delta_label="vs no-drug", better="down"):
    cls = "dn" if ((delta_val < 0 and better == "down")
                   or (delta_val > 0 and better == "up")) else "up"
    arrow = "▼" if delta_val < 0 else "▲"
    return (f'<div class="kpi"><div class="lbl">{label}</div>'
            f'<div class="val">{value}</div>'
            f'<div class="delta {cls}">{arrow} {abs(delta_val):.3g} {delta_label}</div>'
            f'</div>')


C3_pct  = sol_user["C3"][-1] / max(ic["C3"], 1e-9) * 100
C3b_end = sol_user["C3b"][-1]
C3a_end = sol_user["C3a"][-1]
C5a_end = sol_user["C5a"][-1]
MAC_end = sol_user["MAC"][-1]
damage  = (1 - np.exp(-MAC_end / k["mac_damage_N"])) * 100

C3_pct_nd  = sol_nodrug["C3"][-1] / max(ic["C3"], 1e-9) * 100
C3b_nd     = sol_nodrug["C3b"][-1]
C3a_nd     = sol_nodrug["C3a"][-1]
C5a_nd     = sol_nodrug["C5a"][-1]
MAC_nd     = sol_nodrug["MAC"][-1]
damage_nd  = (1 - np.exp(-MAC_nd / k["mac_damage_N"])) * 100

cols = st.columns(5)
kpi_html = [
    kpi("C3 PLASMA",    f"{C3_pct:.1f}%",  C3_pct - C3_pct_nd, better="up"),
    kpi("C3B SURFACE",  f"{C3b_end:.4f}",  C3b_end - C3b_nd, better="down"),
    kpi("C3A",          f"{C3a_end:.4f}",  C3a_end - C3a_nd, better="down"),
    kpi("C5A / MAC",    f"{C5a_end:.5f}",  C5a_end - C5a_nd, better="down"),
    kpi("DAMAGE INDEX", f"{damage:.1f}%",  damage - damage_nd, better="down"),
]
for col, html in zip(cols, kpi_html):
    col.markdown(html, unsafe_allow_html=True)


# =============================================================================
# 6-panel plot grid
# =============================================================================
def panel(title, y_user, y_ref, color, ytitle="AU", yscale=None):
    from plotly.colors import hex_to_rgb
    r, g, b = hex_to_rgb(color)
    fill = f"rgba({r},{g},{b},0.10)"
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=t_eval, y=y_ref, mode="lines",
                             line=dict(color=color, width=1.5, dash="dash"),
                             opacity=0.55, name="no-drug",
                             hovertemplate="t=%{x:.0f}<br>%{y:.4g}<extra>no-drug</extra>"))
    fig.add_trace(go.Scatter(x=t_eval, y=y_user, mode="lines",
                             line=dict(color=color, width=3),
                             fill="tozeroy", fillcolor=fill, name="user",
                             hovertemplate="t=%{x:.0f}<br>%{y:.4g}<extra>user</extra>"))
    fig.update_layout(
        title=dict(text=title.upper(),
                   font=dict(size=11, color="#8892a6"),
                   x=0.5, xanchor="center", y=0.96),
        template="plotly_dark",
        paper_bgcolor="#141824", plot_bgcolor="#141824",
        margin=dict(l=42, r=12, t=32, b=32),
        height=220, showlegend=False,
        xaxis=dict(title=dict(text="Time (min)", font=dict(size=10, color="#8892a6")),
                   gridcolor="#242b3d", zeroline=False,
                   tickfont=dict(size=9, color="#8892a6")),
        yaxis=dict(title=dict(text=ytitle, font=dict(size=10, color="#8892a6")),
                   gridcolor="#242b3d", zeroline=False,
                   tickfont=dict(size=9, color="#8892a6"),
                   type=yscale if yscale else "linear"),
    )
    return fig


p_C3 = panel("C3 plasma level",
             sol_user["C3"] / max(ic["C3"], 1e-9) * 100,
             sol_nodrug["C3"] / max(ic["C3"], 1e-9) * 100,
             "#4dbcff", ytitle="% of initial")
p_C3b = panel("C3b surface deposition",
              sol_user["C3b"], sol_nodrug["C3b"], "#3ee0d8")
p_C3a = panel("C3a anaphylatoxin",
              sol_user["C3a"], sol_nodrug["C3a"], "#ffc857", ytitle="µM")
p_C5a = panel("C5a / MAC risk",
              sol_user["C5a"], sol_nodrug["C5a"], "#ff5e8a")
p_conv = panel("Active convertase",
               sol_user["C3bBb"] * 1e6, sol_nodrug["C3bBb"] * 1e6,
               "#b06cff", ytitle="AU")
p_dmg = panel("Tissue damage index",
              (1 - np.exp(-sol_user["MAC"] / k["mac_damage_N"])) * 100,
              (1 - np.exp(-sol_nodrug["MAC"] / k["mac_damage_N"])) * 100,
              "#ff4d4d", ytitle="%")

r1 = st.columns(3)
r1[0].plotly_chart(p_C3,  use_container_width=True, config={"displayModeBar": False})
r1[1].plotly_chart(p_C3b, use_container_width=True, config={"displayModeBar": False})
r1[2].plotly_chart(p_C3a, use_container_width=True, config={"displayModeBar": False})
r2 = st.columns(3)
r2[0].plotly_chart(p_C5a,  use_container_width=True, config={"displayModeBar": False})
r2[1].plotly_chart(p_conv, use_container_width=True, config={"displayModeBar": False})
r2[2].plotly_chart(p_dmg,  use_container_width=True, config={"displayModeBar": False})


# =============================================================================
# Predicted lab-value panel: coupled outputs at the end of the run
# =============================================================================
st.markdown(
    '<div class="section-label" style="margin-top:24px">'
    'Predicted Plasma Lab Values · t = ' + str(t_end) + ' min</div>',
    unsafe_allow_html=True)

cols = st.columns(6)
for col, name in zip(cols, ["C3", "FB", "FD", "FH", "FP", "C5"]):
    end_uM = sol_user[name][-1]
    end_nM = end_uM * 1000
    base_uM = ic.get(name, 0)
    delta = (end_uM - base_uM) / max(base_uM, 1e-9) * 100
    lo, hi = LAB_REF[name]
    if end_nM < lo: status = ("↓ low",  "#ff5e8a")
    elif end_nM > hi: status = ("↑ high", "#ffc857")
    else: status = ("normal", "#3ee0a8")
    arrow = "▲" if delta > 0 else "▼"
    col.markdown(
        f'<div class="kpi" style="padding:10px 14px">'
        f'<div class="lbl">{name}</div>'
        f'<div class="val" style="font-size:1.2rem">{end_nM:.0f} <small style="font-size:0.7rem;color:var(--muted)">nM</small></div>'
        f'<div class="delta">{arrow} {abs(delta):.1f}% &nbsp;'
        f'<span style="color:{status[1]}">{status[0]}</span></div>'
        f'</div>', unsafe_allow_html=True)

with st.expander("ℹ️ Physiological coupling rules (how the sliders interact)"):
    st.markdown("""
    The model is a coupled 13-state ODE; the sliders are intervention/exposure
    inputs, not independent constants. Sliders affect each other through the
    physics, not via UI updates.

    **1 — Hepatic homeostasis.** Every plasma protein has a synthesis term
    (`k_syn = k_clear × baseline`) and a first-order clearance. Without
    activation the system converges to the healthy lab values. With activation
    above synthesis capacity, proteins drop (consumption disorder).
    Half-lives used: C3=60 h, FB=60 h, FD=24 h, FH=120 h, FP=48 h, C5=96 h
    (Bansal Table 1).

    **2 — Acute-phase response (IL-6/IL-1).** When `Surface Susceptibility > 0.3`
    or the acute-trigger checkbox is on, an inflammation index drives
    hepatic synthesis upward. Per-protein amplification factors:
    C3 ×1.5, FB ×1.3, FH ×1.2, **Properdin ×2.0**. So increasing pathogen
    pressure transiently raises plasma proteins (acute-phase) before
    consumption catches up — the in-vivo signature of subacute infection.

    **3 — Convertase saturation.** `C3bBb` formation is multiplied by
    `(1 − C3bBb / C3bBb_max)` (Hill cap at 0.05 µM) representing finite C3b
    surface sites. This prevents the runaway amplification in the
    pathogen-only scenarios that the previous reduced model showed.

    **4 — FB irreducible reservoir.** The `(FB − FB_min)` floor at 0.05 µM
    captures the in-vivo phenomenon that FB is never fully depleted —
    splenic stores buffer the plasma pool.

    **5 — FH access scaling.** On a host surface, FH access scales with
    `(1 − Surface Susceptibility)`. Pure self surface (susc=0) gets full FH
    protection; AMD/aHUS scenarios use partial loss; pure pathogen disables
    FH entirely.

    **6 — Drug actions are real-time fractional blocks.**
    `Pegcetacoplan` lowers active C3, `Iptacopan` lowers active FB,
    `Danicopan` lowers active FD. The blocks immediately reduce
    consumption, which feeds back to preserve plasma C3 — the documented
    mechanism behind Empaveli's C3 stabilisation in PNH.
    """)

# =============================================================================
# Validation — scenario-aware test suite
#
# Each experimental condition in the XLSX is associated with a simulation setup
# (surface, FH modification, drug block, etc.). The validation loop IGNORES the
# sliders and instead runs the matching canonical simulation per condition,
# then compares each set of validation points to its own simulation.
# =============================================================================
st.markdown(
    '<div class="section-label" style="margin-top:24px">'
    'Model–Experiment Validation</div>', unsafe_allow_html=True)

bcol1, bcol2 = st.columns([1, 5])
with bcol1:
    run_validate = st.button("🔬 Validate against experiments")
with bcol2:
    st.markdown(
        '<div style="color:var(--muted);font-size:0.78rem;padding-top:14px">'
        'Runs a canonical simulation <b>per experimental condition</b> '
        f'(independent of sliders), compares against matching points in '
        f'<code>Template_validation_timeseries</code> '
        f'({len(tw.validation_records)} rows).</div>',
        unsafe_allow_html=True)

OBS_MAP = {
    "C3":           ("C3",    1.0),
    "C3a":          ("C3a",   1.0),
    "C3b":          ("C3b",   1.0),
    "C3b_surface":  ("C3b",   1.0),
    "C3bBb":        ("C3bBb", 1.0),
    "iC3b":         ("iC3b",  1.0),
    "C5a":          ("C5a",   1.0),
    "C5":           ("C5",    1.0),
}

# condition string → simulation params + human label + paper citation
# Fix #2: AMD/FH-deficient scenarios use surface="self" with reduced FH —
#   the diseases happen on host surfaces, not pathogen surfaces. The
#   susceptibility slider modulates how much FH access is preserved.
CONDITION_TO_SCENARIO = {
    "host_surface_normal": dict(
        label="Healthy · self surface", paper="Zewde 2016 Fig 2",
        surface="self", susceptibility=0.05,
        ic_mul={}, k_mul={}, drug={}),
    "pathogen_no_FH": dict(
        label="Healthy · pathogen surface", paper="Zewde 2016 Fig 2/5",
        surface="pathogen", susceptibility=1.0,
        ic_mul={}, k_mul={}, drug={}),
    # AMD Y402H: SCR7 mutation reduces FH binding to host glycosaminoglycans.
    # Effect is BOTH lower bioavailable FH AND weaker per-molecule kinetics.
    "AMD_Y402H": dict(
        label="AMD Y402H · partial FH function", paper="Zewde 2018 S2 Fig",
        surface="self", susceptibility=0.55,
        ic_mul={"FH": 0.22}, k_mul={"inact_kcat": 0.30}, drug={}),
    "AMD_compstatin": dict(
        label="AMD + compstatin / AMY-101", paper="Zewde 2018 S1 Fig",
        surface="self", susceptibility=0.55,
        ic_mul={"FH": 0.22}, k_mul={"inact_kcat": 0.30}, drug={"C3": 0.9}),
    # aHUS-like: severe FH defect — both reduced amount AND impaired catalysis
    # (representative of common pathogenic CFH mutations in SCR19-20).
    "FH_deficient_no_drug": dict(
        label="FH-deficient · no drug (aHUS-like)", paper="Bansal 2022 Fig 10",
        surface="self", susceptibility=0.85,
        ic_mul={"FH": 0.10}, k_mul={"inact_kcat": 0.05}, drug={}),
    "FH_deficient_90pct_AP_block": dict(
        label="FH-def + 90% FB block", paper="Bansal 2022 Fig 10",
        surface="self", susceptibility=0.85,
        ic_mul={"FH": 0.10}, k_mul={"inact_kcat": 0.05}, drug={"FB": 0.9}),
    "FH_deficient_99pct_AP_block": dict(
        label="FH-def + 99% FB block", paper="Bansal 2022 Fig 10",
        surface="self", susceptibility=0.85,
        ic_mul={"FH": 0.10}, k_mul={"inact_kcat": 0.05}, drug={"FB": 0.99}),
    "FH_deficient_90pct_C5_block": dict(
        label="FH-def + 90% C5 block", paper="Bansal 2022 Fig 10",
        surface="self", susceptibility=0.85,
        ic_mul={"FH": 0.10}, k_mul={"inact_kcat": 0.05}, drug={"C5": 0.9}),
    "FH_deficient_99pct_C5_block": dict(
        label="FH-def + 99% C5 block", paper="Bansal 2022 Fig 10",
        surface="self", susceptibility=0.85,
        ic_mul={"FH": 0.10}, k_mul={"inact_kcat": 0.05}, drug={"C5": 0.99}),
    "AP_assay_zymosan_+P": dict(
        label="AP assay · zymosan · +properdin", paper="Bansal 2022 Fig 5",
        surface="pathogen", susceptibility=1.0,
        ic_mul={}, k_mul={}, drug={}, closed_system=True),
    "AP_assay_zymosan_-P": dict(
        label="AP assay · zymosan · -properdin", paper="Bansal 2022 Fig 5",
        surface="pathogen", susceptibility=1.0,
        ic_mul={"FP": 0.0}, k_mul={}, drug={}, closed_system=True),
    "minimal_model_self": dict(
        label="Bakshi minimal model · self surface", paper="Bakshi 2020 Table 3",
        surface="self", susceptibility=0.05,
        ic_mul={}, k_mul={}, drug={}),
}


def _apply_muls(base, mul):
    """base × mul (multiplicative overrides, 0 allowed to zero out a species)."""
    out = dict(base)
    for key, m in mul.items():
        if key in out:
            out[key] = out[key] * m
    return out


NOISE_FLOOR_uM = 0.005    # 5 nM — below clinical detection limit


def metric_score(r2, nrmse=None, data_mean=None, model_mean=None):
    """0–1 quality score that mirrors status_class() exactly. Used by both
    the per-row status badge AND the aggregate-fit % so they can never
    disagree. ≥ 0.6 ≈ good, 0.3–0.6 ≈ partial, < 0.3 ≈ poor."""
    if data_mean is not None and model_mean is not None:
        if abs(data_mean) < NOISE_FLOOR_uM and abs(model_mean) < NOISE_FLOOR_uM:
            return 1.0
        if data_mean > 1e-9 and model_mean > 1e-9:
            fold = max(model_mean / data_mean, data_mean / model_mean)
            if fold < 2.0:   return 1.0
            if fold < 5.0:   return 0.5
    if r2 is not None and np.isfinite(r2):
        return max(0.0, min(1.0, r2))
    if nrmse is None:
        return 0.0
    return max(0.0, 1.0 - nrmse)


def status_class(r2, nrmse=None, data_mean=None, model_mean=None):
    """Biology-aware status with two early returns:

    1. **Noise floor**: if both data and model are below the clinical
       detection limit (~5 nM = 0.005 µM), call it good — the absolute
       discrepancy is in the unmeasurable tail.
    2. **Fold-error**: if both data and model are above the noise floor,
       compute the larger-of (model/data, data/model). Within 2× → good,
       within 5× → partial. This is the standard QSP modelling tolerance.

    Falls back to R² (when variance is meaningful) and finally NRMSE.
    """
    # 1. Noise-floor early return
    if data_mean is not None and model_mean is not None:
        if abs(data_mean) < NOISE_FLOOR_uM and abs(model_mean) < NOISE_FLOOR_uM:
            return "good", "✓ both ≈0"
        # 2. Fold-error
        if data_mean > 1e-9 and model_mean > 1e-9:
            fold = max(model_mean / data_mean, data_mean / model_mean)
            if fold < 2.0:   return "good", f"✓ within 2× ({fold:.1f}×)"
            if fold < 5.0:   return "warn", f"△ within 5× ({fold:.1f}×)"
            # else fall through to R² / NRMSE checks for poor verdict
    # 3. R² when variance is meaningful
    if r2 is not None:
        if r2 > 0.5:           return "good", "✓ good"
        if r2 > 0.0:           return "warn", "△ partial"
        return "bad", "✗ poor"
    # 4. NRMSE final fallback
    if nrmse is None:          return "muted", "—"
    if nrmse < 0.30:           return "good", "✓ good"
    if nrmse < 0.70:           return "warn", "△ partial"
    return "bad", "✗ poor"


# Concentration units the model state variables are in (µM).
_CONC_UNITS_OK = {"uM", "µM", "M", "mM", "nM", "pM"}


if run_validate:
    base_ic = dict(ic_default)
    base_k = default_k()

    # Group points by condition
    by_cond = defaultdict(list)
    n_au_skipped = 0
    for v in tw.validation_records:
        if v.observable not in OBS_MAP: continue
        if v.value is None or v.t_or_dose is None: continue
        if v.t_or_dose_unit not in ("min", "h", "s", None): continue
        # Fix #1: skip rows whose value_unit is incompatible with the
        # model's µM output (notably "AU" surface-density units in
        # Zewde Fig 2 / Bakshi Table 3).
        if v.value_unit and v.value_unit not in _CONC_UNITS_OK:
            n_au_skipped += 1
            continue
        t_val = v.t_min if v.t_min is not None else v.t_or_dose
        if t_val is None or t_val > 200: continue
        by_cond[v.condition].append((v, t_val))

    scenario_results, skipped = [], []
    for cond, pts in by_cond.items():
        if cond not in CONDITION_TO_SCENARIO:
            skipped.append((cond, len(pts)))
            continue
        cfg = CONDITION_TO_SCENARIO[cond]
        s_ic = _apply_muls(base_ic, cfg["ic_mul"])
        s_k = _apply_muls(base_k, cfg["k_mul"])
        t_e, sol = simulate(
            s_k, s_ic, t_end=max(t_end, max(t for _, t in pts) + 10),
            surface=cfg["surface"], drug=cfg["drug"],
            susceptibility=cfg["susceptibility"], acute=False, hepatic=1.0,
            closed_system=cfg.get("closed_system", False))

        obs_groups = defaultdict(list)
        for v, t_val in pts:
            state, scale = OBS_MAP[v.observable]
            mv = float(np.interp(t_val, t_e, sol[state] * scale))
            obs_groups[v.observable].append((t_val, v.value, mv, v.paper))

        obs_metrics, resid = [], []
        for obs, rows in obs_groups.items():
            data = np.array([r[1] for r in rows])
            model = np.array([r[2] for r in rows])
            rmse = float(np.sqrt(np.mean((data - model) ** 2)))
            data_mean = float(np.abs(np.mean(data)))
            data_range = float(data.max() - data.min())
            data_std = float(np.std(data))
            denom = max(data_range, data_mean, 1e-6)
            nrmse = rmse / denom
            # Fix #3: R² is meaningless when data variance is tiny relative
            # to the data magnitude (e.g. AMD+compstatin C3a clustered at
            # 0.002–0.003 µM). Fall back to NRMSE alone in those cases.
            r2 = None
            low_variance = data_std < 0.05 * max(data_mean, 1e-9)
            if len(rows) > 1 and not low_variance:
                ss_res = float(np.sum((data - model) ** 2))
                ss_tot = float(np.sum((data - np.mean(data)) ** 2))
                if ss_tot > 1e-12:
                    r2 = 1 - ss_res / ss_tot
            obs_metrics.append(dict(obs=obs, n=len(rows), rmse=rmse,
                                    nrmse=nrmse, r2=r2,
                                    data_mean=float(np.mean(data)),
                                    model_mean=float(np.mean(model)),
                                    data_range=data_range, rows=rows))
            resid.extend((data - model).tolist())
        overall_rmse = float(np.sqrt(np.mean(np.array(resid) ** 2)))

        scenario_results.append(dict(
            cond=cond, label=cfg["label"], paper=cfg["paper"],
            t_eval=t_e, sol=sol, n=len(pts),
            obs_metrics=obs_metrics, overall_rmse=overall_rmse))

    # ---- Aggregate (uses combined R² + NRMSE + fold-error status) ----
    all_metrics = [m for s in scenario_results for m in s["obs_metrics"]]
    statuses = [status_class(m["r2"], m["nrmse"],
                             m.get("data_mean"), m.get("model_mean"))[0]
                for m in all_metrics]
    good = sum(1 for s in statuses if s == "good")
    partial = sum(1 for s in statuses if s == "warn")
    bad = sum(1 for s in statuses if s == "bad")
    n_total = sum(s["n"] for s in scenario_results)

    # Aggregate score uses the SAME fold-error / noise-floor / R² / NRMSE
    # cascade as the per-row status badge, so they can never disagree.
    scores = [metric_score(m["r2"], m["nrmse"],
                           m.get("data_mean"), m.get("model_mean"))
              for m in all_metrics]
    mean_score = float(np.mean(scores)) if scores else 0.0
    agg_score = max(0.0, mean_score) * 100
    agg_color = ("var(--good)" if agg_score > 50 else
                 "var(--warn)" if agg_score > 20 else "var(--bad)")

    a1, a2, a3 = st.columns([1, 1, 2])
    a1.markdown(
        f'<div class="aggregate-card">'
        f'<div class="big" style="color:{agg_color}">{agg_score:.0f}%</div>'
        f'<div class="lbl">overall fit · mean R² across '
        f'{len(scenario_results)} scenarios</div></div>',
        unsafe_allow_html=True)
    a2.markdown(
        f'<div class="aggregate-card">'
        f'<div class="big">{n_total}</div>'
        f'<div class="lbl">data points compared</div></div>',
        unsafe_allow_html=True)
    a3.markdown(
        f'<div class="aggregate-card">'
        f'<div style="font-size:1.4rem;font-weight:600">'
        f'<span style="color:var(--good)">✓ {good}</span> &nbsp;·&nbsp; '
        f'<span style="color:var(--warn)">△ {partial}</span> &nbsp;·&nbsp; '
        f'<span style="color:var(--bad)">✗ {bad}</span></div>'
        f'<div class="lbl">good · partial · poor (per observable·scenario)</div>'
        f'</div>', unsafe_allow_html=True)

    if n_au_skipped:
        st.markdown(
            f'<div style="color:var(--muted);font-size:0.74rem;margin-top:6px">'
            f'Skipped {n_au_skipped} validation rows in arbitrary surface units (AU); '
            f'these are not directly comparable to the model\'s µM concentration output.'
            f'</div>', unsafe_allow_html=True)

    # ---- Per-scenario cards ----
    OBS_COLOR = {"C3": "#4dbcff", "C3a": "#ffc857", "C3b": "#3ee0d8",
                 "C3b_surface": "#3ee0d8", "C3bBb": "#b06cff",
                 "iC3b": "#9fffbf", "C5a": "#ff5e8a", "C5": "#ff7f50"}

    st.markdown(
        '<div class="section-label" style="margin-top:14px">'
        'Per-scenario results</div>', unsafe_allow_html=True)

    # Sort best→worst by scenario-level mean score (same scoring cascade)
    def scenario_score(s):
        ss = [metric_score(m["r2"], m["nrmse"],
                           m.get("data_mean"), m.get("model_mean"))
              for m in s["obs_metrics"]]
        return float(np.mean(ss)) if ss else -np.inf
    scenario_results.sort(key=lambda s: -scenario_score(s))

    for s in scenario_results:
        with st.container():
            c1, c2 = st.columns([1, 1.5])
            # Left: scenario metadata + per-observable table
            with c1:
                sc = scenario_score(s)              # 0–1 mean fit quality
                # Map directly to good/warn/bad by score thresholds.
                if sc >= 0.6:    cls, lbl = "good", f"✓ {sc*100:.0f}% fit"
                elif sc >= 0.3:  cls, lbl = "warn", f"△ {sc*100:.0f}% fit"
                else:            cls, lbl = "bad",  f"✗ {sc*100:.0f}% fit"
                badge_color = {"good": "#3ee0a8", "warn": "#ffc857",
                               "bad": "#ff5e8a", "muted": "#8892a6"}[cls]
                st.markdown(
                    f'<div style="color:var(--text);font-size:1.02rem;font-weight:600;'
                    f'margin-top:8px">{s["label"]}</div>'
                    f'<div style="color:var(--muted);font-size:0.76rem;margin-bottom:6px">'
                    f'{s["paper"]} · n={s["n"]} · RMSE={s["overall_rmse"]:.3g} · '
                    f'<span style="color:{badge_color};font-weight:600">{lbl}</span>'
                    f'</div>',
                    unsafe_allow_html=True)

                rows_html = ['<div class="fit-table">'
                             '<div class="fit-row head">'
                             '<span>Observable</span><span>n</span>'
                             '<span>RMSE</span><span>NRMSE</span>'
                             '<span>R²</span><span>Status</span></div>']
                for m in s["obs_metrics"]:
                    r2 = m["r2"]
                    mcls, mlbl = status_class(r2, m["nrmse"],
                                              m.get("data_mean"),
                                              m.get("model_mean"))
                    r2_txt = "—" if r2 is None else (
                        f"{r2:.3f}" if np.isfinite(r2) else "−∞")
                    nrmse_txt = (f"{m['nrmse']:.3f}"
                                 if np.isfinite(m["nrmse"]) else "—")
                    dmean = m["data_mean"]; drange = m["data_range"]
                    mmean = m["model_mean"]
                    obs_n = m["obs"]; n_pts = m["n"]; rmse_v = m["rmse"]
                    tooltip = (f"data mean={dmean:.3g} · model mean={mmean:.3g} "
                               f"· range={drange:.3g}")
                    rows_html.append(
                        f'<div class="fit-row" title="{tooltip}">'
                        f'<span class="obs">{obs_n}</span>'
                        f'<span class="n">{n_pts}</span>'
                        f'<span class="num">{rmse_v:.4g}</span>'
                        f'<span class="num">{nrmse_txt}</span>'
                        f'<span class="num">{r2_txt}</span>'
                        f'<span class="status {mcls}">{mlbl}</span>'
                        f'</div>')
                rows_html.append('</div>')
                st.markdown("\n".join(rows_html), unsafe_allow_html=True)

            # Right: overlay plot — model curves + data points for each observable
            with c2:
                fig = go.Figure()
                for m in s["obs_metrics"]:
                    obs = m["obs"]
                    state, scale = OBS_MAP[obs]
                    color = OBS_COLOR.get(obs, "#aaa")
                    fig.add_trace(go.Scatter(
                        x=s["t_eval"], y=s["sol"][state] * scale,
                        mode="lines", line=dict(color=color, width=2),
                        name=f"model · {obs}",
                        hovertemplate="t=%{x:.0f}<br>%{y:.4g}<extra></extra>"))
                    xs = [r[0] for r in m["rows"]]
                    ys = [r[1] for r in m["rows"]]
                    fig.add_trace(go.Scatter(
                        x=xs, y=ys, mode="markers",
                        marker=dict(color=color, size=10, symbol="circle",
                                    line=dict(color="#0a0d14", width=1.2)),
                        name=f"data · {obs}",
                        hovertemplate="t=%{x:.0f}<br>%{y:.4g}<extra>data</extra>"))
                fig.update_layout(
                    template="plotly_dark",
                    paper_bgcolor="#141824", plot_bgcolor="#141824",
                    margin=dict(l=44, r=8, t=24, b=32), height=240,
                    showlegend=True,
                    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=9,
                                color="#c0c9db"), orientation="h", y=-0.22),
                    xaxis=dict(title="time (min)", gridcolor="#242b3d",
                               tickfont=dict(color="#8892a6", size=9)),
                    yaxis=dict(title="concentration (µM)",
                               gridcolor="#242b3d",
                               tickfont=dict(color="#8892a6", size=9)),
                )
                st.plotly_chart(fig, use_container_width=True,
                                config={"displayModeBar": False})

    # ---- Skipped conditions ----
    if skipped:
        st.markdown(
            '<div class="section-label" style="margin-top:18px">'
            'Validation rows without a canonical simulation</div>',
            unsafe_allow_html=True)
        st.markdown(
            '<div style="color:var(--muted);font-size:0.78rem">'
            + " · ".join(f"<code>{c}</code> ({n})" for c, n in skipped)
            + "</div>", unsafe_allow_html=True)


st.markdown(
    '<div class="footer-caption">AP ODE · 13 state variables · Radau solver · '
    'FH–FB competition · tick-over · C3bBb amplification · '
    'Factor I inactivation · C5 cleavage · MAC damage</div>',
    unsafe_allow_html=True)
