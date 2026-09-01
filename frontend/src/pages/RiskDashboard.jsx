import React, { useState, useEffect } from 'react';
import {
  BarChart3,
  TrendingDown,
  ShieldAlert,
  Sliders,
  DollarSign,
  Activity,
  AlertCircle,
  Play
} from 'lucide-react';
import MetricCard from '../components/common/MetricCard';
import LoadingSpinner from '../components/common/LoadingSpinner';
import Badge from '../components/common/Badge';
import { useTelemetry } from '../context/TelemetryContext';
import { riskApi } from '../api/riskApi';
import { simulationApi } from '../api/simulationApi';
import { NO_DATA } from '../utils/formatters';

export default function RiskDashboard() {
  const { formatCurrency, refreshKey } = useTelemetry();
  const [enterpriseRisk, setEnterpriseRisk] = useState(null);
  const [assetRisks, setAssetRisks] = useState([]);
  const [simulationResult, setSimulationResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [simulating, setSimulating] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function loadRiskData() {
      try {
        setLoading(true);
        const [entRes, assetsRes] = await Promise.all([
          riskApi.getEnterpriseRisk(),
          riskApi.getAssetRisks(),
        ]);
        setEnterpriseRisk(entRes);
        setAssetRisks(assetsRes || []);
        setError(null);
      } catch (err) {
        console.error('Error loading risk data:', err);
        setError('Failed to fetch quantitative risk baseline from backend.');
      } finally {
        setLoading(false);
      }
    }
    loadRiskData();
  }, [refreshKey]);

  const handleRunSimulation = async () => {
    try {
      setSimulating(true);
      const res = await simulationApi.runSimulation(0, 1000);
      setSimulationResult(res);
    } catch (err) {
      console.error('Failed to run simulation:', err);
    } finally {
      setSimulating(false);
    }
  };

  if (loading) return <LoadingSpinner text="Loading quantitative risk data from PostgreSQL..." />;
  if (error) {
    return (
      <div className="p-8 text-center text-cv-danger border border-red-200 rounded-lg bg-red-50 font-mono">
        <ShieldAlert className="w-8 h-8 mx-auto mb-2 text-cv-danger" />
        <p>{error}</p>
      </div>
    );
  }

  const totalEalDisplay = enterpriseRisk?.total_expected_annual_loss != null
    ? formatCurrency(enterpriseRisk.total_expected_annual_loss)
    : NO_DATA;

  return (
    <div className="space-y-6">
      
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 rounded-lg cyber-card border-cv-border">
        <div>
          <div className="flex items-center space-x-2">
            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-cv-blueLight text-cv-blue border border-blue-200">
              FAIR RISK QUANTIFICATION
            </span>
            <span className="text-xs font-mono text-cv-muted">
              PostgreSQL Stored Risks • Version: {enterpriseRisk?.calculation_version || 'baseline-1'}
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-cv-text mt-1 tracking-tight">
            Quantitative Risk Analysis & Simulation
          </h1>
          <p className="text-xs sm:text-sm text-cv-muted mt-0.5">
            Asset-by-asset Likelihood, Financial Impact, and Expected Annual Loss modeling.
          </p>
        </div>

        <button
          onClick={handleRunSimulation}
          disabled={simulating}
          className="flex items-center space-x-2 px-4 py-2 rounded-lg bg-cv-blue text-white font-mono text-xs font-bold hover:bg-blue-700 transition-all shadow-sm disabled:opacity-50"
        >
          <Play className="w-4 h-4" />
          <span>{simulating ? 'RUNNING MONTE CARLO...' : 'EXECUTE SIMULATION (API)'}</span>
        </button>
      </div>

      {/* Primary KPI Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Total Expected Loss"
          value={totalEalDisplay}
          subtitle={`Aggregated across ${enterpriseRisk?.risk_count || 0} risks`}
          icon={DollarSign}
          variant="critical"
          technicalBadge="EAL"
          technicalTooltip="Expected Annual Loss stored in the database."
        />

        <MetricCard
          title="Mean Loss (Simulated)"
          value={simulationResult?.mean_loss != null ? formatCurrency(simulationResult.mean_loss) : NO_DATA}
          subtitle={simulationResult ? `${simulationResult.iterations} iterations` : "Execute simulation above"}
          icon={Activity}
          variant="cyan"
          technicalBadge="Mean"
          technicalTooltip="Result from POST /api/simulation/run"
        />

        <MetricCard
          title="P90 VaR Loss"
          value={simulationResult?.p90_loss != null ? formatCurrency(simulationResult.p90_loss) : NO_DATA}
          subtitle={simulationResult ? "10% chance of exceeding" : "Execute simulation above"}
          icon={ShieldAlert}
          variant="warning"
          technicalBadge="P90"
          technicalTooltip="90th percentile loss scenario."
        />

        <MetricCard
          title="P95 VaR Loss"
          value={simulationResult?.p95_loss != null ? formatCurrency(simulationResult.p95_loss) : NO_DATA}
          subtitle={simulationResult ? "5% chance of exceeding" : "Execute simulation above"}
          icon={ShieldAlert}
          variant="danger"
          technicalBadge="P95"
          technicalTooltip="95th percentile worst-case scenario."
        />
      </div>

      {/* FAIR Loss Factor Breakdown Note */}
      <div className="cyber-card rounded-lg p-5 border-cv-border space-y-2">
        <h3 className="text-sm font-sans font-semibold text-cv-text flex items-center space-x-2">
          <BarChart3 className="w-4 h-4 text-cv-blue" />
          <span>FAIR LOSS FACTOR DECOMPOSITION</span>
        </h3>
        <div className="p-4 rounded bg-cv-bg text-center font-mono text-xs text-cv-muted border border-cv-border">
          <p className="font-bold text-cv-text">{NO_DATA}</p>
          <p className="mt-1">
            The backend database stores total asset <code className="text-cv-blue">financial_impact</code> and <code className="text-cv-blue">expected_annual_loss</code>. Sub-factor categories (reputation, regulatory fines, productivity) are not stored in the current schema.
          </p>
        </div>
      </div>

      {/* Asset Risk Quantification Table */}
      <div className="cyber-card rounded-lg border-cv-border p-5 space-y-3">
        <h3 className="text-sm font-sans font-semibold text-cv-text flex items-center justify-between">
          <span className="flex items-center space-x-2">
            <DollarSign className="w-4 h-4 text-cv-blue" />
            <span>QUANTIFIED ASSET RISKS ({assetRisks.length})</span>
          </span>
          <span className="text-xs font-mono text-cv-muted">Sorted by EAL Descending</span>
        </h3>

        <div className="overflow-x-auto">
          <table className="w-full text-left font-mono text-xs">
            <thead>
              <tr className="border-b border-cv-border text-cv-muted text-[11px]">
                <th className="pb-3">RISK ID</th>
                <th className="pb-3">ASSET ID</th>
                <th className="pb-3">LIKELIHOOD</th>
                <th className="pb-3">FINANCIAL IMPACT</th>
                <th className="pb-3">EXPECTED ANNUAL LOSS (EAL)</th>
                <th className="pb-3">CONFIDENCE</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-cv-border">
              {assetRisks.map((r) => (
                <tr key={r.id} className="hover:bg-cv-bg/50 transition-colors">
                  <td className="py-3 font-bold text-cv-text">#{r.id}</td>
                  <td className="py-3 text-cv-blue font-bold">Asset #{r.asset_id}</td>
                  <td className="py-3 text-cv-muted">{(Number(r.likelihood) * 100).toFixed(1)}%</td>
                  <td className="py-3 text-cv-muted">{formatCurrency(r.financial_impact)}</td>
                  <td className="py-3 font-bold text-cv-danger">{formatCurrency(r.expected_annual_loss)}</td>
                  <td className="py-3 text-cv-muted">{(Number(r.confidence) * 100).toFixed(0)}%</td>
                </tr>
              ))}
              {assetRisks.length === 0 && (
                <tr>
                  <td colSpan="6" className="py-8 text-center text-cv-muted">
                    {NO_DATA}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  );
}
