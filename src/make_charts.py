"""Builds charts/*.png and results.json. Run: python src/make_charts.py"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

import model as m  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "charts"
OUT.mkdir(exist_ok=True)
INK, MUTED, GRID = "#1b1f1c", "#6b726d", "#e4e1d8"
GREEN, SOFT, RED, GOLD = "#1f5c43", "#9cc3ad", "#a8432f", "#b8892b"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "axes.edgecolor": GRID,
                     "axes.labelcolor": MUTED, "xtick.color": MUTED, "ytick.color": MUTED,
                     "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
                     "grid.color": GRID, "axes.axisbelow": True, "figure.dpi": 160,
                     "savefig.bbox": "tight", "savefig.facecolor": "white", "text.parse_math": False})


def title(ax, main, sub):
    ax.set_title(main, loc="left", fontsize=14, fontweight="bold", color=INK, pad=26)
    ax.text(0, 1.02, sub, transform=ax.transAxes, fontsize=10.5, color=MUTED)


ue = m.unit_economics()
items = [k for k in ue if k != "Weighted average"]

# 1. Contribution margin by item: weekly CM dollars, labelled with CM ratio
fig, ax = plt.subplots(figsize=(9, 4.8))
weekly = sorted(((k, ue[k]["cm"] * ue[k]["units_per_weekend"]) for k in items), key=lambda x: x[1])
ax.barh([k for k, _ in weekly], [v for _, v in weekly], color=GREEN, height=0.6)
for i, (k, v) in enumerate(weekly):
    ax.text(v + 3, i, f"${v:,.0f}  ·  {ue[k]['cm_ratio'] * 100:.0f}% margin  ·  ${ue[k]['cm']:.2f}/unit",
            va="center", color=INK, fontsize=10)
ax.set_xlim(0, 260); ax.set_xlabel("Contribution margin per weekend, $")
title(ax, "Chicken dishes carry the business",
      f"Contribution margin by item, typical weekend (total ${sum(v for _, v in weekly):,.0f})")
fig.savefig(OUT / "01_cm_by_item.png"); plt.close(fig)

# 2. High-low on the home gas and electric bill
hl = m.high_low()
fig, ax = plt.subplots(figsize=(9, 4.6))
ax.scatter(m.UNITS_COOKED, m.BILLS, s=55, color=SOFT, edgecolor=GREEN, zorder=3)
for mo, u, b in zip(m.MONTHS, m.UNITS_COOKED, m.BILLS):
    ax.annotate(mo, (u, b), xytext=(6, 4), textcoords="offset points", fontsize=9, color=MUTED)
xs = np.array([220, 470])
ax.plot(xs, hl["fixed_per_month"] + hl["variable_per_unit"] * xs, color=GREEN, lw=2)
ax.set_xlabel("Units cooked per month"); ax.set_ylabel("Gas + electric bill, $")
title(ax, f"Each extra dish adds about ${hl['variable_per_unit']:.2f} to the energy bill",
      f"High-low method, Nov (Diwali) vs Jul: ${hl['fixed_per_month']:.0f}/month base bill is household, not business")
fig.savefig(OUT / "02_high_low.png"); plt.close(fig)

# 3. Break-even before and after paying for her time
be = m.break_even()
fig, ax = plt.subplots(figsize=(9, 4.2))
labels = ["Her time treated as free", "Her time paid at $16/hour"]
vals = [be["before_her_time"]["breakeven_per_weekend"], be["including_her_time"]["breakeven_per_weekend"]]
weekly_units = be["units"] / m.WEEKENDS
ax.barh(labels, [weekly_units] * 2, color=SOFT, height=0.55, label="Units sold per weekend")
ax.barh(labels, vals, color=[GREEN, RED], height=0.55, label="Break-even units")
for i, (v, key) in enumerate(zip(vals, ["before_her_time", "including_her_time"])):
    ax.text(v + 1 if v < 20 else v - 1, i, f"break-even {v:.0f} units", va="center",
            color="white" if v > 20 else INK, fontsize=10, ha="left" if v < 20 else "right")
    ax.text(weekly_units + 1, i, f"{be[key]['margin_of_safety'] * 100:.0f}% margin of safety", va="center", color=INK)
ax.set_xlim(0, 100); ax.invert_yaxis(); ax.set_xlabel("Units per weekend (of 76.5 sold)")
title(ax, "Profitable either way, but the real risk is one person",
      "Break-even units per weekend, with and without valuing the owner's 12 hours")
fig.savefig(OUT / "03_break_even.png"); plt.close(fig)

# 4. Plan A vs Plan B cumulative cash
a, b = m.plan_cash_flows(), m.plan_cash_flows(helper=True)
fig, ax = plt.subplots(figsize=(9, 4.6))
yrs = range(6)
ax.plot(yrs, np.cumsum(a), marker="o", color=GREEN, lw=2.5, label=f"Plan A: equipment (NPV ${m.npv(a):,.0f})")
ax.plot(yrs, np.cumsum(b), marker="o", color=RED, lw=2.5, label=f"Plan B: equipment + helper (NPV −${-m.npv(b):,.0f})")
ax.axhline(0, color=INK, lw=1)
ax.annotate(f"Pays back in {m.payback(a):.1f} years", (m.payback(a), 0), xytext=(18, -40), textcoords="offset points",
            color=GREEN, arrowprops=dict(arrowstyle="-", color=GREEN))
ax.set_xlabel("Year"); ax.set_ylabel("Cumulative free cash flow, $"); ax.legend(frameon=False, loc="lower left")
title(ax, "Buy the bigger pots now; the helper does not pay yet",
      f"Undiscounted cumulative cash flow, $2,500 investment, {m.DISCOUNT * 100:.1f}% discount rate for NPV")
fig.savefig(OUT / "04_plan_a_vs_b.png"); plt.close(fig)

# 5. When does the helper pay off?
# Incremental value of the helper: Plan B serving `o` orders vs Plan A serving today's 2.5
orders = np.linspace(m.ORDERS_TURNED_DOWN, 9, 131)
base_a = m.npv(m.plan_cash_flows())
npv_b = [m.npv(m.plan_cash_flows(orders_per_weekend=o, helper=True)) - base_a for o in orders]
cross = orders[np.argmin(np.abs(npv_b))]
fig, ax = plt.subplots(figsize=(9, 4.6))
ax.plot(orders, npv_b, color=GREEN, lw=2.5)
ax.fill_between(orders, npv_b, 0, where=np.array(npv_b) < 0, color=RED, alpha=0.15)
ax.fill_between(orders, npv_b, 0, where=np.array(npv_b) >= 0, color=SOFT, alpha=0.5)
ax.axhline(0, color=INK, lw=1)
ax.axvline(m.ORDERS_TURNED_DOWN, color=MUTED, ls=":")
ax.text(m.ORDERS_TURNED_DOWN + 0.1, max(npv_b) * 0.8, "Today: 2-3 orders\nturned down a weekend", color=MUTED, fontsize=10)
ax.plot(cross, 0, "o", color=RED)
ax.annotate(f"Hire at ~{cross:.1f} turned-down\norders a weekend", (cross, 0), xytext=(-170, 30),
            textcoords="offset points", color=RED, arrowprops=dict(arrowstyle="-", color=RED))
ax.set_xlabel("Orders turned down per weekend"); ax.set_ylabel("Extra NPV from hiring, $")
title(ax, f"The hiring trigger: about {cross:.0f} turned-down orders a weekend",
      "NPV the part-time helper adds on top of Plan A, as unmet demand grows")
fig.savefig(OUT / "05_helper_trigger.png"); plt.close(fig)

results = {
    "unit_economics": {k: {kk: round(vv, 3) for kk, vv in v.items()} for k, v in ue.items()},
    "high_low": {k: (round(v, 4) if isinstance(v, float) else v) for k, v in hl.items()},
    "break_even": {k: ({kk: round(vv, 2) for kk, vv in v.items()} if isinstance(v, dict) else round(v, 2))
                   for k, v in be.items()},
    "plan_a": {"npv": round(m.npv(a), 2), "irr": round(m.irr(a), 4), "payback_years": round(m.payback(a), 2)},
    "plan_a_20pct_fewer_orders_npv": round(m.npv(m.plan_cash_flows(orders_per_weekend=2.0)), 2),
    "plan_b": {"npv": round(m.npv(b), 2)},
    "helper_trigger_total_orders_per_weekend": round(m.ORDERS_TURNED_DOWN + m.helper_breakeven_orders(), 2),
}
(ROOT / "results.json").write_text(json.dumps(results, indent=2))
print("charts and results.json written")
