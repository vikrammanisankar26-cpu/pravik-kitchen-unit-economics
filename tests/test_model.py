"""Checks that the Python model reproduces the submitted Excel workbook."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import model as m  # noqa: E402


class ReproducesExcel(unittest.TestCase):
    def test_high_low(self):
        hl = m.high_low()
        self.assertAlmostEqual(hl["variable_per_unit"], 0.2986, places=4)
        self.assertEqual((hl["high"], hl["low"]), ("Nov", "Jul"))

    def test_weighted_cm(self):
        w = m.unit_economics()["Weighted average"]
        self.assertAlmostEqual(w["cm"], 8.483, places=3)
        self.assertAlmostEqual(w["cm_ratio"], 0.632, places=3)

    def test_break_even(self):
        be = m.break_even()
        self.assertAlmostEqual(be["sales"], 53_404, places=0)
        self.assertAlmostEqual(be["before_her_time"]["breakeven_units"], 247.55, places=2)
        self.assertAlmostEqual(be["including_her_time"]["margin_of_safety"], 0.642, places=3)
        self.assertAlmostEqual(be["before_her_time"]["operating_income"], 31_645.6, places=1)
        self.assertAlmostEqual(be["profit_per_hour"], 50.71, places=2)

    def test_investment(self):
        a = m.plan_cash_flows()
        self.assertAlmostEqual(m.npv(a), 4_649.60, places=1)
        self.assertAlmostEqual(m.irr(a), 0.787, places=3)
        self.assertAlmostEqual(m.payback(a), 1.30, places=2)
        self.assertAlmostEqual(m.npv(m.plan_cash_flows(orders_per_weekend=2.0)), 3_173.20, places=1)
        self.assertAlmostEqual(m.npv(m.plan_cash_flows(helper=True)), -5_845.24, places=1)
        self.assertAlmostEqual(m.helper_breakeven_orders(), 3.366, places=3)


if __name__ == "__main__":
    unittest.main()
