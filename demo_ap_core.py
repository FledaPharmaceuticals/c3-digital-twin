"""
Minimal AP-core demo: pulls parameters + initial conditions from the loader,
integrates a 10-state reduced-order alternative-pathway model under two
scenarios (self-surface vs pathogen-surface), and overlays digitized Zewde
2016 / Bakshi 2020 validation points.

Run:
    source .venv/bin/activate
    python demo_ap_core.py
Produces: demo_ap_core.png + steady-state console printout.

Reduced-order AP model (Bakshi-style, ~10 ODEs):
    d[C3]     = -r_tick  - r_amp
    d[FB]     = -r_conv_form
    d[C3b]    =  r_tick  + r_amp - r_conv_form - r_inact
    d[C3bBb]  =  r_conv_form - r_decay_eff
    d[C3a]    =  r_tick  + r_amp
    d[iC3b]   =  r_inact          (FH+FI cleavage; only on 'self' surface)
    d[FD]=d[FH]=d[FI]=d[FP] = 0   (catalytic regulators conserved)

Properdin folded into effective decay rate via a Langmuir fraction:
    f_P = FP / (FP + Kd_P)
    k_decay_eff = (1-f_P) * k_decay + f_P * k_decay_P
"""
import numpy as np
from scipy.integrate import solve_ivp
import matplotlib.pyplot as plt

from c3_twin_loader import C3Twin

tw = C3Twin()

# ---------------------------------------------------------------------------
# 1. Pull parameters from the calibrated XLSX via the loader
# ---------------------------------------------------------------------------
def pick(rid, fallback):
    v = tw.kinetic_value(rid)
    return v if v is not None else fallback

k = {
    "tick":       pick("R009",  4.98e-5),     # Pangburn 1983 spontaneous tickover
    "conv_form":  pick("R001a", 0.1278),       # Zewde fluid-phase C3b+FB kon
    "decay":      pick("R004",  0.462),        # Pangburn 1986 C3bBb intrinsic decay
    "decay_P":    pick("R005",  0.0462),       # properdin-stabilised decay
    "Kd_P":       0.03 / 0.87,                 # Bakshi R006b/R006a
    "amp_kcat":   pick("R003a", 106.8) * 0.01, # Pangburn 1986 kcat, sigma-corrected
    "amp_Km":     pick("R003b", 5.86),
    "inact_kcat": pick("R008a", 78),           # Pangburn 1983 FH/FI catalysis
    "inact_Km":   pick("R008b", 0.25),
}
print("[k] parameters loaded:")
for name, val in k.items():
    print(f"    {name:12s} = {val:g}")

# ---------------------------------------------------------------------------
# 2. Initial conditions from loader
# ---------------------------------------------------------------------------
ic = tw.initial_conditions("healthy_baseline")
print("\n[ic] healthy baseline (uM):")
for n in ["C3", "FB", "FD", "FH", "FI", "FP"]:
    print(f"    {n:4s} = {ic.get(n)}")

# State vector layout:
#   0  1   2   3   4   5   6     7       8     9
#   C3 FB  FD  FH  FI  FP  C3b   C3bBb   C3a   iC3b
def state_vec(ic):
    return np.array([
        ic["C3"], ic["FB"], ic["FD"], ic["FH"], ic["FI"], ic["FP"],
        0.0, 0.0, 0.0, 0.0,
    ])

# ---------------------------------------------------------------------------
# 3. RHS
# ---------------------------------------------------------------------------
def rhs(t, y, surface):
    C3, FB, FD, FH, FI, FP, C3b, C3bBb, C3a, iC3b = y

    # Tickover
    r_tick = k["tick"] * C3

    # C3 convertase formation: lumped k_on * C3b * FB (assumes FD saturating)
    r_conv_form = k["conv_form"] * C3b * FB

    # Effective decay (properdin fraction on convertase)
    f_P = FP / (FP + k["Kd_P"] + 1e-12)
    k_decay_eff = (1 - f_P) * k["decay"] + f_P * k["decay_P"]
    r_decay = k_decay_eff * C3bBb

    # Amplification (C3bBb cleaves C3)
    r_amp = k["amp_kcat"] * C3bBb * C3 / (k["amp_Km"] + C3 + 1e-12)

    # FH+FI inactivation of C3b — only on self surface
    if surface == "self":
        r_inact = k["inact_kcat"] * C3b * FH / (k["inact_Km"] + C3b + 1e-12)
    else:  # pathogen: no FH access
        r_inact = 0.0

    return [
        -r_tick - r_amp,                          # C3
        -r_conv_form,                             # FB
        0.0, 0.0, 0.0, 0.0,                       # FD, FH, FI, FP (catalytic)
        r_tick + r_amp - r_conv_form - r_inact,   # C3b
        r_conv_form - r_decay,                    # C3bBb
        r_tick + r_amp,                           # C3a
        r_inact,                                  # iC3b
    ]


