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
  Percent
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Cell
} from 'recharts';
import MetricCard from '../components/common/MetricCard';
import Badge from '../components/common/Badge';
import LoadingSpinner from '../components/common/LoadingSpinner';
import { useTelemetry } from '../context/TelemetryContext';
import { simulationApi } from '../api/simulationApi';

const TOOLTIP_STYLE = {
  backgroundColor: '#FFFFFF',
  borderColor: '#E4E7EC',
  borderRadius: '8px',
  fontSize: '11px',
  fontFamily: 'JetBrains Mono',
  color: '#17212B',
  boxShadow: '0 4px 6px -1px rgba(0,0,0,0.08)'
};

export default function SimulationPage() {
  const { formatCurrency, refreshKey } = useTelemetry();
  const [controls, setControls] = useState([]);
  const [enabledIds, setEnabledIds] = useState(['ctrl_mfa', 'ctrl_patching', 'ctrl_segmentation']);
  const [simulationResult, setSimulationResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [calculating, setCalculating] = useState(false);

  useEffect(() => {
    async function loadControls() {
      try {
        setLoading(true);
        const data = await simulationApi.getControls();
        setControls(data);
      } catch (err) {
        console.error('Failed to load simulation controls:', err);
      } finally {
        setLoading(false);
      }
    }
    loadControls();
  }, [refreshKey]);

  useEffect(() => {
    async function runSim() {
      try {
        setCalculating(true);
        const res = await simulationApi.calculateScenario(enabledIds);
        setSimulationResult(res);
      } catch (err) {
        console.error('Simulation calculation failed:', err);
      } finally {
        setCalculating(false);
      }
    }
    runSim();
  }, [enabledIds]);

  const toggleControl = (id) => {
    setEnabledIds(prev =>
      prev.includes(id) ? prev.filter(c => c !== id) : [...prev, id]
    );
  };

  const applyPreset = (presetType) => {
    if (presetType === 'all') {
      setEnabledIds(controls.map(c => c.id));
    } else if (presetType === 'recommended') {
      setEnabledIds(['ctrl_mfa', 'ctrl_patching', 'ctrl_segmentation']);
    } else if (presetType === 'identity') {
      setEnabledIds(['ctrl_mfa', 'ctrl_pam']);
    } else if (presetType === 'clear') {
      setEnabledIds([]);
    }
  };

  if (loading) return <LoadingSpinner text="Initializing What-If Monte Carlo Engine..." />;

  const comparisonBarData = simulationResult ? [
    { name: 'Risk Score (0-100)', Before: simulationResult.before.riskScore, After: simulationResult.after.riskScore, unit: 'pts' },
    { name: 'Expected Annual Loss', Before: simulationResult.before.eal, After: simulationResult.after.eal, unit: '₹ Cr' },
    { name: 'P95 Catastrophe VaR', Before: simulationResult.before.p95Loss, After: simulationResult.after.p95Loss, unit: '₹ Cr' },
  ] : [];

  return (
    <div className="space-y-6">
      
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 rounded-lg cyber-card border-cv-border">
        <div>
          <div className="flex items-center space-x-2">
            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-cv-blueLight text-cv-blue border border-blue-200">
              WHAT-IF RISK SIMULATOR
            </span>
            <span className="text-xs font-mono text-cv-muted">
              Deterministic & Stochastic Control Modeling • ROSI Optimization
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-cv-text mt-1 tracking-tight">
            Security Control Simulation & ROSI Forecasting
          </h1>
          <p className="text-xs sm:text-sm text-cv-muted mt-0.5">
            Test security investment scenarios, calculate EAL reduction, and evaluate Return on Security Investment (ROSI).
          </p>
        </div>

        {/* Preset Buttons */}
        <div className="flex flex-wrap items-center gap-2 font-mono text-xs">
          <button
            onClick={() => applyPreset('recommended')}
            className="px-3 py-1.5 rounded-lg bg-cv-successBg text-cv-success border border-green-200 hover:bg-green-100 font-bold transition-all"
          >
            Recommended Top 3
          </button>
          <button
            onClick={() => applyPreset('all')}
            className="px-3 py-1.5 rounded-lg bg-cv-blueLight text-cv-blue border border-blue-200 hover:bg-blue-100 font-bold transition-all"
          >
            Full Zero Trust
          </button>
          <button
            onClick={() => applyPreset('clear')}
            className="p-1.5 rounded-lg bg-cv-bg text-cv-muted border border-cv-border hover:text-cv-text"
            title="Reset All Controls"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Primary Before vs After KPI Grid */}
      {simulationResult && (
        <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
          
          <MetricCard
            title="Risk Score Delta"
            value={`${simulationResult.before.riskScore} → ${simulationResult.after.riskScore}`}
            unit="pts"
            subtitle={`-${simulationResult.before.riskScore - simulationResult.after.riskScore} Pts Reduction`}
            delta={-(simulationResult.before.riskScore - simulationResult.after.riskScore)}
            deltaType="negative_is_good"
            icon={ShieldAlert}
            variant="cyan"
            badge="SCORE"
          />

          <MetricCard
            title="EAL Reduction"
            value={formatCurrency(simulationResult.reduction)}
            subtitle={`From ${formatCurrency(simulationResult.before.eal)} to ${formatCurrency(simulationResult.after.eal)}`}
            delta={-simulationResult.reduction}
            deltaType="negative_is_good"
            icon={TrendingDown}
            variant="success"
            badge="ANNUAL SAVINGS"
          />

          <MetricCard
            title="Implementation Cost"
            value={formatCurrency(simulationResult.cost)}
            subtitle={`${simulationResult.enabledControlsCount} Controls Active`}
            icon={DollarSign}
            variant="warning"
            badge="CAPEX + OPEX"
          />

          <MetricCard
            title="Return on Investment"
            value={`${simulationResult.rosi}%`}
            subtitle={`ROSI = (Risk Reduction - Cost) / Cost`}
            icon={Percent}
            variant="purple"
            badge="ROSI"
          />

          <MetricCard
            title="Payback Period"
            value={`${simulationResult.paybackMonths} Mo`}
            subtitle="Time to Recover Investment"
            icon={Zap}
            variant="default"
            badge="PAYBACK"
          />

        </div>
      )}

      {/* Main Simulation Workspace */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left 2 Cols: Interactive Control Knobs */}
        <div className="lg:col-span-2 cyber-card rounded-lg p-5 border-cv-border space-y-4">
          <div className="border-b border-cv-border pb-3 flex items-center justify-between">
            <div>
              <h3 className="text-sm font-sans font-semibold text-cv-text flex items-center space-x-2">
                <SlidersHorizontal className="w-4 h-4 text-cv-blue" />
                <span>SELECT CONTROLS TO DEPLOY & SIMULATE</span>
              </h3>
              <p className="text-xs text-cv-muted">Toggle initiatives to observe real-time delta on financial risk exposure</p>
            </div>
            <span className="text-xs font-mono text-cv-blue font-bold">
              {enabledIds.length} / {controls.length} Active
            </span>
          </div>

          <div className="space-y-3 font-mono text-xs">
            {controls.map((ctrl) => {
              const isEnabled = enabledIds.includes(ctrl.id);
              return (
                <div
                  key={ctrl.id}
                  onClick={() => toggleControl(ctrl.id)}
                  className={`p-4 rounded-lg border transition-all cursor-pointer flex flex-col sm:flex-row sm:items-center justify-between gap-3 ${
                    isEnabled
                      ? 'bg-cv-blueLight border-blue-200 shadow-card'
                      : 'bg-cv-bg border-cv-border hover:border-slate-300 opacity-75'
                  }`}
                >
                  <div className="flex items-start space-x-3">
                    <div className={`pt-0.5 ${isEnabled ? 'text-cv-blue' : 'text-cv-muted'}`}>
                      {isEnabled ? <CheckSquare className="w-5 h-5" /> : <Square className="w-5 h-5" />}
                    </div>
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className={`font-bold font-sans text-sm ${isEnabled ? 'text-cv-text' : 'text-cv-muted'}`}>
                          {ctrl.name}
                        </span>
                        <span className="text-[10px] px-2 py-0.5 rounded bg-white border border-cv-border text-cv-muted">
                          {ctrl.category}
                        </span>
                      </div>
                      <p className="text-[11px] text-cv-muted mt-1 max-w-xl">
                        {ctrl.description}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center space-x-4 border-t sm:border-t-0 sm:border-l border-cv-border pt-2 sm:pt-0 sm:pl-4 flex-shrink-0">
                    <div className="text-right">
                      <span className="text-cv-muted text-[10px] block">COST</span>
                      <span className="font-bold text-cv-text">{formatCurrency(ctrl.cost)}</span>
                    </div>
                    <div className="text-right">
                      <span className="text-cv-muted text-[10px] block">EAL DROP</span>
                      <span className="font-bold text-cv-success">-{formatCurrency(ctrl.riskReduction)}</span>
                    </div>
                    <div className="text-right">
                      <span className="text-cv-muted text-[10px] block">SCORE</span>
                      <span className="font-bold text-cv-blue">{ctrl.riskScoreImpact} pts</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Col: Before vs After Comparison & Summary */}
        <div className="cyber-card rounded-lg p-5 border-cv-border space-y-4 flex flex-col justify-between">
          <div className="border-b border-cv-border pb-3">
            <h3 className="text-sm font-sans font-semibold text-cv-text flex items-center space-x-2">
              <Sparkles className="w-4 h-4 text-cv-blue" />
              <span>SIMULATION COMPARATIVE ANALYSIS</span>
            </h3>
            <p className="text-xs text-cv-muted">Pre-mitigation vs Post-mitigation metrics</p>
          </div>

          <div className="h-56 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={comparisonBarData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E4E7EC" vertical={false} />
                <XAxis dataKey="name" stroke="#94A3B8" fontSize={10} fontFamily="JetBrains Mono" />
                <YAxis stroke="#94A3B8" fontSize={10} fontFamily="JetBrains Mono" />
                <Tooltip contentStyle={TOOLTIP_STYLE} />
                <Bar dataKey="Before" fill="#DC2626" name="Current Baseline" radius={[4, 4, 0, 0]} />
                <Bar dataKey="After" fill="#16A34A" name="Simulated Post-Control" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {simulationResult && (
            <div className="p-3.5 rounded-lg bg-cv-bg border border-cv-border space-y-2 font-mono text-xs">
              <div className="flex justify-between text-cv-muted">
                <span>Baseline EAL:</span>
                <span className="font-bold text-cv-danger">{formatCurrency(simulationResult.before.eal)}</span>
              </div>
              <div className="flex justify-between text-cv-muted">
                <span>Simulated EAL:</span>
                <span className="font-bold text-cv-success">{formatCurrency(simulationResult.after.eal)}</span>
              </div>
              <div className="flex justify-between text-cv-muted border-t border-cv-border pt-1">
                <span>Net Risk Reduction:</span>
                <span className="font-bold text-cv-blue">{formatCurrency(simulationResult.reduction)}</span>
              </div>
              <div className="flex justify-between text-cv-muted">
                <span>Total Program Cost:</span>
                <span className="font-bold text-cv-warning">{formatCurrency(simulationResult.cost)}</span>
              </div>
              <div className="flex justify-between text-cv-muted border-t border-cv-border pt-1">
                <span>Net Economic Gain:</span>
                <span className="font-bold text-cv-success">
                  {formatCurrency(simulationResult.reduction - simulationResult.cost)}
                </span>
              </div>
            </div>
          )}

          <div className="p-3 rounded-lg bg-cv-successBg border border-green-200 text-[11px] font-mono text-cv-success">
            ✓ <strong>Board Ready Summary:</strong> Deploying the selected security controls yields an aggregate return of <strong>{simulationResult?.rosi}%</strong>, recovering full capital outlay within <strong>{simulationResult?.paybackMonths} months</strong>.
          </div>
        </div>

      </div>

    </div>
  );
}
