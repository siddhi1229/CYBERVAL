"""Explainable baseline likelihood model.

likelihood_score (0-1)  = normalised weighted sum of the 8 risk factors.
                          An ordinal exposure index. NOT a probability.

annual_incident_probability (0-1)
                        = floor + (cap - floor) * likelihood_score ** gamma
                          A documented monotonic transform of the score into an
                          annualised probability. This is an ASSUMPTION, not a
                          statistically calibrated rate - there is no historical
                          incident dataset for this enterprise to calibrate on.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.services.risk.config import RiskEngineConfig
from app.services.risk.signals import FACTOR_NAMES


@dataclass
class LikelihoodResult:
    likelihood_score: float
    annual_incident_probability: float
    weighted_contributions: dict[str, float]  # normalised weight * factor value
    normalised_weights: dict[str, float]
    factors: dict[str, float]

    def as_dict(self) -> dict[str, object]:
        return {
            "likelihood_score": self.likelihood_score,
            "annual_incident_probability": self.annual_incident_probability,
            "weighted_contributions": self.weighted_contributions,
            "normalised_weights": self.normalised_weights,
            "factors": self.factors,
        }


def compute_likelihood(factors: dict[str, float], config: RiskEngineConfig) -> LikelihoodResult:
    cfg = config.likelihood
    raw_weights = {name: float(cfg.factor_weights.get(name, 0.0)) for name in FACTOR_NAMES}
    total_weight = sum(raw_weights.values()) or 1.0
    norm_weights = {name: w / total_weight for name, w in raw_weights.items()}

    contributions = {
        name: norm_weights[name] * max(0.0, min(1.0, float(factors.get(name, 0.0))))
        for name in FACTOR_NAMES
    }
    likelihood_score = max(0.0, min(1.0, sum(contributions.values())))

    floor = cfg.annual_probability_floor
    cap = cfg.annual_probability_cap
    gamma = cfg.annual_probability_gamma
    annual_probability = floor + (cap - floor) * (likelihood_score ** gamma)
    annual_probability = max(0.0, min(1.0, annual_probability))

    return LikelihoodResult(
        likelihood_score=likelihood_score,
        annual_incident_probability=annual_probability,
        weighted_contributions=contributions,
        normalised_weights=norm_weights,
        factors={name: float(factors.get(name, 0.0)) for name in FACTOR_NAMES},
    )
