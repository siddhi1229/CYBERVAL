import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ShieldAlert,
  DollarSign,
  TrendingDown,
  AlertTriangle,
  Layers,
  ArrowRight,
  Sparkles,
  ExternalLink,
  Sliders,
  CheckCircle,
  FileText,
  Calendar,
  Info,
  Server,
  Activity
} from 'lucide-react';
import MetricCard from '../components/common/MetricCard';
import Badge from '../components/common/Badge';
import LoadingSpinner from '../components/common/LoadingSpinner';
import CyTooltip from '../components/common/Tooltip';
import { useTelemetry } from '../context/TelemetryContext';
import { executiveApi } from '../api/executiveApi';
import { NO_DATA } from '../utils/formatters';

export default function ExecutiveDashboard() {
  const navigate = useNavigate();
  const { formatCurrency, refreshKey } = useTelemetry();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('contributors');

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const result = await executiveApi.getOverview();
        setData(result);
        setError(null);
      } catch (err) {
        console.error('Failed to load executive overview:', err);
        setError('Unable to load risk data from backend. Please verify that the API service is running.');
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [refreshKey]);

  if (loading) return <LoadingSpinner text="Ingesting live enterprise risk telemetry..." />;
  if (error || !data) {
    return (
      <div className="p-8 text-center text-cv-danger border border-red-200 rounded-lg bg-red-50 font-mono">
        <AlertTriangle className="w-8 h-8 mx-auto mb-2 text-cv-danger" />
        <p>{error || 'No data available.'}</p>
      </div>
    );
  }

  const ealDisplay = data.totalExpectedAnnualLoss != null
    ? formatCurrency(data.totalExpectedAnnualLoss)
    : NO_DATA;

  return (
    <div className="space-y-6">
      
      {/* Top Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 rounded-lg cyber-card border-cv-border">
        <div>
          <div className="flex items-center space-x-2">
            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-cv-blueLight text-cv-blue border border-blue-200">
              EXECUTIVE RISK OVERVIEW
            </span>
            <span className="text-xs font-mono text-cv-muted">
              Live PostgreSQL Baseline · Version: {data.calculationVersion || 'baseline-1'}
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-cv-text mt-1 tracking-tight">
            Cyber Risk & Financial Exposure
          </h1>
          <p className="text-xs sm:text-sm text-cv-muted mt-0.5">
            Real-time financial risk exposure aggregated across all normalized assets and threat models.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={() => navigate('/copilot')}
            className="flex items-center space-x-2 px-3.5 py-2 rounded-lg bg-cv-blueLight border border-blue-200 text-cv-blue hover:bg-blue-100 font-mono text-xs font-semibold transition-all"
          >
            <Sparkles className="w-4 h-4" />
            <span>ASK CYBERVAL</span>
          </button>
          <button
            onClick={() => navigate('/simulation')}
            className="flex items-center space-x-2 px-3.5 py-2 rounded-lg bg-cv-blue text-white hover:bg-blue-700 font-mono text-xs font-semibold shadow-sm transition-all"
          >
            <Sliders className="w-4 h-4" />
            <span>WHAT-IF SIMULATION</span>
          </button>
        </div>
      </div>

      {/* Primary KPI Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        
        {/* Total Expected Annual Loss (EAL) */}
        <MetricCard
          title="Expected Yearly Loss"
          explanation="Statistical annual financial loss from cyber incidents across enterprise assets"
          value={ealDisplay}
          subtitle={`Evaluated across ${data.riskCount || 0} active risks`}
          icon={DollarSign}
          variant="critical"
          technicalBadge="EAL"
          technicalTooltip="Expected Annual Loss (EAL) — sum of (Likelihood × Financial Impact) for all enterprise assets stored in PostgreSQL."
        >
          <div className="mt-2 text-[11px] font-mono text-cv-muted flex items-center justify-between border-t border-cv-border pt-1.5">
            <span>Highest Risk Asset ID:</span>
            <strong className="text-cv-danger">#{data.highestRiskAssetId || 'N/A'}</strong>
          </div>
        </MetricCard>

        {/* Enterprise Risk Score Card (Data Integrity: backend provides no scalar) */}
        <div className="cyber-card rounded-lg p-4 flex flex-col justify-between border-cv-border">
          <div className="flex items-center justify-between text-xs font-mono text-cv-muted">
            <span className="font-bold uppercase tracking-wider text-cv-text">Enterprise Risk Score</span>
            <Badge variant="cyan">FAIR BASELINE</Badge>
          </div>
          <p className="text-[11px] text-cv-muted font-sans mt-1">
            Unified 0–100 enterprise scalar
          </p>
          <div className="my-4 text-center">
            <span className="text-xl font-bold font-mono text-cv-muted italic">
              {NO_DATA}
            </span>
            <p className="text-[10px] text-cv-muted mt-1 font-mono">
              Backend provides financial EAL rather than synthetic score
            </p>
          </div>
          <div className="text-[11px] font-mono text-cv-muted text-center border-t border-cv-border pt-2">
            Primary metric: <strong className="text-cv-text">EAL in INR (₹)</strong>
          </div>
        </div>

        {/* Worst-Case Loss (P95 VaR) */}
        <MetricCard
          title="Worst-Case Loss (P95)"
          explanation="Simulated 95th percentile Value-at-Risk financial exposure"
          value={NO_DATA}
          subtitle="Run Monte Carlo simulation in What-If"
          icon={ShieldAlert}
          variant="warning"
          technicalBadge="P95 VaR"
          technicalTooltip="Requires running simulation engine in the What-If module."
        >
          <div className="text-[11px] font-mono text-cv-muted mt-2 bg-cv-bg p-2 rounded border border-cv-border flex items-center justify-between">
            <span>Simulation:</span>
            <button
              onClick={() => navigate('/simulation')}
              className="text-cv-blue hover:underline font-bold"
            >
              Run Now →
            </button>
          </div>
        </MetricCard>

        {/* Actionable Risk Reduction */}
        <MetricCard
          title="Optimized Reduction"
          explanation="Projected risk reduction achievable through knapsack capital optimization"
          value={NO_DATA}
          subtitle="Available via Investment Optimizer"
          icon={TrendingDown}
          variant="success"
          technicalBadge="ROSI"
          technicalTooltip="Calculated by P5 knapsack optimization engine under allocated budget."
        >
          <div className="flex items-center justify-between text-[11px] font-mono mt-2 pt-1 border-t border-cv-border">
            <span className="text-cv-muted">Knapsack Engine:</span>
            <button
              onClick={() => navigate('/investment')}
              className="text-cv-success hover:underline font-bold"
            >
              Optimize Budget →
            </button>
          </div>
        </MetricCard>

      </div>

      {/* Historical Trend Placeholder (Strictly enforcing DATA INTEGRITY RULE) */}
      <div className="cyber-card rounded-lg p-5 border-cv-border space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-cv-border pb-3">
          <div>
            <h3 className="text-sm font-sans font-semibold text-cv-text flex items-center space-x-2">
              <Activity className="w-4 h-4 text-cv-blue" />
              <span>ENTERPRISE RISK TREND OVER TIME</span>
            </h3>
            <p className="text-xs text-cv-muted">Month-by-month financial exposure trajectory</p>
          </div>
          <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-cv-bg border border-cv-border text-cv-muted">
            Status: Baseline Only
          </span>
        </div>

        <div className="py-12 text-center font-mono space-y-2">
          <Calendar className="w-8 h-8 mx-auto text-cv-muted/50" />
          <p className="text-sm font-bold text-cv-muted">
            {NO_DATA} (Historical tracking inactive in current backend baseline)
          </p>
          <p className="text-xs text-cv-muted max-w-md mx-auto font-sans">
            The platform database records the active snapshot (calculation version: <code className="text-cv-text">{data.calculationVersion}</code>). Historical trend time-series tables are not maintained in the current schema.
          </p>
        </div>
      </div>

      {/* Secondary Information Tabs */}
      <div className="cyber-card rounded-lg border-cv-border overflow-hidden">
        <div className="border-b border-cv-border bg-cv-bg/50 px-5 pt-3 flex space-x-4 font-mono text-xs">
          <button
            onClick={() => setActiveTab('contributors')}
            className={`pb-3 border-b-2 font-bold transition-all ${
              activeTab === 'contributors'
                ? 'border-cv-blue text-cv-blue'
                : 'border-transparent text-cv-muted hover:text-cv-text'
            }`}
          >
            TOP ASSET RISK CONTRIBUTORS ({data.topRiskContributors.length})
          </button>
          <button
            onClick={() => setActiveTab('services')}
            className={`pb-3 border-b-2 font-bold transition-all ${
              activeTab === 'services'
                ? 'border-cv-blue text-cv-blue'
                : 'border-transparent text-cv-muted hover:text-cv-text'
            }`}
          >
            BUSINESS DEPARTMENTS & SERVICES ({data.criticalBusinessServices.length})
          </button>
        </div>

        <div className="p-5">
          {activeTab === 'contributors' && (
            <div className="overflow-x-auto">
              <table className="w-full text-left font-mono text-xs">
                <thead>
                  <tr className="border-b border-cv-border text-cv-muted text-[11px]">
                    <th className="pb-3 font-semibold">ASSET NAME</th>
                    <th className="pb-3 font-semibold">CRITICALITY</th>
                    <th className="pb-3 font-semibold">INTERNET EXPOSED</th>
                    <th className="pb-3 font-semibold">PRIMARY CVE</th>
                    <th className="pb-3 font-semibold">FINANCIAL IMPACT</th>
                    <th className="pb-3 font-semibold">EXPECTED ANNUAL LOSS</th>
                    <th className="pb-3 font-semibold">ACTION</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-cv-border">
                  {data.topRiskContributors.map((c) => (
                    <tr key={c.id} className="hover:bg-cv-bg/50 transition-colors">
                      <td className="py-3 font-bold text-cv-text">
                        {c.assetName}
                      </td>
                      <td className="py-3">
                        <Badge variant={c.criticality === 'CRITICAL' ? 'critical' : 'warning'}>
                          {c.criticality}
                        </Badge>
                      </td>
                      <td className="py-3">
                        {c.internetExposed ? (
                          <span className="px-2 py-0.5 rounded text-[10px] bg-red-50 text-cv-danger border border-red-200 font-bold">
                            EXPOSED
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 rounded text-[10px] bg-slate-100 text-slate-600 font-medium">
                            INTERNAL
                          </span>
                        )}
                      </td>
                      <td className="py-3 text-cv-blue font-bold">
                        {c.cve}
                      </td>
                      <td className="py-3 text-cv-muted">
                        {formatCurrency(c.financialExposure)}
                      </td>
                      <td className="py-3 font-bold text-cv-danger">
                        {formatCurrency(c.ealContribution)}
                      </td>
                      <td className="py-3">
                        <button
                          onClick={() => navigate('/technical')}
                          className="text-cv-blue hover:underline flex items-center space-x-1"
                        >
                          <span>Inspect</span>
                          <ArrowRight className="w-3 h-3" />
                        </button>
                      </td>
                    </tr>
                  ))}
                  {data.topRiskContributors.length === 0 && (
                    <tr>
                      <td colSpan="7" className="py-8 text-center text-cv-muted">
                        {NO_DATA}
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}

          {activeTab === 'services' && (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 font-mono text-xs">
              {data.criticalBusinessServices.map((s) => (
                <div key={s.id} className="p-4 rounded-lg bg-cv-bg border border-cv-border space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-sm text-cv-text">{s.name}</span>
                    <Server className="w-4 h-4 text-cv-blue" />
                  </div>
                  <div className="flex justify-between text-cv-muted pt-2 border-t border-cv-border">
                    <span>Total Assets:</span>
                    <strong className="text-cv-text">{s.assetCount}</strong>
                  </div>
                  <div className="flex justify-between text-cv-muted">
                    <span>Critical Assets:</span>
                    <strong className="text-cv-danger">{s.criticalAssets}</strong>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

    </div>
  );
}
