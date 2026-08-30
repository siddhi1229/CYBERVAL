# CYBERVAL P2 — Cyber Risk Quantification Engine

The P2 engine converts P1's normalized security telemetry (PostgreSQL, the single
source of truth) into **financial** cyber risk. It creates no new dataset and does
not re-implement ingestion — it is strictly a consumer of P1 data.

```
P1 security telemetry (assets, vulns, KEV, SIEM, IAM, EDR, CSPM, controls, threats,
                       business services)
        │
        ▼
 risk signal extraction        (8 factors, each normalised 0–1)   signals.py
        │
        ▼
 likelihood model              likelihood_score (0–1, ordinal)     likelihood.py
        │                      annual_incident_probability (0–1)
        ▼
 financial impact (INR)        6 cost components                   impact.py
        │
        ▼
 Expected Annual Loss          EAL = P(incident) × financial_impact engine.py
        │
        ▼
 Monte Carlo simulation        annual-loss distribution            monte_carlo.py
        │                      mean / P50 / P90 / P95 / P99
        ▼
 VaR95 / VaR99  +  risk drivers  +  control effectiveness / residual risk
        │
        ▼
 aggregation: asset → business service → department → enterprise
```

Everything a calculation depends on is a **documented, overridable assumption**
in `backend/app/services/risk/config.py` (`RiskEngineConfig`). Nothing is
hardcoded at a call site. Override per request via `config_overrides` on
`POST /api/risk/calculate`, or programmatically with
`RiskEngine(RiskEngineConfig(**overrides))`.

> **Calibration disclaimer.** There is no historical incident dataset for this
> enterprise. The probability and cost parameters are transparent planning
> assumptions, **not statistically calibrated rates**. The engine never claims
> otherwise.

---

## 1. Data consumed from P1

| Signal domain | P1 tables / fields |
|---|---|
| Asset context | `assets.criticality`, `internet_exposed`, `business_value`, `asset_type`, `department`, `business_service_id` |
| Business service | `business_services.criticality`, `annual_revenue` |
| Vulnerabilities | `vulnerabilities.cvss_score`, `severity`, `known_exploited` (CISA KEV), `known_ransomware_use`, `status` |
| SIEM | `security_events.event_type`, `severity`, `technique` (ATT&CK), `observed_at` |
| EDR | `edr_events.indicator`, `severity`, `event_type`, `raw_payload` (e.g. `records_extracted`) |
| CSPM | `cspm_findings.severity`, `status`, `internet_exposed`, `encrypted` |
| IAM | `users.privileged`, `mfa_enabled`, `failed_login_count`, `risky_login` via `iam_access` |
| Threats | `threats.annual_frequency` |
| Controls | `controls.effectiveness`, `status`, `name` (+ `framework_controls`) |

---

## 2. Risk signal extraction (`signals.py`)

Eight factors, each clamped to **[0, 1]**:

| Factor | Derivation (defaults; all in `SignalConfig`) |
|---|---|
| `internet_exposure` | `0.85` if `asset.internet_exposed`; `+0.15` and floor `0.6` if a CSPM finding is internet-exposed; clamp 1. |
| `vulnerability_severity` | `max(cvss_score of open vulns) / 10`. "Open" = status in `{open,in_progress,accepted,new}`. |
| `known_exploitation` | `0` if no KEV vuln; else `kev_base` (0.8), `+ kev_ransomware_uplift` (0.2) if any `known_ransomware_use`. |
| `threat_activity` | `max(SIEM component, enterprise_threat_baseline × attacker_interest[criticality])`. SIEM component = `Σ severity_weight(recent events) / siem_saturation_score` (30-day lookback). `enterprise_threat_baseline = 1 − Π(1 − threats.annual_frequency)`. |
| `endpoint_risk` | `Σ edr_severity_weight / edr_saturation_score`; floored at `0.7` if any high-risk indicator (`credential_dumping`, `data_staging_for_exfiltration`, `reverse_shell`, …). |
| `cloud_posture_risk` | `Σ (cspm_severity_weight + 0.2·exposed + 0.15·unencrypted) / cspm_saturation_score` over open findings. |
| `identity_risk` | `0.6` if any privileged user without MFA `+ 0.25` if any risky login `+ 0.3 · min(max_failed_logins / 15, 1)`; clamp 1. |
| `control_weakness` | `1 − aggregate_control_effectiveness` (see §7). |

