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
  Award
} from 'lucide-react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ReferenceLine,
  ReferenceDot
} from 'recharts';
import MetricCard from '../components/common/MetricCard';
import Badge from '../components/common/Badge';
import LoadingSpinner from '../components/common/LoadingSpinner';
import { useTelemetry } from '../context/TelemetryContext';
import { investmentApi } from '../api/investmentApi';

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
  const { formatCurrency, refreshKey } = useTelemetry();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [budgetSlider, setBudgetSlider] = useState(0.5);
  const [optResult, setOptResult] = useState(null);

  useEffect(() => {
    async function loadInvestment() {
      try {
        setLoading(true);
        const result = await investmentApi.getOverview(budgetSlider);
        setData(result);
        if (result && result.selectedControls) {
          setOptResult({
            total_budget: result.totalBudget * 10000000,
            total_investment: result.allocatedBudget * 10000000,
            total_risk_reduction: result.totalRiskReduction * 10000000,
            residual_enterprise_eal: result.residualEal * 10000000,
            portfolio_rosi_percentage: result.portfolioRosi,
            selected_controls: result.selectedControls,
            unselected_controls: result.unselectedControls,
          });
        }
      } catch (err) {
        console.error('Failed to load investment telemetry:', err);
      } finally {
        setLoading(false);
      }
    }
    loadInvestment();
  }, [refreshKey]);

  useEffect(() => {
    let isMounted = true;
    const timer = setTimeout(async () => {
      try {
        const opt = await investmentApi.optimizeBudget(budgetSlider);
        if (isMounted && opt) {
          setOptResult(opt);
        }
      } catch (err) {
        console.warn('Live optimization call failed:', err);
      }
    }, 200);
    return () => {
      isMounted = false;
      clearTimeout(timer);
    };
  }, [budgetSlider]);

  if (loading || !data) return <LoadingSpinner text="Calculating optimal security investment..." />;

  const baselineEal = data.baselineEal || 54.69;
  const dynamicInvestment = optResult 
    ? Number((optResult.total_investment / 10000000).toFixed(2)) 
    : data.allocatedBudget;
  const dynamicReduction = optResult 
    ? Number((optResult.total_risk_reduction / 10000000).toFixed(2)) 
    : data.totalRiskReduction;
  const dynamicRosi = optResult 
    ? Math.round(optResult.portfolio_rosi_percentage ?? data.portfolioRosi) 
    : data.portfolioRosi;
  const dynamicEal = optResult 
    ? Number((optResult.residual_enterprise_eal / 10000000).toFixed(2)) 
    : data.residualEal;

  const initiativesToDisplay = (data.recommendedInitiatives || data.topCandidateControls || []).map((init) => {
    const isSelected = optResult && optResult.selected_controls
      ? optResult.selected_controls.some((sc) => sc.id === init.id)
      : init.status === 'APPROVED_FOR_BUDGET';
    return {
      ...init,
      status: isSelected ? 'APPROVED_FOR_BUDGET' : 'UNDER_REVIEW',
    };
  });

  return (
    <div className="space-y-6">
      
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 rounded-lg cyber-card border-cv-border">
        <div>
          <div className="flex items-center space-x-2">
            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-cv-successBg text-cv-success border border-green-200">
              SECURITY BUDGET
            </span>
            <span className="text-xs font-mono text-cv-muted">
              Where to invest for the best risk reduction
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-cv-text mt-1 tracking-tight">
            Security Investment & Return Analysis
          </h1>
          <p className="text-xs sm:text-sm text-cv-muted mt-0.5">
            Find the optimal security budget and identify which investments deliver the greatest financial risk reduction.
          </p>
        </div>

        <div className="flex items-center space-x-3 font-mono text-xs">
          <div className="px-3.5 py-2 rounded-lg bg-cv-bg border border-cv-border text-cv-text">
            PORTFOLIO RETURN: <strong className="text-cv-success">{dynamicRosi}%</strong>
          </div>
        </div>
      </div>

      {/* Primary KPI Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        
        <MetricCard
          title="Security Budget"
          explanation="Total budget available for security improvements"
          value={formatCurrency(budgetSlider)}
          subtitle={`Allocated: ${formatCurrency(dynamicInvestment)} (${budgetSlider > 0 ? ((dynamicInvestment/budgetSlider)*100).toFixed(0) : 0}%)`}
          icon={DollarSign}
          variant="cyan"
        >
          <div className="w-full bg-cv-bg border border-cv-border rounded-full h-1.5 overflow-hidden mt-2">
            <div
              className="bg-cv-blue h-full transition-all duration-300"
              style={{ width: `${Math.min(100, budgetSlider > 0 ? (dynamicInvestment / budgetSlider) * 100 : 0)}%` }}
            />
          </div>
        </MetricCard>

        <MetricCard
          title="Risk We Can Reduce"
          explanation="How much financial loss we can avoid with this budget"
          value={formatCurrency(dynamicReduction)}
          subtitle={`Yearly loss drops: ${formatCurrency(baselineEal)} → ${formatCurrency(dynamicEal)}`}
          delta={dynamicReduction}
          deltaType="positive_is_good"
          icon={TrendingUp}
          variant="success"
          technicalBadge="EAL Δ"
          technicalTooltip="Expected Annual Loss reduction — how much the yearly loss figure drops after implementing these controls."
        />

        <MetricCard
          title="Return on Investment"
          explanation="Financial benefit compared to what we spend"
          value={`${dynamicRosi}%`}
          subtitle="For every ₹1 spent, losses avoided"
          delta={dynamicRosi}
          deltaType="positive_is_good"
          icon={Percent}
          variant="purple"
          technicalBadge="ROSI"
          technicalTooltip="Return on Security Investment — for every ₹1 invested in these controls, the business avoids this multiple in financial losses."
        />

        <MetricCard
          title="Risk Score Impact"
          explanation="How the overall risk score improves after investment"
          value={`${data.currentRiskScore} → ${Math.max(15, Math.round(data.currentRiskScore - (dynamicReduction / (baselineEal || 10)) * 40))}`}
          unit="pts"
          subtitle={`-${Math.round((dynamicReduction / (baselineEal || 10)) * 40)} point improvement`}
          icon={ShieldCheck}
          variant="warning"
          badge="AFTER INVESTMENT"
        />

      </div>

      {/* Efficient Frontier Chart + Summary Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Budget vs Risk Reduction Curve */}
        <div className="lg:col-span-2 cyber-card rounded-lg p-5 border-cv-border space-y-3">
          <div className="border-b border-cv-border pb-3 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div>
              <h3 className="text-sm font-sans font-semibold text-cv-text flex items-center space-x-2">
                <span className="w-2.5 h-2.5 rounded-full bg-cv-success" />
                <span>HOW MUCH RISK EACH ₹1 OF BUDGET REMOVES</span>
              </h3>
              <p className="text-xs text-cv-muted">Beyond the sweet spot, additional spending delivers less and less benefit</p>
            </div>
            <span className="text-xs font-mono text-cv-success font-bold">
              Best value: ₹1.30 Cr
            </span>
          </div>

          <div className="h-64 sm:h-72 w-full pt-2">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data.efficientFrontier} margin={{ top: 10, right: 20, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E4E7EC" vertical={false} />
                <XAxis
                  dataKey="investment"
                  stroke="#94A3B8"
                  fontSize={11}
                  fontFamily="JetBrains Mono"
                  tickFormatter={(val) => `₹${val}Cr`}
                />
                <YAxis
                  stroke="#94A3B8"
                  fontSize={11}
                  fontFamily="JetBrains Mono"
                  tickFormatter={(val) => `₹${val}Cr`}
                />
                <Tooltip
                  contentStyle={TOOLTIP_STYLE}
                  formatter={(val, name) => [name === 'riskReduction' ? `₹${val} Cr EAL Reduction` : name === 'eal' ? `₹${val} Cr Remaining EAL` : `${val}%`, name === 'riskReduction' ? 'Risk Reduction' : name === 'eal' ? 'Remaining EAL' : 'ROSI']}
                />
                <ReferenceLine x={1.30} stroke="#16A34A" strokeDasharray="3 3" label={{ value: 'Optimal Sweet Spot (₹1.3 Cr)', fill: '#16A34A', fontSize: 10, position: 'top' }} />
                <ReferenceLine x={2.60} stroke="#DC2626" strokeDasharray="3 3" label={{ value: 'Diminishing Returns Zone', fill: '#DC2626', fontSize: 10, position: 'top' }} />
                
                <Line
                  type="monotone"
                  dataKey="riskReduction"
                  stroke="#16A34A"
                  strokeWidth={3}
                  dot={{ fill: '#16A34A', r: 4 }}
                  name="riskReduction"
                />
                <Line
                  type="monotone"
                  dataKey="eal"
                  stroke="#2563EB"
                  strokeWidth={2}
                  strokeDasharray="4 4"
                  dot={{ fill: '#2563EB', r: 3 }}
                  name="eal"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Interactive Budget Slider */}
          <div className="p-3.5 rounded-lg bg-cv-bg border border-cv-border space-y-2 font-mono text-xs">
            <div className="flex justify-between items-center text-cv-muted">
              <span>Simulate Custom Budget Allocation:</span>
              <strong className="text-cv-blue text-sm font-sans">{formatCurrency(budgetSlider)}</strong>
            </div>
            <input
              type="range"
              min="0.2"
              max="3.5"
              step="0.05"
              value={budgetSlider}
              onChange={(e) => setBudgetSlider(parseFloat(e.target.value))}
              className="w-full h-2 bg-cv-border rounded-lg appearance-none cursor-pointer accent-cv-blue"
            />
            <div className="flex justify-between text-[10px] text-cv-muted">
              <span>Min: ₹20 Lakhs</span>
              <span className="text-cv-success">Sweet Spot: ₹1.30 Cr</span>
              <span>Max Budget: ₹3.50 Cr</span>
            </div>
          </div>
        </div>

        {/* Investment Payback & Portfolio Metrics */}
        <div className="cyber-card rounded-lg p-5 border-cv-border flex flex-col justify-between space-y-4">
          <div className="border-b border-cv-border pb-3">
            <h3 className="text-sm font-sans font-semibold text-cv-text flex items-center space-x-2">
              <Award className="w-4 h-4 text-cv-warning" />
              <span>CAPITAL OPTIMIZATION SUMMARY</span>
            </h3>
            <p className="text-xs text-cv-muted">Board-level financial exposure metrics</p>
          </div>

          <div className="space-y-3 font-mono text-xs">
            <div className="p-3 rounded-lg bg-cv-bg border border-cv-border space-y-2">
              <div className="flex justify-between text-cv-muted">
                <span>Current EAL Exposure:</span>
                <strong className="text-cv-danger">{formatCurrency(baselineEal)}</strong>
              </div>
              <div className="flex justify-between text-cv-muted">
                <span>Simulated EAL with ₹{budgetSlider}Cr:</span>
                <strong className="text-cv-success">{formatCurrency(dynamicEal)}</strong>
              </div>
              <div className="flex justify-between text-cv-muted border-t border-cv-border pt-1">
                <span>Net Annual Value Saved:</span>
                <strong className="text-cv-blue">{formatCurrency(dynamicReduction)} / yr</strong>
              </div>
            </div>

            <div className="p-3 rounded-lg bg-cv-bg border border-cv-border space-y-2">
              <div className="flex justify-between text-cv-muted">
                <span>Payback Duration:</span>
                <strong className="text-cv-warning">
                  {dynamicReduction > 0 ? `~${((dynamicInvestment / dynamicReduction) * 12).toFixed(1)} Months` : '—'}
                </strong>
              </div>
              <div className="flex justify-between text-cv-muted">
                <span>3-Year Cumulative Benefit:</span>
                <strong className="text-cv-success">
                  {formatCurrency(Math.max(0, dynamicReduction * 3 - dynamicInvestment))}
                </strong>
              </div>
            </div>
          </div>

          <div className="p-3 rounded-lg bg-cv-blueLight border border-blue-200 text-[11px] font-mono text-cv-blue">
            ⚡ <strong>Executive Insight:</strong> Beyond ₹1.70 Cr of capital, the marginal risk reduction flattens to less than 12% per additional ₹50 Lakhs invested due to control saturation.
          </div>
        </div>

      </div>

      {/* Recommended Security Investment Initiatives Table */}
      <div className="cyber-card rounded-lg border-cv-border overflow-hidden space-y-3 p-5">
        <div className="border-b border-cv-border pb-3 flex items-center justify-between">
          <div>
            <h3 className="text-sm font-sans font-semibold text-cv-text flex items-center space-x-2">
              <Sparkles className="w-4 h-4 text-cv-success" />
              <span>RECOMMENDED SECURITY INITIATIVES (ROSI-RANKED)</span>
            </h3>
            <p className="text-xs text-cv-muted">
              Prioritized security investments ordered by Return on Security Investment (ROSI)
            </p>
          </div>
          <Badge variant="success">TOP 5 RANKED</Badge>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left font-mono text-xs">
            <thead>
              <tr className="border-b border-cv-border text-cv-muted uppercase">
                <th className="pb-3 px-3">Rank & Initiative</th>
                <th className="pb-3 px-3">Domain</th>
                <th className="pb-3 px-3">Investment Cost</th>
                <th className="pb-3 px-3">EAL Reduction</th>
                <th className="pb-3 px-3">ROSI %</th>
                <th className="pb-3 px-3">Payback Period</th>
                <th className="pb-3 px-3 text-right">Approval Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-cv-border">
              {initiativesToDisplay.map((init) => (
                <tr key={init.id} className="hover:bg-cv-bg transition-colors">
                  <td className="py-3 px-3">
                    <div className="flex items-center space-x-2">
                      <span className="w-5 h-5 rounded-full bg-cv-blueLight border border-blue-200 flex items-center justify-center font-bold text-cv-blue text-[10px]">
                        #{init.priorityRank}
                      </span>
                      <span className="font-bold text-cv-text font-sans text-sm">{init.title}</span>
                    </div>
                  </td>
                  <td className="py-3 px-3 text-cv-muted">
                    <span className="px-2 py-0.5 rounded bg-cv-bg border border-cv-border text-[10px] text-cv-muted">
                      {init.domain}
                    </span>
                  </td>
                  <td className="py-3 px-3 font-bold text-cv-text">
                    {formatCurrency(init.cost)}
                  </td>
                  <td className="py-3 px-3 font-bold text-cv-success">
                    -{formatCurrency(init.riskReduction)}
                  </td>
                  <td className="py-3 px-3">
                    <span className="px-2 py-0.5 rounded bg-cv-successBg text-cv-success border border-green-200 font-bold">
                      {init.rosi}%
                    </span>
                  </td>
                  <td className="py-3 px-3 text-cv-muted">
                    {init.paybackPeriod}
                  </td>
                  <td className="py-3 px-3 text-right">
                    <Badge
                      variant={init.status === 'APPROVED_FOR_BUDGET' ? 'success' : init.status === 'UNDER_REVIEW' ? 'medium' : 'default'}
                      size="xs"
                    >
                      {init.status.replace(/_/g, ' ')}
                    </Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  );
}
