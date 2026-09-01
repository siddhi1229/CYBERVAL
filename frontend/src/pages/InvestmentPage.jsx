import React, { useState, useEffect } from 'react';
import {
  TrendingUp,
  DollarSign,
  PieChart,
  Percent,
  Sliders,
  ShieldCheck,
  ArrowRight,
  Sparkles,
  Layers,
  Award,
  AlertTriangle,
  Play
} from 'lucide-react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ReferenceLine
} from 'recharts';
import MetricCard from '../components/common/MetricCard';
import Badge from '../components/common/Badge';
import LoadingSpinner from '../components/common/LoadingSpinner';
import { useTelemetry } from '../context/TelemetryContext';
import { investmentApi } from '../api/investmentApi';
import { NO_DATA } from '../utils/formatters';

const TOOLTIP_STYLE = {
  backgroundColor: '#FFFFFF',
  borderColor: '#E4E7EC',
  borderRadius: '8px',
  fontSize: '11px',
  fontFamily: 'JetBrains Mono',
  color: '#17212B',
  boxShadow: '0 4px 6px -1px rgba(0,0,0,0.08)'
};

export default function InvestmentPage() {
  const { formatCurrency, enterpriseRisk, refreshKey } = useTelemetry();
  const [budgetSlider, setBudgetSlider] = useState(10000000); // Default 1 Crore INR (10M)
  const [optimizationResult, setOptimizationResult] = useState(null);
  const [curveData, setCurveData] = useState(null);
  const [controls, setControls] = useState([]);
  const [loading, setLoading] = useState(true);
  const [optimizing, setOptimizing] = useState(false);
  const [error, setError] = useState(null);

  const baselineEalRaw = enterpriseRisk?.total_expected_annual_loss;

  useEffect(() => {
    async function loadInitialData() {
      try {
        setLoading(true);
        const [ctrlsRes, curveRes, optRes] = await Promise.allSettled([
          investmentApi.getControls(),
          investmentApi.getCurves(budgetSlider, baselineEalRaw),
          investmentApi.optimizeBudget(budgetSlider, baselineEalRaw),
        ]);

        if (ctrlsRes.status === 'fulfilled') setControls(ctrlsRes.value || []);
        if (curveRes.status === 'fulfilled') setCurveData(curveRes.value);
        if (optRes.status === 'fulfilled') setOptimizationResult(optRes.value);
        setError(null);
      } catch (err) {
        console.error('Failed to load investment data:', err);
        setError('Failed to fetch investment optimization engine.');
      } finally {
        setLoading(false);
      }
    }
    loadInitialData();
  }, [refreshKey]);

  const handleRunOptimization = async () => {
    try {
      setOptimizing(true);
      const [optRes, curveRes] = await Promise.allSettled([
        investmentApi.optimizeBudget(budgetSlider, baselineEalRaw),
        investmentApi.getCurves(budgetSlider, baselineEalRaw),
      ]);
      if (optRes.status === 'fulfilled') setOptimizationResult(optRes.value);
      if (curveRes.status === 'fulfilled') setCurveData(curveRes.value);
    } catch (err) {
      console.error('Optimization error:', err);
    } finally {
      setOptimizing(false);
    }
  };

  if (loading) return <LoadingSpinner text="Executing 0/1 Knapsack Portfolio Optimization..." />;

  const rosiDisplay = optimizationResult?.portfolio_rosi_percentage != null
    ? `${Number(optimizationResult.portfolio_rosi_percentage).toFixed(1)}%`
    : NO_DATA;

  const totalRiskReductionDisplay = optimizationResult?.total_risk_reduction != null
    ? formatCurrency(optimizationResult.total_risk_reduction)
    : NO_DATA;

  const totalInvestmentDisplay = optimizationResult?.total_investment != null
    ? formatCurrency(optimizationResult.total_investment)
    : formatCurrency(budgetSlider);

  const remainingBudgetDisplay = optimizationResult?.remaining_budget != null
    ? formatCurrency(optimizationResult.remaining_budget)
    : NO_DATA;

  // Chart data points from curve response
  const chartPoints = (curveData?.data_points || []).map((pt) => ({
    step: pt.step,
    investment: pt.cumulative_investment / 10000000, // Cr
    reduction: pt.cumulative_risk_reduction / 10000000, // Cr
    name: pt.control_name || `Step ${pt.step}`,
  }));

  return (
    <div className="space-y-6">
      
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 rounded-lg cyber-card border-cv-border">
        <div>
          <div className="flex items-center space-x-2">
            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-cv-successBg text-cv-success border border-green-200">
              P5 KNAPSACK OPTIMIZATION ENGINE
            </span>
            <span className="text-xs font-mono text-cv-muted">
              Live Mathematical Optimization (`/api/investment/optimize`)
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-cv-text mt-1 tracking-tight">
            Security Investment & Portfolio ROSI Analysis
          </h1>
          <p className="text-xs sm:text-sm text-cv-muted mt-0.5">
            0/1 Knapsack budget optimizer maximizing enterprise financial risk reduction (EAL reduced) within capital constraints.
          </p>
        </div>

        <button
          onClick={handleRunOptimization}
          disabled={optimizing}
          className="flex items-center space-x-2 px-4 py-2.5 rounded-lg bg-cv-blue text-white font-mono text-xs font-bold hover:bg-blue-700 transition-all shadow-sm disabled:opacity-50"
        >
          <Play className="w-4 h-4" />
          <span>{optimizing ? 'SOLVING KNAPSACK...' : 'OPTIMIZE BUDGET (API)'}</span>
        </button>
      </div>

      {/* Primary KPI Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Allocated Budget"
          value={formatCurrency(budgetSlider)}
          subtitle="Capital ceiling"
          icon={DollarSign}
          variant="cyan"
          technicalBadge="Budget"
          technicalTooltip="Total capital budget allocated for security controls."
        />

        <MetricCard
          title="Committed Capital"
          value={totalInvestmentDisplay}
          subtitle={`Remaining: ${remainingBudgetDisplay}`}
          icon={Layers}
          variant="warning"
          technicalBadge="Investment"
          technicalTooltip="Sum of implementation costs for selected optimal controls."
        />

        <MetricCard
          title="Total Risk Reduction"
          value={totalRiskReductionDisplay}
          subtitle="EAL mitigated in INR"
          icon={TrendingUp}
          variant="success"
          technicalBadge="EAL Saved"
          technicalTooltip="Financial loss avoided through the selected portfolio."
        />

        <MetricCard
          title="Portfolio ROSI"
          value={rosiDisplay}
          subtitle="Return on Security Investment"
          icon={Award}
          variant="critical"
          technicalBadge="ROSI"
          technicalTooltip="ROSI = ((Risk Reduction - Cost) / Cost) × 100"
        />
      </div>

      {/* Budget Slider Card */}
      <div className="cyber-card rounded-lg p-5 border-cv-border space-y-4 font-mono text-xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h3 className="text-sm font-sans font-semibold text-cv-text flex items-center space-x-2">
              <Sliders className="w-4 h-4 text-cv-blue" />
              <span>CAPITAL BUDGET ALLOCATION SLIDER</span>
            </h3>
            <p className="text-xs text-cv-muted font-sans mt-0.5">
              Adjust budget and execute the 0/1 Knapsack optimizer to calculate the highest return portfolio.
            </p>
          </div>
          <div className="px-3 py-1.5 rounded bg-cv-bg border border-cv-border font-bold text-sm text-cv-text">
            {formatCurrency(budgetSlider)}
          </div>
        </div>

        <input
          type="range"
          min="1000000"
          max="50000000"
          step="1000000"
          value={budgetSlider}
          onChange={(e) => setBudgetSlider(Number(e.target.value))}
          className="w-full cursor-pointer accent-cv-blue"
        />
        <div className="flex justify-between text-[11px] text-cv-muted">
          <span>₹10 Lakhs (Min)</span>
          <span>₹1.00 Crore (Standard)</span>
          <span>₹2.50 Crores</span>
          <span>₹5.00 Crores (Max)</span>
        </div>
      </div>

      {/* Diminishing Returns Curve */}
      <div className="cyber-card rounded-lg p-5 border-cv-border space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-cv-border pb-3">
          <div>
            <h3 className="text-sm font-sans font-semibold text-cv-text flex items-center space-x-2">
              <TrendingUp className="w-4 h-4 text-cv-success" />
              <span>DIMINISHING RETURNS RISK REDUCTION CURVE</span>
            </h3>
            <p className="text-xs text-cv-muted">Cumulative Capital Invested (₹ Cr) vs. Cumulative Risk Reduction (₹ Cr)</p>
          </div>
          {curveData?.summary && (
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cv-bg border border-cv-border text-cv-muted max-w-xs truncate">
              {curveData.summary}
            </span>
          )}
        </div>

        {chartPoints.length > 0 ? (
          <div className="h-64 sm:h-72 w-full pt-2">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartPoints} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E4E7EC" vertical={false} />
                <XAxis dataKey="investment" stroke="#94A3B8" fontSize={11} fontFamily="JetBrains Mono" tickFormatter={(v) => `₹${v.toFixed(1)}Cr`} />
                <YAxis stroke="#94A3B8" fontSize={11} fontFamily="JetBrains Mono" tickFormatter={(v) => `₹${v.toFixed(1)}Cr`} />
                <Tooltip
                  contentStyle={TOOLTIP_STYLE}
                  formatter={(val, name) => [`₹${Number(val).toFixed(2)} Cr`, name === 'reduction' ? 'Risk Reduction' : 'Cumulative Cost']}
                />
                <Line type="monotone" dataKey="reduction" stroke="#16A34A" strokeWidth={2.5} dot={{ fill: '#16A34A', r: 4 }} name="reduction" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <div className="py-12 text-center font-mono text-xs text-cv-muted">
            <TrendingUp className="w-8 h-8 mx-auto text-cv-border mb-2" />
            <p>{NO_DATA} (Curve data points not generated)</p>
          </div>
        )}
      </div>

      {/* Selected Portfolio of Controls */}
      <div className="cyber-card rounded-lg border-cv-border p-5 space-y-3">
        <h3 className="text-sm font-sans font-semibold text-cv-text flex items-center justify-between">
          <span className="flex items-center space-x-2">
            <ShieldCheck className="w-4 h-4 text-cv-blue" />
            <span>OPTIMIZED CONTROL PORTFOLIO ({optimizationResult?.selected_controls?.length || 0})</span>
          </span>
          <span className="text-xs font-mono text-cv-muted">Selected by 0/1 Knapsack Solver</span>
        </h3>

        <div className="overflow-x-auto">
          <table className="w-full text-left font-mono text-xs">
            <thead>
              <tr className="border-b border-cv-border text-cv-muted text-[11px]">
                <th className="pb-3">CONTROL ID / NAME</th>
                <th className="pb-3">ANNUAL COST</th>
                <th className="pb-3">EFFECTIVENESS</th>
                <th className="pb-3">RISK REDUCTION</th>
                <th className="pb-3">ROSI (%)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-cv-border">
              {(optimizationResult?.selected_controls || []).map((ctrl, i) => {
                const cId = ctrl.id || `CTRL-${i + 1}`;
                const cName = ctrl.name || `Control #${ctrl.id || i + 1}`;
                const cCost = ctrl.annual_cost != null ? formatCurrency(ctrl.annual_cost) : NO_DATA;
                const cEff = ctrl.effectiveness != null ? `${(ctrl.effectiveness * 100).toFixed(0)}%` : NO_DATA;
                const cRed = ctrl.risk_reduction != null ? formatCurrency(ctrl.risk_reduction) : NO_DATA;
                const cRosi = ctrl.rosi?.rosi_percentage != null ? `${ctrl.rosi.rosi_percentage.toFixed(0)}%` : NO_DATA;

                return (
                  <tr key={cId} className="hover:bg-cv-bg/50">
                    <td className="py-3 font-bold text-cv-text">{cName}</td>
                    <td className="py-3 text-cv-muted">{cCost}</td>
                    <td className="py-3 text-cv-success font-bold">{cEff}</td>
                    <td className="py-3 font-bold text-cv-danger">{cRed}</td>
                    <td className="py-3 font-bold text-cv-blue">{cRosi}</td>
                  </tr>
                );
              })}
              {(!optimizationResult?.selected_controls || optimizationResult.selected_controls.length === 0) && (
                <tr>
                  <td colSpan="5" className="py-8 text-center text-cv-muted">
                    {NO_DATA} (No controls selected under current budget allocation)
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