`extract_asset_signals` also returns raw **evidence** (counts / flags) used for
explainability and for the financial-impact model, plus:
`active_attack` (hands-on-keyboard ATT&CK technique or high-risk EDR indicator),
`data_bearing` / `records_at_risk`, `exfiltration_detected`.

### PAYMENT-API-01

The engine recognises the coordinated P1 scenario because every input factor
fires at once: internet-exposed (+ open security group), CVE-2021-44228 /
CVE-2024-3094 open with KEV + ransomware flags, CVSS 10.0, `USR-001` privileged
with MFA disabled and 17 failed logins, SIEM `BRUTE_FORCE` (T1110) + C2 (T1071),
EDR `credential_dumping`, CSPM `OPEN_SECURITY_GROUP`. Result: all eight factors
at or near 1.0 → top-ranked asset by a wide margin.

---

## 3. Likelihood model (`likelihood.py`)

```
likelihood_score = Σ_f  normalised_weight[f] · factor[f]              ∈ [0, 1]
```

`normalised_weight` = `factor_weights` (defaults below) rescaled to sum to 1, so
only the ratios matter.

| factor | default weight |
|---|---|
| known_exploitation | 1.8 |
| internet_exposure | 1.4 |
| vulnerability_severity | 1.3 |
| control_weakness | 1.3 |
| identity_risk | 1.2 |
| endpoint_risk | 1.1 |
| threat_activity | 1.0 |
| cloud_posture_risk | 0.9 |

`likelihood_score` is an **ordinal 0–1 exposure index for ranking assets. It is
not a probability.**

```
annual_incident_probability = floor + (cap − floor) · likelihood_score ^ gamma
                            = 0.01 + 0.59 · likelihood_score ^ 1.8            (defaults)
```

A deliberately simple, monotonic, **assumption-based** transform — not a fitted
model. `floor` = irreducible background probability; `cap` = the engine will not
assert an annual incident probability above 0.60 for any single asset from
signals alone; `gamma` > 1 keeps mid-range scores conservative.

---

## 4. Financial impact (`impact.py`) — all INR

```
financial_impact = downtime_cost
                 + data_breach_cost
                 + recovery_cost
                 + regulatory_cost
                 + business_loss
                 + reputational_loss
```

| Component | Formula (defaults in `ImpactConfig`) |
|---|---|
| `downtime_cost` | `downtime_hours × downtime_cost_per_hour[criticality]`. `downtime_hours = expected_downtime_hours[criticality] × m`, where `m = 1 + 0.35·(internet_exposed) + 0.75·(active_attack)`, capped at `×3`. Rates: LOW ₹25k/h, MED ₹150k/h, HIGH ₹500k/h, CRIT ₹1.2M/h. Base hours: 2 / 4 / 8 / 12. |
| `data_breach_cost` | `records_at_risk × breach_cost_per_record_inr` (₹1,800). `records_at_risk` = telemetry (`edr.raw_payload.records_extracted`) if present, else `records_at_risk_by_type` (database 200k, application 25k, cloud 100k, identity 5k, others 0). `× breach_exfiltration_multiplier` (2.0) when staged exfiltration is detected. Non-data-bearing assets = 0. |
| `recovery_cost` | `max(0.15 × asset.business_value, ₹500k)`. |
| `regulatory_cost` | `regulatory_cost_by_service_criticality_inr[business_service.criticality]` — critical ₹50M, high ₹20M, medium ₹5M, low ₹0. **Only applied when `data_breach_cost > 0`** (`regulatory_requires_data_breach = true`). Reference: India **DPDP Act 2023** (max penalty ₹250 crore). |
| `business_loss` | `service_annual_revenue × (business_disruption_days[criticality] × 24 / 8760) × revenue_dependency_factor (0.5)`. Disruption days: 0.5 / 1 / 3 / 5. Falls back to `default_service_annual_revenue_inr` (₹50M) with no linked service. |
| `reputational_loss` | `0.40 × (data_breach_cost + business_loss)`. |

