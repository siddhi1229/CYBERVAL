"""
CYBERVAL - Module P5: Investment Optimization
Standalone Verification & Demonstration Test Suite

This script executes standalone validation of:
1. ROSI (Return on Security Investment) mathematical formulas.
2. 0/1 Knapsack Budget Optimization (Maximizing Risk Reduction under ₹1 Crore Budget).
3. Risk-Reduction Curves demonstrating diminishing marginal returns.
4. FastAPI REST API endpoints using FastAPI TestClient.

Usage:
    python backend/app/standalone_test.py
    or
    python standalone_test.py (from inside backend/app/)
"""

import sys
import os
import io

# Ensure UTF-8 output encoding on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Ensure backend/app and parent directories are in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, "..", ".."))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    from backend.app.schemas import BudgetRequest, ControlOption
    from backend.app.services.optimization import InvestmentOptimizationService
    from backend.app.mock_data import (
        MOCK_P2_ENTERPRISE_BASELINE_EAL,
        MOCK_P3_ASSET_BASELINE_EAL,
        MOCK_AVAILABLE_CONTROLS_RAW,
        format_inr,
    )
    from backend.app.main import app
except ImportError:
    # If running from inside backend/app directly
    from schemas import BudgetRequest, ControlOption
    from services.optimization import InvestmentOptimizationService
    from mock_data import (
        MOCK_P2_ENTERPRISE_BASELINE_EAL,
        MOCK_P3_ASSET_BASELINE_EAL,
        MOCK_AVAILABLE_CONTROLS_RAW,
        format_inr,
    )
    from main import app

from starlette.testclient import TestClient


def print_header(title: str):
    width = 90
    print("\n" + "=" * width)
    print(f" {title.center(width - 2)} ")
    print("=" * width)


def print_section(title: str):
    print(f"\n--- {title} " + "-" * (88 - len(title)))


def test_rosi_calculations():
    print_header("TEST 1: RETURN ON SECURITY INVESTMENT (ROSI) FORMULA VERIFICATION")
    print("Formula: ROSI = [ ( (Baseline EAL * Control Effectiveness) - Annual Cost ) / Annual Cost ] * 100\n")

    service = InvestmentOptimizationService()
    controls = service._hydrate_controls(None)

    print(f"{'Control ID':<15} | {'Cost (INR)':<15} | {'Baseline EAL':<15} | {'Eff %':<6} | {'Risk Red (INR)':<15} | {'Net Benefit':<15} | {'ROSI (%)':<10}")
    print("-" * 115)

    expected_results = {
        "CTRL-MFA-001": {"risk_red": 31_500_000.0, "net_benefit": 30_000_000.0, "rosi": 2000.0},
        "CTRL-PATCH-002": {"risk_red": 18_000_000.0, "net_benefit": 14_000_000.0, "rosi": 350.0},
        "CTRL-EDR-003": {"risk_red": 12_000_000.0, "net_benefit": 9_000_000.0, "rosi": 300.0},
        "CTRL-NET-004": {"risk_red": 14_000_000.0, "net_benefit": 9_000_000.0, "rosi": 180.0},
    }

    for ctrl in controls:
        rosi = ctrl.rosi
        assert rosi is not None, f"ROSI result missing for {ctrl.id}"
        
        expected = expected_results[ctrl.id]
        assert abs(rosi.risk_reduction - expected["risk_red"]) < 1e-4, f"Mismatch in risk reduction for {ctrl.id}"
        assert abs(rosi.net_financial_benefit - expected["net_benefit"]) < 1e-4, f"Mismatch in net benefit for {ctrl.id}"
        assert abs(rosi.rosi_percentage - expected["rosi"]) < 1e-2, f"Mismatch in ROSI % for {ctrl.id}"

        print(
            f"{ctrl.id:<15} | "
            f"₹{ctrl.annual_cost:>12,.0f} | "
            f"₹{ctrl.baseline_eal:>12,.0f} | "
            f"{ctrl.effectiveness * 100:>5.0f}% | "
            f"₹{rosi.risk_reduction:>12,.0f} | "
            f"₹{rosi.net_financial_benefit:>12,.0f} | "
            f"{rosi.rosi_percentage:>8.1f}%"
        )

    print("\n[SUCCESS] All ROSI formula computations match exact theoretical values.")


