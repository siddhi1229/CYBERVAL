"""Monte Carlo annual-loss simulation.

Model (per asset, per simulated year):

    N ~ Poisson(lambda)                 lambda = annual_incident_probability
                                                 * frequency_scale
    severity_k ~ Lognormal(mu, sigma)   mu = ln(deterministic financial_impact)
                                        sigma = impact.severity_lognormal_sigma
                                        each draw capped at
                                        financial_impact * severity_cap_multiplier
    annual_loss = sum_{k=1..N} severity_k     (0 when N == 0)

Running this for many iterations produces an annual-loss distribution. From it:

    mean / median
    P50, P90, P95, P99  - percentiles of the annual-loss distribution
    VaR95 = P95         - the loss level that annual loss exceeds only 5% of years
    VaR99 = P99         - ... exceeded only 1% of years
    ES95  (TVaR)        - mean loss in the worst 5% of years

Nothing here is hardcoded: every parameter is read from ``RiskEngineConfig`` and
the RNG is seeded (``monte_carlo.seed`` + a per-asset offset) so results are
reproducible while still being genuine samples.

Aggregation: each asset is simulated once against its own seeded RNG; the raw
per-year loss vectors are summed element-wise to build business-service and
enterprise annual-loss distributions. This counts each asset exactly once
(no double counting) and assumes asset loss events are independent - a stated
limitation, since a shared root cause (e.g. the PAYMENT-API-01 scenario) can
correlate several assets in reality.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from app.services.risk.config import RiskEngineConfig


@dataclass
class MonteCarloResult:
    iterations: int
    mean: float
    median: float
    percentiles: dict[str, float]
    var95: float
    var99: float
    probability_of_loss: float
    expected_shortfall_95: float
    max_simulated: float

    @property
    def p50(self) -> float:
        return self.percentiles.get("p50", self.median)

    @property
    def p90(self) -> float:
        return self.percentiles.get("p90", 0.0)

    @property
    def p95(self) -> float:
        return self.percentiles.get("p95", 0.0)

    @property
    def p99(self) -> float:
        return self.percentiles.get("p99", 0.0)

    def as_dict(self) -> dict[str, object]:
        return {
            "iterations": self.iterations,
            "mean": self.mean,
            "median": self.median,
            "percentiles": self.percentiles,
            "p50": self.p50,
            "p90": self.p90,
            "p95": self.p95,
            "p99": self.p99,
            "var95": self.var95,
            "var99": self.var99,
            "probability_of_loss": self.probability_of_loss,
            "expected_shortfall_95": self.expected_shortfall_95,
            "max_simulated": self.max_simulated,
        }


@dataclass
class AssetSimulation:
    asset_id: int
    losses: np.ndarray = field(repr=False)
    result: MonteCarloResult


def summarize(losses: np.ndarray, config: RiskEngineConfig) -> MonteCarloResult:
    iters = int(losses.shape[0])
    pct_levels = config.monte_carlo.percentiles
    pct_values = np.percentile(losses, pct_levels)
    percentiles = {f"p{int(level)}": float(val) for level, val in zip(pct_levels, pct_values)}

    p95 = percentiles.get("p95")
    if p95 is None:
        p95 = float(np.percentile(losses, 95))
        percentiles["p95"] = p95
    p99 = percentiles.get("p99")
    if p99 is None:
        p99 = float(np.percentile(losses, 99))
        percentiles["p99"] = p99

    tail = losses[losses >= p95]
    es95 = float(tail.mean()) if tail.size else float(p95)

    return MonteCarloResult(
        iterations=iters,
        mean=float(losses.mean()),
        median=float(np.median(losses)),
        percentiles=percentiles,
        var95=float(p95),
        var99=float(p99),
        probability_of_loss=float((losses > 0).mean()),
        expected_shortfall_95=es95,
        max_simulated=float(losses.max()),
    )


def simulate_asset_losses(
    annual_probability: float,
    financial_impact: float,
    config: RiskEngineConfig,
    seed_offset: int = 0,
    iterations: int | None = None,
) -> np.ndarray:
    mc = config.monte_carlo
    iters = int(iterations or mc.iterations)
    rng = np.random.default_rng(mc.seed + seed_offset)

    if financial_impact <= 0.0 or annual_probability <= 0.0:
        return np.zeros(iters, dtype=float)

    lam = max(annual_probability * mc.frequency_scale, 0.0)
    counts = rng.poisson(lam, size=iters)
    total_events = int(counts.sum())
    if total_events == 0:
        return np.zeros(iters, dtype=float)

    # Mean-preserving lognormal: E[severity] == deterministic financial_impact,
    # so the Monte Carlo mean annual loss reconciles with the analytic EAL
    # (annual_incident_probability * financial_impact) while the distribution
    # still carries a realistic right tail.
    sigma = max(config.impact.severity_lognormal_sigma, 1e-6)
    mu = np.log(financial_impact) - 0.5 * sigma * sigma
    severities = rng.lognormal(mean=mu, sigma=sigma, size=total_events)
    cap = financial_impact * config.impact.severity_cap_multiplier
    np.clip(severities, 0.0, cap, out=severities)

    iteration_index = np.repeat(np.arange(iters), counts)
    losses = np.bincount(iteration_index, weights=severities, minlength=iters)
    return losses.astype(float)


def simulate_asset(
    asset_id: int,
    annual_probability: float,
    financial_impact: float,
    config: RiskEngineConfig,
    iterations: int | None = None,
) -> AssetSimulation:
    losses = simulate_asset_losses(
        annual_probability,
        financial_impact,
        config,
        seed_offset=asset_id,
        iterations=iterations,
    )
    return AssetSimulation(asset_id=asset_id, losses=losses, result=summarize(losses, config))


def aggregate_simulations(
    simulations: list[AssetSimulation], config: RiskEngineConfig
) -> MonteCarloResult:
    if not simulations:
        return summarize(np.zeros(1, dtype=float), config)
    length = min(sim.losses.shape[0] for sim in simulations)
    stacked = np.sum([sim.losses[:length] for sim in simulations], axis=0)
    return summarize(stacked, config)