All coefficients are per-request overridable — e.g.
`{"impact": {"breach_cost_per_record_inr": 3000, "reputational_multiplier": 0.6}}`.

---

## 5. Expected Annual Loss (`engine.py`)

```
expected_annual_loss (EAL) = annual_incident_probability × financial_impact
```

The engine returns, per asset: `risk_score`, `likelihood_score`,
`annual_incident_probability`, `financial_impact`, `expected_annual_loss`,
`control_effectiveness`, `inherent_expected_annual_loss`,
`residual_expected_annual_loss`, `risk_reduction_from_controls`, Monte Carlo
percentiles, `risk_drivers`.

### risk_score (0–100)

```
impact_index = clamp(expected_annual_loss / eal_reference_inr, 0, 1)   # ref = ₹40M
risk_score   = 100 · (0.55 · likelihood_score + 0.45 · impact_index)
```

An **ordinal ranking index**, not a probability and not money.

---

## 6. Monte Carlo simulation (`monte_carlo.py`)

Per asset, per simulated year:

```
N          ~ Poisson(λ)                 λ = annual_incident_probability × frequency_scale (1.0)
severity_k ~ Lognormal(μ, σ)            σ = severity_lognormal_sigma (0.55)
                                        μ = ln(financial_impact) − σ²/2   ← mean-preserving
                                        each draw capped at financial_impact × 8
annual_loss = Σ_{k=1..N} severity_k     (0 when N = 0)
```

- **Mean-preserving lognormal:** `E[severity] = financial_impact`, so the Monte
  Carlo **mean annual loss reconciles with the analytic EAL** while the
  distribution still carries a realistic right tail.
- `iterations` default **50,000** (`list_iterations` 20,000 for endpoints that
  score every asset). RNG is `numpy.random.default_rng(seed + asset_id)` →
  **reproducible** but genuine sampling. `seed` is configurable.
- Poisson (not Bernoulli) so an asset can suffer more than one event in a bad
  year.

### Reported statistics

| Stat | Meaning |
|---|---|
| `mean` | average annual loss across all simulated years (≈ analytic EAL) |
| `median` / `p50` | half of simulated years lose less than this |
| `p90` / `p95` / `p99` | the loss level exceeded in only 10% / 5% / 1% of simulated years |
| `var95` | **= p95**. Value at Risk (95%): the annual loss that will be exceeded at most 5% of years. "There is a 95% chance the year's cyber losses are ≤ VaR95." |
| `var99` | **= p99**. Same, 1% tail. |
| `expected_shortfall_95` (TVaR) | the *average* loss in the worst 5% of years (≥ VaR95) — how bad the tail is once you're in it |
| `probability_of_loss` | fraction of simulated years with any loss |

`p95_loss` in API responses is exactly `var95`; `p99_loss` is `var99`.

---

## 7. Control effectiveness & residual risk (`controls.py`)

P1 stores controls globally (no asset link), so each **active** control is
treated as enterprise-wide and its free-text `name` is mapped to the risk-signal
domain it mitigates (`control_domain_keywords`: "mfa"→identity_risk,
"patch"/"vulnerability"→vulnerability_severity, "segmentation"/"network"→
internet_exposure, "endpoint"→endpoint_risk, "cloud"/"posture"→
cloud_posture_risk).

Per control, per asset — **evidence-adjusted effectiveness**:

```
effectiveness = base_effectiveness (P1 controls.effectiveness)
              × status_factor            active 1.0 | inactive 0.25
              × coverage                 domain-specific, from P1 telemetry
              × (1 − telemetry_penalty)  0.5 when the control is observed failing
                                          (e.g. brute force despite an MFA control,
                                           KEV vuln still open despite a patch control)
              × (1 − incident_penalty)   0.3 when the domain signal is already severe (≥0.75)
```

`coverage` examples: MFA control coverage = fraction of privileged users with
access who have MFA enabled; patching coverage = 0.3 if a KEV vuln is open, 0.6
otherwise; segmentation coverage = 0.15 if internet-exposed with an open security
group.

Domain effectiveness (defence-in-depth): `1 − Π(1 − effectiveness_i)` over
controls in that domain.
`aggregate_control_effectiveness` = the same combination over domain values.
`control_weakness` factor = `1 − aggregate_control_effectiveness`.

### Residual vs inherent

- **Residual EAL** = the EAL above — controls already suppress likelihood through
  the `control_weakness` factor.
- **Inherent EAL** = recomputed with `control_weakness` forced to `1.0` (no
  credit for any control).
- `risk_reduction_from_controls = inherent_EAL − residual_EAL`.
- **Per-control marginal reduction** (`marginal_eal_reduction_inr`): the EAL that
  returns if that single control is removed (its domain effectiveness recomputed
  without it). Answers "how much risk reduction does this control provide?"

> **Limitation.** Controls influence risk through one likelihood factor. When an
> asset is already saturated on exposure + active exploitation (PAYMENT-API-01),
> a single control improvement moves residual EAL only modestly — which is the
> intended, honest behaviour: MFA alone does not fix an actively-exploited
> internet-facing box.

---

## 8. Risk drivers (`drivers.py`)

Because `likelihood_score` is a weighted sum, each factor's share of it is exactly
`normalised_weight · factor_value`. Those shares are relabelled to the business
taxonomy (`known_exploited_vulnerability`, `internet_exposure`,
`critical_vulnerability`, `siem_activity`, `edr_activity`,
`cspm_misconfiguration`, `control_weakness`) and `identity_risk` is split into
`mfa_disabled` / `privileged_access` / `failed_login_activity` using the same
sub-weights the signal layer used. Contributions are normalised to **sum to 1.0**.

```json
{ "factor": "known_exploited_vulnerability", "contribution": 0.19 }
```

`impact_drivers` separately ranks the six cost components by share of
`financial_impact`.

Enterprise / group drivers = per-asset drivers pooled with each asset weighted by
its EAL.

---

## 9. Risk aggregation (`engine.py`)

| Scope | Method |
|---|---|
| **Asset** | direct engine output |
| **Business service** | assets grouped by `business_service_id`; EAL = Σ member asset EAL; Monte Carlo = element-wise sum of member annual-loss vectors |
| **Department** | assets grouped by `assets.department`; same method |
| **Enterprise** | Σ over **all** assets; Monte Carlo = element-wise sum of every asset's annual-loss vector |

**No double counting:** every asset is simulated exactly once against its own
seeded RNG; groups sum those same vectors. Business services and departments are
partitions/subsets of the enterprise and are reported **alongside**, never added
to, the enterprise total.

`enterprise.var95` / `var99` come from the summed distribution, so they correctly
capture diversification (the enterprise P95 is **less** than the sum of asset
P95s).

> **Limitation.** Aggregation assumes asset loss events are independent. A shared
> root cause (the PAYMENT-API-01 kill chain touching the gateway, the API and the
> payment DB) would correlate losses and fatten the true enterprise tail. The
> per-asset scenario recognition captures the correlated *signal*; the aggregate
> *tail* is a lower bound.

---

## 10. Persistence

`POST /api/risk/calculate` with `persist: true`:

1. **Upserts** the existing P1 `risks` row per asset —
   `likelihood = annual_incident_probability`, `financial_impact`,
   `expected_annual_loss`, `confidence = 0.50` (planning-assumption confidence,
   not calibrated), `calculation_version = "p2-risk-engine-1.0"`.