def test_budget_optimization():
    print_header("TEST 2: 0/1 KNAPSACK BUDGET OPTIMIZATION (BUDGET = ₹1,00,00,000 / ₹1 CR)")
    
    total_budget = 10_000_000.0  # ₹1.00 Crore
    service = InvestmentOptimizationService()

    result = service.optimize_budget(
        total_budget=total_budget,
        enterprise_baseline_eal=MOCK_P2_ENTERPRISE_BASELINE_EAL
    )

    print_section("EXECUTIVE SUMMARY")
    print(f"Total Available Budget     : {result.formatted_total_budget}")
    print(f"Total Committed Investment : {result.formatted_total_investment}")
    print(f"Unallocated Surplus Budget : {result.formatted_remaining_budget} ({100 - result.budget_utilization_pct:.1f}%)")
    print(f"Enterprise Baseline EAL    : {result.formatted_baseline_eal}")
    print(f"Total Risk Reduced (EAL)   : {result.formatted_total_risk_reduction} ({result.overall_risk_reduction_pct:.1f}% Enterprise Risk Mitigated)")
    print(f"Residual Enterprise EAL    : {result.formatted_residual_eal}")
    print(f"Portfolio Net Benefit      : {result.formatted_net_benefit}")
    print(f"Portfolio Aggregate ROSI   : {result.portfolio_rosi_percentage:.2f}%")
    print(f"Benefit-to-Cost Ratio      : {result.benefit_cost_ratio:.2f}x (Returns ₹{result.benefit_cost_ratio:.2f} in risk reduction per ₹1 invested)")

    print_section("SELECTED OPTIMAL CONTROLS")
    selected_ids = [c.id for c in result.selected_controls]
    for idx, c in enumerate(result.selected_controls, start=1):
        print(f"  {idx}. [{c.id}] {c.name}")
        print(f"     - Cost: {format_inr(c.annual_cost)} | Target: {c.target_asset_or_risk}")
        print(f"     - Risk Reduction: {format_inr(c.risk_reduction)} | Control ROSI: {c.rosi.rosi_percentage:.1f}%")

    print_section("EXCLUDED CONTROLS (DUE TO BUDGET CEILING)")
    for idx, c in enumerate(result.unselected_controls, start=1):
        print(f"  {idx}. [{c.id}] {c.name}")
        print(f"     - Cost: {format_inr(c.annual_cost)} | Target: {c.target_asset_or_risk}")
        print(f"     - Risk Reduction: {format_inr(c.risk_reduction)} | Control ROSI: {c.rosi.rosi_percentage:.1f}%")

    # Mathematical Verification:
    # Selected must be MFA (15L), Patch (40L), EDR (30L) totaling 85L cost and 615L risk reduction.
    # Micro-segmentation (50L) is excluded because 15L + 40L + 50L = 105L > 100L.
    assert "CTRL-MFA-001" in selected_ids, "MFA should be selected (highest efficiency)"
    assert "CTRL-PATCH-002" in selected_ids, "Patch should be selected"
    assert "CTRL-EDR-003" in selected_ids, "EDR should be selected"
    assert "CTRL-NET-004" not in selected_ids, "Network Micro-segmentation exceeds budget constraint"
    assert result.total_investment == 8_500_000.0, f"Expected total investment ₹85,00,000, got {result.total_investment}"
    assert result.total_risk_reduction == 61_500_000.0, f"Expected risk reduction ₹6,15,00,000, got {result.total_risk_reduction}"
    assert result.remaining_budget == 1_500_000.0, f"Expected remaining budget ₹15,00,000, got {result.remaining_budget}"

    print("\n[SUCCESS] 0/1 Knapsack Solver identified mathematically optimal combination.")


