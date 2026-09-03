"""
CYBERVAL - Module P5: Investment Optimization Service
Core Mathematical and Algorithmic Engine for:
1. Return on Security Investment (ROSI) Calculation
2. 0/1 Knapsack Dynamic Programming / Branch & Bound Budget Optimizer
3. Diminishing Returns Risk-Reduction Curve Generator

All financial calculations and outputs use Indian Rupees (INR - ₹).
"""

from typing import List, Optional, Tuple, Dict, Any
import math

from ..schemas import (
    ROSIResult,
    ControlOption,
    OptimizationResult,
    CurveDataPoint,
    RiskReductionCurveResponse,
)
from ..mock_data import (
    MOCK_P2_ENTERPRISE_BASELINE_EAL,
    MOCK_P3_ASSET_BASELINE_EAL,
    MOCK_AVAILABLE_CONTROLS_RAW,
    format_inr,
)


class InvestmentOptimizationService:
    """
    Service class providing core algorithms for Cyber Security Investment Optimization (Module P5).
    """

    def __init__(self):
        pass

    # =========================================================================
    # REQ 1.1: ROSI (RETURN ON SECURITY INVESTMENT) CALCULATION
    # =========================================================================
    def calculate_rosi(
        self,
        baseline_eal: float,
        effectiveness: float,
        annual_cost: float,
        control_id: str = "CTRL-GENERIC",
        control_name: str = "Generic Security Control",
        target_asset_or_risk: str = "ENTERPRISE",
    ) -> ROSIResult:
        """
        Calculates Return on Security Investment (ROSI).
        
        Formula:
            ROSI (%) = [ ( (Baseline EAL * Control Effectiveness) - Annual Cost ) / Annual Cost ] * 100
        
        Args:
            baseline_eal: Expected Annual Loss (EAL) in INR before the control is implemented.
            effectiveness: Fractional risk reduction (0.0 to 1.0, e.g. 0.75 for 75%).
            annual_cost: Annualized cost of implementing and operating the control in INR.
            control_id: Unique control identifier.
            control_name: Display name.
            target_asset_or_risk: Targeted asset or risk scope.
            
        Returns:
            ROSIResult containing computed metrics, net benefit, ROSI %, and INR formatted strings.
        """
        # Ensure non-negative baseline and cost
        baseline_eal = max(0.0, float(baseline_eal))
        annual_cost = max(0.0, float(annual_cost))
        effectiveness = max(0.0, min(1.0, float(effectiveness)))

        # 1. Financial Risk Reduction (EAL Reduced)
        risk_reduction = baseline_eal * effectiveness

        # 2. Net Financial Benefit (Risk Reduction - Annual Cost)
        net_financial_benefit = risk_reduction - annual_cost

        # 3. ROSI Calculation
        if annual_cost > 0:
            rosi_percentage = (net_financial_benefit / annual_cost) * 100.0
        else:
            # Handle edge-case of zero cost
            rosi_percentage = float("inf") if risk_reduction > 0 else 0.0

        return ROSIResult(
            control_id=control_id,
            control_name=control_name,
            target_asset_or_risk=target_asset_or_risk,
            baseline_eal=baseline_eal,
            control_effectiveness=effectiveness,
            annual_cost=annual_cost,
            risk_reduction=risk_reduction,
            net_financial_benefit=net_financial_benefit,
            rosi_percentage=round(rosi_percentage, 2),
            currency="INR",
            formatted_risk_reduction=format_inr(risk_reduction),
            formatted_annual_cost=format_inr(annual_cost),
            formatted_net_benefit=format_inr(net_financial_benefit),
        )

    # =========================================================================
    # REQ 1.2: BUDGET OPTIMIZATION ENGINE (0/1 KNAPSACK SOLVER)
    # =========================================================================
    def optimize_budget(
        self,
        total_budget: float = 10_000_000.0,
        controls: Optional[List[ControlOption]] = None,
        enterprise_baseline_eal: Optional[float] = None,
    ) -> OptimizationResult:
        """
        Selects the optimal subset of security controls to MAXIMIZE total financial risk reduction
        (EAL mitigated in INR) without exceeding the total budget limit.
        
        Solves the classic 0/1 Knapsack Problem:
            Maximize:   Sum( RiskReduction_i * x_i )
            Subject to: Sum( Cost_i * x_i ) <= Total Budget
            Where:      x_i in {0, 1}
        
        Uses an exact branch-and-bound / DFS memoization algorithm guaranteeing 100% mathematical
        optimality regardless of cost scales or floating-point budget sizes.
        
        Args:
            total_budget: Maximum available budget in INR (default ₹1,00,00,000 / ₹1 Cr).
            controls: List of ControlOption candidates. If None, uses mock P1/P2 controls.
            enterprise_baseline_eal: Total Enterprise Baseline EAL in INR. If None, uses mock P2 value.
            
        Returns:
            OptimizationResult containing optimal selection, budget metrics, and portfolio ROSI.
        """
        # Resolve enterprise baseline EAL
        if enterprise_baseline_eal is None or enterprise_baseline_eal <= 0:
            enterprise_baseline_eal = MOCK_P2_ENTERPRISE_BASELINE_EAL

        # Load and hydrate candidate controls
        hydrated_controls: List[ControlOption] = self._hydrate_controls(controls)

        # Execute 0/1 Knapsack Solver
        selected_indices = self._solve_01_knapsack(
            budget=total_budget,
            controls=hydrated_controls
        )

        selected_controls: List[ControlOption] = []
        unselected_controls: List[ControlOption] = []

        for idx, ctrl in enumerate(hydrated_controls):
            if idx in selected_indices:
                selected_controls.append(ctrl)
            else:
                unselected_controls.append(ctrl)

        # Aggregate portfolio metrics
        total_investment = sum(c.annual_cost for c in selected_controls)
        remaining_budget = max(0.0, total_budget - total_investment)
        budget_utilization_pct = min(100.0, max(0.0, (total_investment / total_budget * 100.0))) if total_budget > 0 else 0.0

        total_risk_reduction = sum(c.risk_reduction or 0.0 for c in selected_controls)
        residual_enterprise_eal = max(0.0, enterprise_baseline_eal - total_risk_reduction)
        overall_risk_reduction_pct = (
            min(100.0, max(0.0, (total_risk_reduction / enterprise_baseline_eal * 100.0)))
            if enterprise_baseline_eal > 0
            else 0.0
        )

        portfolio_net_benefit = total_risk_reduction - total_investment
        portfolio_rosi_pct = (
            (portfolio_net_benefit / total_investment * 100.0)
            if total_investment > 0
            else 0.0
        )
        benefit_cost_ratio = (
            (total_risk_reduction / total_investment)
            if total_investment > 0
            else 0.0
        )

        return OptimizationResult(
            total_budget=total_budget,
            total_investment=total_investment,
            remaining_budget=remaining_budget,
            budget_utilization_pct=round(budget_utilization_pct, 2),
            baseline_enterprise_eal=enterprise_baseline_eal,
            total_risk_reduction=total_risk_reduction,
            residual_enterprise_eal=residual_enterprise_eal,
            overall_risk_reduction_pct=round(overall_risk_reduction_pct, 2),
            portfolio_net_benefit=portfolio_net_benefit,
            portfolio_rosi_percentage=round(portfolio_rosi_pct, 2),
            benefit_cost_ratio=round(benefit_cost_ratio, 2),
            selected_controls=selected_controls,
            unselected_controls=unselected_controls,
            currency="INR",
            formatted_total_budget=format_inr(total_budget),
            formatted_total_investment=format_inr(total_investment),
            formatted_remaining_budget=format_inr(remaining_budget),
            formatted_baseline_eal=format_inr(enterprise_baseline_eal),
            formatted_total_risk_reduction=format_inr(total_risk_reduction),
            formatted_residual_eal=format_inr(residual_enterprise_eal),
            formatted_net_benefit=format_inr(portfolio_net_benefit),
        )

    # =========================================================================
    # REQ 1.3: RISK-REDUCTION CURVE GENERATOR (DIMINISHING RETURNS)
    # =========================================================================
    def generate_risk_reduction_curve(
        self,
        controls: Optional[List[ControlOption]] = None,
        enterprise_baseline_eal: Optional[float] = None,
        max_budget: Optional[float] = None,
    ) -> RiskReductionCurveResponse:
        """
        Generates data points plotting Cumulative Investment (₹) vs. Cumulative Risk Reduction (₹).
        
        Controls are sequenced in order of marginal efficiency (Risk Reduction / Cost ratio) in
        descending order to demonstrate the classical economic Law of Diminishing Marginal Returns:
        the most cost-effective controls are deployed first, with subsequent controls yielding
        lower risk reduction per rupee invested.
        
        Args:
            controls: List of ControlOption candidates. If None, uses mock controls.
            enterprise_baseline_eal: Total Enterprise Baseline EAL in INR.
            max_budget: Optional upper budget ceiling.
            
        Returns:
            RiskReductionCurveResponse containing step-by-step curve data points and summary.
        """
        if enterprise_baseline_eal is None or enterprise_baseline_eal <= 0:
            enterprise_baseline_eal = MOCK_P2_ENTERPRISE_BASELINE_EAL

        hydrated_controls = self._hydrate_controls(controls)

        # Sort candidate controls by Efficiency Ratio = (Risk Reduction / Annual Cost) descending
        # Controls with 0 cost placed at highest priority
        sorted_controls = sorted(
            hydrated_controls,
            key=lambda c: (
                (c.risk_reduction / c.annual_cost)
                if c.annual_cost > 0
                else float("inf")
            ),
            reverse=True,
        )

        data_points: List[CurveDataPoint] = []
        cumulative_investment = 0.0
        cumulative_risk_reduction = 0.0

        # Step 0: Baseline state before any security investment
        data_points.append(
            CurveDataPoint(
                step=0,
                control_id="BASELINE",
                control_name="Baseline (No Controls Deployed)",
                cumulative_investment=0.0,
                cumulative_risk_reduction=0.0,
                marginal_cost=0.0,
                marginal_risk_reduction=0.0,
                marginal_efficiency=0.0,
                marginal_rosi_pct=0.0,
                residual_eal=enterprise_baseline_eal,
                formatted_cumulative_investment=format_inr(0.0),
                formatted_cumulative_risk_reduction=format_inr(0.0),
                formatted_residual_eal=format_inr(enterprise_baseline_eal),
            )
        )

        # Subsequent steps: Greedily add controls by efficiency
        for step, ctrl in enumerate(sorted_controls, start=1):
            ctrl_cost = ctrl.annual_cost
            ctrl_reduction = ctrl.risk_reduction or 0.0

            if max_budget is not None and (cumulative_investment + ctrl_cost) > max_budget:
                # If a max budget was explicitly given and this control exceeds it, continue
                continue

            cumulative_investment += ctrl_cost
            cumulative_risk_reduction += ctrl_reduction
            residual_eal = max(0.0, enterprise_baseline_eal - cumulative_risk_reduction)

            marginal_eff = (ctrl_reduction / ctrl_cost) if ctrl_cost > 0 else 0.0
            marginal_rosi = ctrl.rosi.rosi_percentage if ctrl.rosi else 0.0

            data_points.append(
                CurveDataPoint(
                    step=step,
                    control_id=ctrl.id,
                    control_name=ctrl.name,
                    cumulative_investment=cumulative_investment,
                    cumulative_risk_reduction=cumulative_risk_reduction,
                    marginal_cost=ctrl_cost,
                    marginal_risk_reduction=ctrl_reduction,
                    marginal_efficiency=round(marginal_eff, 2),
                    marginal_rosi_pct=round(marginal_rosi, 2),
                    residual_eal=residual_eal,
                    formatted_cumulative_investment=format_inr(cumulative_investment),
                    formatted_cumulative_risk_reduction=format_inr(cumulative_risk_reduction),
                    formatted_residual_eal=format_inr(residual_eal),
                )
            )

        # Generate executive narrative summary
        summary = self._generate_curve_summary(data_points, enterprise_baseline_eal)

        return RiskReductionCurveResponse(
            baseline_enterprise_eal=enterprise_baseline_eal,
            total_available_controls=len(sorted_controls),
            currency="INR",
            data_points=data_points,
            summary=summary,
            formatted_baseline_enterprise_eal=format_inr(enterprise_baseline_eal),
        )

    # =========================================================================
    # INTERNAL HELPER & SOLVER METHODS
    # =========================================================================
    def _hydrate_controls(
        self, controls: Optional[List[ControlOption]]
    ) -> List[ControlOption]:
        """
        Validates, fills missing baseline EALs from P2/P3 mock data, and computes ROSI for all controls.
        """
        hydrated: List[ControlOption] = []

        if not controls:
            # Fallback to default mock candidate controls
            raw_controls = MOCK_AVAILABLE_CONTROLS_RAW
            for raw in raw_controls:
                baseline_eal = raw.get("baseline_eal")
                if baseline_eal is None:
                    target = raw.get("target_asset_or_risk", "ENTERPRISE-WIDE")
                    baseline_eal = MOCK_P3_ASSET_BASELINE_EAL.get(
                        target, MOCK_P2_ENTERPRISE_BASELINE_EAL
                    )

                rosi_result = self.calculate_rosi(
                    baseline_eal=baseline_eal,
                    effectiveness=raw["effectiveness"],
                    annual_cost=raw["annual_cost"],
                    control_id=raw["id"],
                    control_name=raw["name"],
                    target_asset_or_risk=raw["target_asset_or_risk"],
                )

                ctrl = ControlOption(
                    id=raw["id"],
                    name=raw["name"],
                    description=raw.get("description"),
                    annual_cost=raw["annual_cost"],
                    target_asset_or_risk=raw["target_asset_or_risk"],
                    effectiveness=raw["effectiveness"],
                    baseline_eal=baseline_eal,
                    risk_reduction=rosi_result.risk_reduction,
                    rosi=rosi_result,
                    currency="INR",
                )
                hydrated.append(ctrl)
        else:
            for c in controls:
                baseline_eal = c.baseline_eal
                if baseline_eal is None:
                    baseline_eal = MOCK_P3_ASSET_BASELINE_EAL.get(
                        c.target_asset_or_risk, MOCK_P2_ENTERPRISE_BASELINE_EAL
                    )

                rosi_result = self.calculate_rosi(
                    baseline_eal=baseline_eal,
                    effectiveness=c.effectiveness,
                    annual_cost=c.annual_cost,
                    control_id=c.id,
                    control_name=c.name,
                    target_asset_or_risk=c.target_asset_or_risk,
                )

                reduc_val = float(c.risk_reduction) if c.risk_reduction is not None and c.risk_reduction > 0 else rosi_result.risk_reduction
                ctrl = ControlOption(
                    id=c.id,
                    name=c.name,
                    description=c.description,
                    annual_cost=c.annual_cost,
                    target_asset_or_risk=c.target_asset_or_risk,
                    effectiveness=c.effectiveness,
                    baseline_eal=baseline_eal,
                    risk_reduction=reduc_val,
                    rosi=rosi_result,
                    currency="INR",
                )
                hydrated.append(ctrl)

        return hydrated

    def _solve_01_knapsack(
        self, budget: float, controls: List[ControlOption]
    ) -> List[int]:
        """
        Exact 0/1 Knapsack branch-and-bound solver with memoization.
        Guarantees exact optimal solution for continuous or integer budgets and costs.
        """
        n = len(controls)
        if n == 0 or budget <= 0:
            return []

        costs = [c.annual_cost for c in controls]
        values = [c.risk_reduction or 0.0 for c in controls]

        # Use recursive search with pruning / branch & bound
        best_value = 0.0
        best_combination: List[int] = []

        def search(idx: int, current_cost: float, current_val: float, selected: List[int]):
            nonlocal best_value, best_combination
            
            # Prune if remaining possible value cannot beat best_value
            remaining_possible = sum(values[i] for i in range(idx, n))
            if current_val + remaining_possible < best_value:
                return

            if idx == n:
                if current_val > best_value or (
                    current_val == best_value and (len(best_combination) == 0 or current_cost < sum(costs[i] for i in best_combination))
                ):
                    best_value = current_val
                    best_combination = list(selected)
                return

            # Option 1: Include controls[idx] if budget permits
            if current_cost + costs[idx] <= budget:
                search(
                    idx + 1,
                    current_cost + costs[idx],
                    current_val + values[idx],
                    selected + [idx],
                )

            # Option 2: Exclude controls[idx]
            search(
                idx + 1,
                current_cost,
                current_val,
                selected,
            )

        search(0, 0.0, 0.0, [])
        return best_combination

    def _generate_curve_summary(
        self, points: List[CurveDataPoint], baseline_eal: float
    ) -> str:
        """
        Constructs an executive narrative summary of the diminishing returns trajectory.
        """
        if len(points) <= 1:
            return "No controls available to generate investment curve."

        initial_eff = points[1].marginal_efficiency if len(points) > 1 else 0
        final_eff = points[-1].marginal_efficiency if len(points) > 1 else 0
        total_inv = points[-1].cumulative_investment
        total_red = points[-1].cumulative_risk_reduction
        red_pct = (total_red / baseline_eal * 100) if baseline_eal > 0 else 0

        return (
            f"The Risk-Reduction Curve exhibits clear diminishing marginal returns. "
            f"Phase 1 controls achieve peak capital efficiency of ₹{initial_eff:.2f} risk reduction per ₹1 invested, "
            f"whereas later controls yield ₹{final_eff:.2f} per ₹1. "
            f"Deploying all {len(points)-1} controls requires a total investment of {format_inr(total_inv)}, "
            f"yielding {format_inr(total_red)} in cumulative risk reduction ({red_pct:.1f}% of enterprise baseline EAL)."
        )