2. **Appends** `risk_history` snapshot rows (asset + business_service +
   department + enterprise) tagged with a `run_id`.

### Schema change (the only one P2 makes)

`risk_history` — a new **append-only** table (`backend/app/models/risk_history.py`).
Rationale: `GET /api/risk/trends` needs time series; P1's `risks` table holds one
current row per asset and is summed by `/api/risk/enterprise`, so adding history
rows there would double-count. `risk_history` references no P1 table, alters no P1
table, and is created by `Base.metadata.create_all` (same mechanism as P1's
`init_db.py`). **No P1 model or table is modified.**

---

## 11. API

| Method / path | Purpose |
|---|---|
| `POST /api/risk/calculate` | run the engine (optional `asset_ids`, `iterations`, `persist`, `config_overrides`); upserts `risks`, appends `risk_history` |
| `GET /api/risk/assets` | financial risk for every asset (filters: `min_score`, `business_service`, `department`, `limit`), sorted by EAL |
| `GET /api/risk/assets/{asset_id}` | full breakdown for one asset — signals, likelihood, impact components, Monte Carlo, control evaluations, drivers |
| `GET /api/risk/enterprise` | enterprise + per business-service + per-department risk, with VaR |
| `GET /api/risk/drivers` | top enterprise drivers (`scope=enterprise` or `high_risk_assets`) |
| `GET /api/risk/trends` | historical snapshots from `risk_history` (`scope`, `ref`, `limit`) |

These routes are registered before P1's router in `app.main`, so they supersede
P1's two `/api/risk/*` stubs (`/api/risk/enterprise`, `/api/risk/assets`) without
editing `routers.py`. All other P1 routes are untouched.

### Example — PAYMENT-API-01 (seed: 45 assets, default config, 12k iterations)

```json
{
  "asset_code": "PAYMENT-API-01",
  "asset_name": "Payment API",
  "risk_score": 98.1,
  "likelihood_score": 0.966,
  "annual_incident_probability": 0.564,
  "financial_impact": 155042740.0,
  "expected_annual_loss": 87493144.0,
  "control_effectiveness": 0.262,
  "inherent_expected_annual_loss": 116282055.0,
  "residual_expected_annual_loss": 87493144.0,
  "p95_loss": 363681319.0,
  "p99_loss": 587876036.0,
  "risk_drivers": [
    {"factor": "known_exploited_vulnerability", "contribution": 0.19},
    {"factor": "internet_exposure", "contribution": 0.14},
    {"factor": "critical_vulnerability", "contribution": 0.13},
    {"factor": "edr_activity", "contribution": 0.11},
    {"factor": "siem_activity", "contribution": 0.10}
  ]
}
```

(Exact figures move slightly with `iterations` / seed / seed size — they are
**computed, never hardcoded**. The lowest-risk internal assets score ~2 with EAL
~₹0.07M, i.e. PAYMENT-API-01 is > 40× higher.)

---

## 12. Limitations

1. **Not calibrated.** No historical incident data exists for this enterprise.
   Probabilities and costs are transparent assumptions. `confidence` is a fixed
   planning value, not a measured one.
2. **Likelihood transform is a modelling choice**, not a fitted curve.
3. **Controls act through a single likelihood factor** (§7).
4. **Aggregation assumes asset independence** (§9) — enterprise tail is a lower
   bound under a correlated kill chain.
5. **Global controls.** P1 has no asset↔control mapping, so control applicability
   is inferred from control names and per-asset telemetry.
6. **Records-at-risk** are type-based defaults unless EDR telemetry provides a
   count; they are not derived from actual data-classification inventory.
7. **Regulatory cost** is a single tiered figure keyed to business-service
   criticality, not a jurisdiction-by-jurisdiction penalty model.
8. **Trends** reflect recorded engine runs, not a forecast; a fresh database has
   no history until `POST /api/risk/calculate` has run at least twice.
9. **Monte Carlo severity** uses one lognormal shape for all assets/components;
   component-level distributions would be more faithful.