def test_risk_reduction_curves():
    print_header("TEST 3: RISK-REDUCTION CURVE & DIMINISHING RETURNS GENERATION")
    
    service = InvestmentOptimizationService()
    curve = service.generate_risk_reduction_curve(enterprise_baseline_eal=MOCK_P2_ENTERPRISE_BASELINE_EAL)

    print(f"Enterprise Baseline EAL: {curve.formatted_baseline_enterprise_eal}\n")
    print(f"{'Step':<5} | {'Control Added':<36} | {'Marginal Cost':<16} | {'Marginal Red.':<16} | {'Efficiency':<10} | {'Cumul. Inv.':<16} | {'Cumul. Red.':<16} | {'Residual EAL':<16}")
    print("-" * 155)

    efficiencies = []
    for dp in curve.data_points:
        if dp.step > 0:
            efficiencies.append(dp.marginal_efficiency)
        print(
            f"{dp.step:<5} | "
            f"{(dp.control_name or 'Baseline')[:35]:<36} | "
            f"₹{dp.marginal_cost:>13,.0f} | "
            f"₹{dp.marginal_risk_reduction:>13,.0f} | "
            f"{dp.marginal_efficiency:>8.2f}x | "
            f"₹{dp.cumulative_investment:>13,.0f} | "
            f"₹{dp.cumulative_risk_reduction:>13,.0f} | "
            f"₹{dp.residual_eal:>13,.0f}"
        )

    print_section("CURVE ANALYSIS & NARRATIVE")
    print(curve.summary)

    # Verify strictly diminishing marginal efficiency
    for i in range(len(efficiencies) - 1):
        assert efficiencies[i] >= efficiencies[i + 1], (
            f"Diminishing returns violated: step {i+1} efficiency ({efficiencies[i]}) < "
            f"step {i+2} efficiency ({efficiencies[i+1]})"
        )

    print("\n[SUCCESS] Diminishing returns curve strictly validated (Efficiency decreases monotonically).")


def test_fastapi_endpoints():
    print_header("TEST 4: FASTAPI HTTP ENDPOINTS VERIFICATION")
    
    client = TestClient(app)

    # 1. Health check
    res = client.get("/")
    assert res.status_code == 200, f"Health check failed: {res.text}"
    print(f"[PASSED] GET / -> 200 OK ({res.json()['service']})")

    # 2. Controls endpoint
    res = client.get("/api/investment/controls")
    assert res.status_code == 200, f"Controls list failed: {res.text}"
    controls_data = res.json()
    assert len(controls_data) == 4, f"Expected 4 controls, got {len(controls_data)}"
    print(f"[PASSED] GET /api/investment/controls -> 200 OK ({len(controls_data)} candidate controls loaded)")

    # 3. Optimize endpoint
    payload = {
        "total_budget": 10000000.0,
        "total_enterprise_eal": 100000000.0,
        "currency": "INR"
    }
    res = client.post("/api/investment/optimize", json=payload)
    assert res.status_code == 200, f"Optimize endpoint failed: {res.text}"
    opt_data = res.json()
    assert opt_data["total_investment"] == 8500000.0
    assert opt_data["total_risk_reduction"] == 61500000.0
    print(f"[PASSED] POST /api/investment/optimize -> 200 OK (Optimized Investment: {opt_data['formatted_total_investment']}, Risk Reduction: {opt_data['formatted_total_risk_reduction']})")

    # 4. Curves endpoint
    res = client.get("/api/investment/curves")
    assert res.status_code == 200, f"Curves endpoint failed: {res.text}"
    curves_data = res.json()
    assert len(curves_data["data_points"]) == 5  # Step 0 (baseline) + 4 controls
    print(f"[PASSED] GET /api/investment/curves -> 200 OK ({len(curves_data['data_points'])} curve steps returned)")

    # 5. Single ROSI endpoint
    params = {
        "baseline_eal": 42000000.0,
        "effectiveness": 0.75,
        "annual_cost": 1500000.0,
        "control_id": "TEST-MFA",
        "control_name": "Test MFA Control"
    }
    res = client.post("/api/investment/rosi", params=params)
    assert res.status_code == 200, f"ROSI endpoint failed: {res.text}"
    rosi_data = res.json()
    assert rosi_data["rosi_percentage"] == 2000.0
    print(f"[PASSED] POST /api/investment/rosi -> 200 OK (Calculated ROSI: {rosi_data['rosi_percentage']}%)")


if __name__ == "__main__":
    print_header("CYBERVAL - MODULE P5: INVESTMENT OPTIMIZATION TEST SUITE")
    test_rosi_calculations()
    test_budget_optimization()
    test_risk_reduction_curves()
    test_fastapi_endpoints()
    print_header("ALL MODULE P5 TESTS COMPLETED WITH 100% SUCCESS")
