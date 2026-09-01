import React, { useState, useEffect } from 'react';
import {
  SlidersHorizontal,
  TrendingDown,
  ShieldCheck,
  DollarSign,
  Zap,
  Sparkles,
  RotateCcw,
  CheckSquare,
  Square,
  ArrowRight,
  ShieldAlert,
  Play
} from 'lucide-react';
import MetricCard from '../components/common/MetricCard';
import Badge from '../components/common/Badge';
import LoadingSpinner from '../components/common/LoadingSpinner';
import { useTelemetry } from '../context/TelemetryContext';
import { simulationApi } from '../api/simulationApi';
import { NO_DATA } from '../utils/formatters';

export default function SimulationPage() {
  const { formatCurrency, enterpriseRisk, refreshKey } = useTelemetry();
  const [controls, setControls] = useState([]);
  const [simBudget, setSimBudget] = useState(5000000); // 50 Lakhs default
  const [iterations, setIterations] = useState(1000);
  const [simulationResult, setSimulationResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [calculating, setCalculating] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function loadControls() {
      try {
        setLoading(true);
        const data = await simulationApi.getControls();
        setControls(data || []);
        setError(null);
      } catch (err) {
        console.error('Failed to load simulation controls:', err);
        setError('Failed to fetch security controls from backend.');
      } finally {
        setLoading(false);
      }
    }
    loadControls();
  }, [refreshKey]);

  const runSimulation = async () => {
    try {
      setCalculating(true);
      const res = await simulationApi.runSimulation(simBudget, iterations);
      setSimulationResult(res);
    } catch (err) {
      console.error('Simulation calculation failed:', err);
    } finally {
      setCalculating(false);
    }
  };

  if (loading) return <LoadingSpinner text="Loading Master Security Controls from PostgreSQL..." />;

  const baselineEal = enterpriseRisk?.total_expected_annual_loss != null
    ? formatCurrency(enterpriseRisk.total_expected_annual_loss)
    : NO_DATA;

  return (
    <div className="space-y-6">
      
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 rounded-lg cyber-card border-cv-border">
        <div>
          <div className="flex items-center space-x-2">
            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-cv-blueLight text-cv-blue border border-blue-200">
              WHAT-IF SIMULATION ENGINE
            </span>
            <span className="text-xs font-mono text-cv-muted">
              Live Monte Carlo Service (`POST /api/simulation/run`)
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-cv-text mt-1 tracking-tight">
            Security Control & Budget Simulation
          </h1>
          <p className="text-xs sm:text-sm text-cv-muted mt-0.5">
            Model the effect of allocated security capital on enterprise loss distribution.
          </p>
        </div>

        <button
          onClick={runSimulation}
          disabled={calculating}
          className="flex items-center space-x-2 px-4 py-2.5 rounded-lg bg-cv-blue text-white font-mono text-xs font-bold hover:bg-blue-700 transition-all shadow-sm disabled:opacity-50"
        >
          <Play className="w-4 h-4" />
          <span>{calculating ? 'RUNNING ITERATIONS...' : 'RUN WHAT-IF SIMULATION'}</span>
        </button>
      </div>

      {/* KPI Comparison Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Baseline Yearly Loss"
          value={baselineEal}
          subtitle="Pre-simulation baseline"
          icon={DollarSign}
          variant="critical"
          technicalBadge="Baseline"
          technicalTooltip="Current enterprise EAL before what-if budget allocation."
        />

        <MetricCard
          title="Simulated Mean Loss"
          value={simulationResult?.mean_loss != null ? formatCurrency(simulationResult.mean_loss) : NO_DATA}
          subtitle={simulationResult ? `${simulationResult.iterations} trials executed` : "Run simulation to calculate"}
          icon={ActivityIcon}
          variant="cyan"
          technicalBadge="Mean"
          technicalTooltip="Simulated mean loss under allocated budget."
        />

        <MetricCard
          title="Simulated P90 Loss"
          value={simulationResult?.p90_loss != null ? formatCurrency(simulationResult.p90_loss) : NO_DATA}
          subtitle={simulationResult ? "90th percentile tail loss" : "Run simulation to calculate"}
          icon={ShieldAlert}
          variant="warning"
          technicalBadge="P90"
          technicalTooltip="10% chance of exceeding this financial loss."
        />

        <MetricCard
          title="Simulated P95 Loss"
          value={simulationResult?.p95_loss != null ? formatCurrency(simulationResult.p95_loss) : NO_DATA}
          subtitle={simulationResult ? "95th percentile worst-case" : "Run simulation to calculate"}
          icon={ShieldAlert}
          variant="danger"
          technicalBadge="P95"
          technicalTooltip="5% chance of exceeding this financial loss."
        />
      </div>

      {/* Simulation Parameters & Active Controls */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Simulation Parameter Inputs */}
        <div className="lg:col-span-4 cyber-card rounded-lg p-5 border-cv-border space-y-4 font-mono text-xs">
          <h3 className="text-sm font-sans font-semibold text-cv-text flex items-center space-x-2">
            <SlidersHorizontal className="w-4 h-4 text-cv-blue" />
            <span>SIMULATION PARAMETERS</span>
          </h3>

          <div className="space-y-2">
            <label className="text-cv-muted font-bold block">
              Budget Allocation (INR): {formatCurrency(simBudget)}
            </label>
            <input
              type="range"
              min="0"
              max="20000000"
              step="500000"
              value={simBudget}
              onChange={(e) => setSimBudget(Number(e.target.value))}
              className="w-full cursor-pointer accent-cv-blue"
            />
            <div className="flex justify-between text-[10px] text-cv-muted">
              <span>₹0</span>
              <span>₹1 Cr</span>
              <span>₹2 Cr</span>
            </div>
          </div>

          <div className="space-y-2 pt-2 border-t border-cv-border">
            <label className="text-cv-muted font-bold block">
              Monte Carlo Iterations: {iterations.toLocaleString()}
            </label>
            <select
              value={iterations}
              onChange={(e) => setIterations(Number(e.target.value))}
              className="w-full p-2 bg-cv-bg border border-cv-border rounded text-cv-text font-mono text-xs"
            >
              <option value={500}>500 Iterations (Fast)</option>
              <option value={1000}>1,000 Iterations (Balanced)</option>
              <option value={5000}>5,000 Iterations (High Precision)</option>
              <option value={10000}>10,000 Iterations (Extensive)</option>
            </select>
          </div>

          <div className="pt-3">
            <button
              onClick={runSimulation}
              disabled={calculating}
              className="w-full py-2.5 rounded bg-cv-blue text-white font-bold hover:bg-blue-700 transition-all flex items-center justify-center space-x-2 disabled:opacity-50"
            >
              <Play className="w-3.5 h-3.5" />
              <span>{calculating ? 'Running Simulation...' : 'Execute Simulation (API)'}</span>
            </button>
          </div>
        </div>

        {/* Master Controls In Scope */}
        <div className="lg:col-span-8 cyber-card rounded-lg p-5 border-cv-border space-y-3">
          <h3 className="text-sm font-sans font-semibold text-cv-text flex items-center justify-between">
            <span className="flex items-center space-x-2">
              <ShieldCheck className="w-4 h-4 text-cv-success" />
              <span>MASTER CONTROLS IN SCOPE ({controls.length})</span>
            </span>
            <span className="text-xs font-mono text-cv-muted">From PostgreSQL `controls` table</span>
          </h3>

          <div className="overflow-x-auto max-h-[400px]">
            <table className="w-full text-left font-mono text-xs">
              <thead>
                <tr className="border-b border-cv-border text-cv-muted text-[11px]">
                  <th className="pb-2">CONTROL NAME</th>
                  <th className="pb-2">DESCRIPTION</th>
                  <th className="pb-2">EFFECTIVENESS</th>
                  <th className="pb-2">STATUS</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-cv-border">
                {controls.map((ctrl) => (
                  <tr key={ctrl.id} className="hover:bg-cv-bg/50">
                    <td className="py-2.5 font-bold text-cv-text">{ctrl.name}</td>
                    <td className="py-2.5 text-cv-muted text-[11px] max-w-xs truncate">{ctrl.description}</td>
                    <td className="py-2.5 text-cv-success font-bold">
                      {(Number(ctrl.effectiveness) * 100).toFixed(0)}%
                    </td>
                    <td className="py-2.5">
                      <Badge variant="success">
                        {ctrl.status?.toUpperCase() || 'ACTIVE'}
                      </Badge>
                    </td>
                  </tr>
                ))}
                {controls.length === 0 && (
                  <tr>
                    <td colSpan="4" className="py-8 text-center text-cv-muted">
                      {NO_DATA}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

      </div>

    </div>
  );
}

function ActivityIcon(props) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M22 12h-2.48a2 2 0 0 0-1.93 1.46l-2.35 8.36a.25.25 0 0 1-.48 0L9.24 2.18a.25.25 0 0 0-.48 0l-2.35 8.36A2 2 0 0 1 4.48 12H2" />
    </svg>
  );
}