# ---------------------------------------------------------------------------
# 4. Integrate both scenarios
# ---------------------------------------------------------------------------
y0 = state_vec(ic)
t_span = (0, 120)
t_eval = np.linspace(0, 120, 241)

sol_self = solve_ivp(rhs, t_span, y0, args=("self",), t_eval=t_eval,
                     method="LSODA", rtol=1e-8, atol=1e-12)
sol_path = solve_ivp(rhs, t_span, y0, args=("pathogen",), t_eval=t_eval,
                     method="LSODA", rtol=1e-8, atol=1e-12)

STATE = ["C3", "FB", "FD", "FH", "FI", "FP", "C3b", "C3bBb", "C3a", "iC3b"]
def get(sol, name):
    return sol.y[STATE.index(name)]


# ---------------------------------------------------------------------------
# 5. Plot + overlay validation points
# ---------------------------------------------------------------------------
fig, axes = plt.subplots(2, 2, figsize=(11, 7.5))
fig.suptitle("C3 Digital Twin — reduced AP core demo (loader-driven)",
             fontsize=13, fontweight="bold")

# Panel A: C3 (plasma)
ax = axes[0, 0]
ax.plot(t_eval, get(sol_self, "C3"), lw=2, label="sim: self surface")
ax.plot(t_eval, get(sol_path, "C3"), lw=2, label="sim: pathogen surface")
pts = tw.validation("C3", condition="host_surface_normal")
if pts:
    ax.scatter([p.t_or_dose for p in pts], [p.value for p in pts],
               color="C0", zorder=5, label="Zewde 2016 Fig 2 (self)")
ax.set_title("C3 (plasma)"); ax.set_xlabel("time (min)"); ax.set_ylabel("µM")
ax.legend(fontsize=8); ax.grid(alpha=0.3)

# Panel B: C3a
ax = axes[0, 1]
ax.plot(t_eval, get(sol_self, "C3a"), lw=2, label="sim: self")
ax.plot(t_eval, get(sol_path, "C3a"), lw=2, label="sim: pathogen")
pts = tw.validation("C3a", condition="pathogen_no_FH")
if pts:
    ax.scatter([p.t_or_dose for p in pts], [p.value for p in pts],
               color="C1", zorder=5, label="Zewde 2016 Fig 5 (pathogen)")
ax.set_title("C3a (plasma)"); ax.set_xlabel("time (min)"); ax.set_ylabel("µM")
ax.legend(fontsize=8); ax.grid(alpha=0.3)

# Panel C: surface C3b
ax = axes[1, 0]
ax.plot(t_eval, get(sol_self, "C3b"), lw=2, label="sim: self")
ax.plot(t_eval, get(sol_path, "C3b"), lw=2, label="sim: pathogen")
ax.set_yscale("log")
ax.set_title("C3b (log scale; surface accumulation)")
ax.set_xlabel("time (min)"); ax.set_ylabel("µM")
ax.legend(fontsize=8); ax.grid(alpha=0.3, which="both")

# Panel D: C3bBb convertase
ax = axes[1, 1]
ax.plot(t_eval, get(sol_self, "C3bBb"), lw=2, label="sim: self")
ax.plot(t_eval, get(sol_path, "C3bBb"), lw=2, label="sim: pathogen")
# Bakshi 2020 steady-state target for self surface (arbitrary units — plot as horizontal guide)
ss = tw.steady_state("C3bBb", model_variant="properdin_model")
if ss and ss.value is not None:
    ax.axhline(ss.value, color="gray", ls="--", lw=1,
               label=f"Bakshi SS target (properdin): {ss.value:g} {ss.unit}")
ax.set_yscale("log")
ax.set_title("C3bBb convertase (log scale)")
ax.set_xlabel("time (min)"); ax.set_ylabel("µM")
ax.legend(fontsize=8); ax.grid(alpha=0.3, which="both")

plt.tight_layout()
plt.savefig("demo_ap_core.png", dpi=130)
print("\nSaved plot → demo_ap_core.png")


# ---------------------------------------------------------------------------
# 6. Steady-state printout vs Bakshi Table 3
# ---------------------------------------------------------------------------
print("\n[steady-state comparison at t=120 min]")
print(f"  {'species':<8} {'sim(self)':>12} {'sim(path)':>12}   Bakshi target")
for name in ["C3", "C3b", "C3bBb", "C3a", "iC3b"]:
    sim_self = get(sol_self, name)[-1]
    sim_path = get(sol_path, name)[-1]
    bakshi = tw.steady_state(name, model_variant="properdin_model")
    btxt = f"{bakshi.value:g} {bakshi.unit}" if bakshi and bakshi.value is not None else "—"
    print(f"  {name:<8} {sim_self:>12.4g} {sim_path:>12.4g}   {btxt}")
