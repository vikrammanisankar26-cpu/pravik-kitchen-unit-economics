"""Pravik's Kitchen: unit economics, break-even and a capacity investment decision.

A weekend home-cooked South Indian food business in New Jersey. The owner had no
written records, so every input below is an ESTIMATE, calibrated to the roughly
$1,000 of sales she brings in on a normal weekend.
"""

WEEKENDS = 52
TAX = 0.25                      # federal + NJ income tax + self-employment tax
DISCOUNT = 0.045 + 0.05 + 0.03 + 0.04   # risk-free + equity premium + size + one-cook risk = 16.5%

# name: (price, food, packaging, oil & extras, units per weekend)
MENU = {
    "Chicken biryani": (15, 4.50, 0.50, 0.20, 18),
    "Mutton biryani":  (20, 7.50, 0.50, 0.20, 8),
    "Veg biryani":     (12, 3.00, 0.50, 0.20, 8),
    "Chicken gravy":   (16, 5.00, 0.50, 0.20, 15),
    "Snacks (dozen)":  (8, 1.80, 0.20, 0.50, 15),
    "Sambar & soups":  (8, 1.60, 0.50, 0.10, 12),
    "Party tray":      (90, 30.00, 3.00, 1.00, 0.5),
}
FIXED_PER_YEAR = {"Phone (WhatsApp orders)": 480, "Car fuel": 720, "Flyers & samples": 300,
                  "Depreciation, existing pots": 600}
OWNER_HOURS, HOURLY_VALUE = 12, 16.0          # her weekend hours; NJ part-time kitchen pay

# Home gas + electric: units cooked and bill per month (estimated), for the high-low method
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
UNITS_COOKED = [269, 269, 316, 300, 300, 253, 237, 269, 316, 395, 458, 411]
BILLS = [285, 280, 295, 285, 285, 265, 271, 280, 295, 318, 337, 323]

# Capacity investment
EQUIPMENT, SALVAGE, LIFE, UPKEEP = 2_500, 300, 5, 300
ORDERS_TURNED_DOWN, YEAR1_WIN_BACK = 2.5, 0.80
TYPICAL_ORDER = ["Chicken biryani", "Chicken gravy", "Snacks (dozen)"]
HELPER_HOURS, EXTRA_TRAYS = 6, 12


def high_low():
    hi = UNITS_COOKED.index(max(UNITS_COOKED))
    lo = UNITS_COOKED.index(min(UNITS_COOKED))
    var = (BILLS[hi] - BILLS[lo]) / (UNITS_COOKED[hi] - UNITS_COOKED[lo])
    return {"variable_per_unit": var, "fixed_per_month": BILLS[hi] - var * UNITS_COOKED[hi],
            "high": MONTHS[hi], "low": MONTHS[lo]}


def unit_economics():
    gas = high_low()["variable_per_unit"]
    rows = {}
    for name, (price, food, pack, oil, qty) in MENU.items():
        vc = food + pack + oil + gas
        rows[name] = {"price": price, "variable_cost": vc, "cm": price - vc, "cm_ratio": (price - vc) / price,
                      "units_per_weekend": qty}
    qty = sum(r["units_per_weekend"] for r in rows.values())
    w = lambda k: sum(r[k] * r["units_per_weekend"] for r in rows.values()) / qty  # noqa: E731
    rows["Weighted average"] = {"price": w("price"), "variable_cost": w("variable_cost"), "cm": w("cm"),
                                "cm_ratio": w("cm") / w("price"), "units_per_weekend": qty}
    return rows


def break_even():
    ue = unit_economics()["Weighted average"]
    units = ue["units_per_weekend"] * WEEKENDS
    sales = units * ue["price"]
    fixed = sum(FIXED_PER_YEAR.values())
    owner = OWNER_HOURS * HOURLY_VALUE * WEEKENDS
    out = {}
    for label, f in (("before_her_time", fixed), ("including_her_time", fixed + owner)):
        be_units = f / ue["cm"]
        out[label] = {"fixed": f, "breakeven_units": be_units, "breakeven_per_weekend": be_units / WEEKENDS,
                      "breakeven_sales": f / ue["cm_ratio"], "margin_of_safety": (units - be_units) / units,
                      "operating_income": units * ue["cm"] - f}
    out["sales"], out["units"] = sales, units
    out["profit_per_hour"] = out["before_her_time"]["operating_income"] / (OWNER_HOURS * WEEKENDS)
    return out


def order_cm():
    ue = unit_economics()
    return sum(ue[n]["cm"] for n in TYPICAL_ORDER)


def plan_cash_flows(orders_per_weekend=ORDERS_TURNED_DOWN, helper=False):
    ue = unit_economics()
    dep = (EQUIPMENT - SALVAGE) / LIFE
    flows = [-EQUIPMENT]
    for year in range(1, LIFE + 1):
        orders = orders_per_weekend * WEEKENDS * (YEAR1_WIN_BACK if year == 1 else 1)
        ebitda = orders * order_cm() - UPKEEP
        if helper:
            ebitda += EXTRA_TRAYS * ue["Party tray"]["cm"] - HELPER_HOURS * HOURLY_VALUE * WEEKENDS
        ebit = ebitda - dep
        fcf = ebit * (1 - TAX) + dep + (SALVAGE if year == LIFE else 0)
        flows.append(fcf)
    return flows


def npv(flows, rate=DISCOUNT):
    return sum(cf / (1 + rate) ** t for t, cf in enumerate(flows))


def irr(flows, lo=-0.9, hi=5.0):
    if npv(flows, lo) * npv(flows, hi) > 0:
        return None
    for _ in range(200):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if npv(flows, mid) > 0 else (lo, mid)
    return (lo + hi) / 2


def payback(flows):
    cum = flows[0]
    for t in range(1, len(flows)):
        if cum + flows[t] >= 0:
            return t - 1 + (-cum) / flows[t]
        cum += flows[t]
    return None


def helper_breakeven_orders():
    """Extra orders per weekend needed for the helper to pay for herself."""
    ue = unit_economics()
    helper = HELPER_HOURS * HOURLY_VALUE * WEEKENDS
    return (helper - EXTRA_TRAYS * ue["Party tray"]["cm"]) / (order_cm() * WEEKENDS)
