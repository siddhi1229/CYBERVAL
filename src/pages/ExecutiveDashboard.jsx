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
  Info
} from 'lucide-react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
  BarChart,
  Bar,
  Cell
} from 'recharts';
import MetricCard from '../components/common/MetricCard';
import RiskGauge from '../components/common/RiskGauge';
import Badge from '../components/common/Badge';
import LoadingSpinner from '../components/common/LoadingSpinner';
import CyTooltip from '../components/common/Tooltip';
import { useTelemetry } from '../context/TelemetryContext';
import { executiveApi } from '../api/executiveApi';

// Shared chart tooltip style
const TOOLTIP_STYLE = {
  backgroundColor: '#FFFFFF',
  borderColor: '#E4E7EC',
  borderRadius: '8px',
  fontSize: '11px',
  fontFamily: 'JetBrains Mono',
  color: '#17212B',
  boxShadow: '0 4px 6px -1px rgba(0,0,0,0.08)'
};

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
        setError('Unable to load risk data. Please check your connection.');
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [refreshKey]);

  if (loading) return <LoadingSpinner text="Loading risk intelligence..." />;
  if (error || !data) {
    return (
      <div className="p-8 text-center text-cv-danger border border-red-200 rounded-lg bg-red-50 font-mono">
        <AlertTriangle className="w-8 h-8 mx-auto mb-2 text-cv-danger" />
        <p>{error || 'No data available.'}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      
      {/* Top Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 rounded-lg cyber-card border-cv-border">
        <div>
          <div className="flex items-center space-x-2">
            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-cv-blueLight text-cv-blue border border-blue-200">
              EXECUTIVE SUMMARY
            </span>
            <span className="text-xs font-mono text-cv-muted">
              Live Risk Intelligence · Updated Just Now
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-cv-text mt-1 tracking-tight">
            Cyber Risk & Financial Exposure
          </h1>
          <p className="text-xs sm:text-sm text-cv-muted mt-0.5">
            How much financial risk cyber threats pose to the business — and what we can do about it.
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
            <span>TRY A SECURITY CHANGE</span>
          </button>
        </div>
      </div>

      {/* Primary KPI Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        
        {/* Enterprise Risk Score */}
        <div className="cyber-card rounded-lg p-4 flex flex-col justify-between border-red-200">
          <div className="flex items-center justify-between text-xs font-mono text-cv-muted">
            <span className="font-bold uppercase tracking-wider text-cv-text">Enterprise Risk Score</span>
            <Badge variant="critical">HIGH RISK</Badge>
          </div>
          <p className="text-[11px] text-cv-muted font-sans mt-1">
            How much cyber risk the business currently faces
          </p>
          <div className="my-1 flex items-center justify-center">
            <RiskGauge score={data.enterpriseRiskScore} max={100} size={150} strokeWidth={10} delta={data.riskScoreDelta} label="" />
          </div>
          <div className="text-[11px] font-mono text-cv-muted text-center border-t border-cv-border pt-2">
            Target after improvements: <strong className="text-cv-success">42 / 100</strong>
          </div>
        </div>

        {/* Expected Yearly Loss */}
        <MetricCard
          title="Expected Yearly Loss"
          explanation="Estimated financial loss from cyber incidents in a typical year"
          value={formatCurrency(data.expectedAnnualLoss)}
          subtitle={`Range: ${formatCurrency(data.confidenceInterval.low)} – ${formatCurrency(data.confidenceInterval.high)}`}
          delta={data.ealDelta}
          deltaType="negative_is_good"
          icon={DollarSign}
          variant="critical"
          technicalBadge="EAL"
          technicalTooltip="Expected Annual Loss — the statistically estimated total financial loss from cyber incidents in a typical year."
        >
          <div className="w-full bg-cv-bg rounded-full h-1.5 overflow-hidden mt-1">
            <div className="bg-gradient-to-r from-cv-warning to-cv-danger h-full w-[65%]" />
          </div>
          <div className="flex justify-between text-[10px] font-mono text-cv-muted mt-1">
            <span>Best case: ₹12.0 Cr</span>
            <span>Worst case: ₹84.2 Cr</span>
          </div>
        </MetricCard>

        {/* Worst-Case Loss */}
        <MetricCard
          title="Worst-Case Loss"
          explanation="Estimated loss in a severe cyber attack scenario"
          value={formatCurrency(data.p95Loss)}
          subtitle={`Extreme scenario: ${formatCurrency(data.p99Loss)}`}
          delta={-1.3}
          deltaType="negative_is_good"
          icon={ShieldAlert}
          variant="warning"
          technicalBadge="P95 VaR"
          technicalTooltip="P95 Value at Risk — 95% of simulated scenarios result in losses below this figure. Only 1-in-20 years would be worse."
        >
          <div className="text-[11px] font-mono text-cv-muted mt-2 bg-cv-bg p-2 rounded border border-cv-border">
            5% chance of exceeding <strong className="text-cv-warning">{formatCurrency(data.p95Loss)}</strong> in any given year.
          </div>
        </MetricCard>

        {/* Risk We Can Reduce */}
        <MetricCard
          title="Risk We Can Reduce"
          explanation="Estimated financial risk we can remove through security improvements"
          value={formatCurrency(data.potentialRiskReduction)}
          subtitle="From 3 priority security actions"
          delta={6.5}
          deltaType="positive_is_good"
          icon={TrendingDown}
          variant="success"
          technicalBadge="ROSI"
          technicalTooltip="Return on Security Investment — for every ₹1 spent on these controls, the business avoids ₹4+ in potential losses."
        >
          <div className="flex items-center justify-between text-[11px] font-mono mt-2 pt-1 border-t border-cv-border">
            <span className="text-cv-muted">Investment needed:</span>
            <span className="text-cv-success font-bold">₹1.30 Cr → 400% return</span>
          </div>
        </MetricCard>

      </div>

      {/* Risk Over Time Chart + Money At Risk Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Risk Over Time Chart */}
        <div className="lg:col-span-2 cyber-card rounded-lg p-5 border-cv-border space-y-3">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-cv-border pb-3">
            <div>
              <h3 className="text-sm font-sans font-semibold text-cv-text flex items-center space-x-2">
                <span className="w-2.5 h-2.5 rounded-full bg-cv-blue" />
                <span>RISK OVER TIME</span>
              </h3>
              <p className="text-xs text-cv-muted">How our cyber risk and potential losses are changing month by month</p>
            </div>
            <div className="flex items-center space-x-3 text-xs font-mono">
              <span className="flex items-center text-cv-blue"><span className="w-2 h-2 rounded bg-cv-blue mr-1.5" />Expected Loss</span>
              <span className="flex items-center text-cv-danger"><span className="w-2 h-2 rounded bg-cv-danger mr-1.5" />Risk Score</span>
              <span className="flex items-center text-cv-warning"><span className="w-2 h-2 rounded bg-cv-warning mr-1.5" />Worst-Case Loss</span>
            </div>
          </div>

          <div className="h-64 sm:h-72 w-full pt-2">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={data.riskTrend} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="ealGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%"  stopColor="#2563EB" stopOpacity={0.2} />
                    <stop offset="95%" stopColor="#2563EB" stopOpacity={0.0} />
                  </linearGradient>
                  <linearGradient id="p95Grad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%"  stopColor="#D97706" stopOpacity={0.15} />
                    <stop offset="95%" stopColor="#D97706" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#E4E7EC" vertical={false} />
                <XAxis dataKey="month" stroke="#94A3B8" fontSize={11} fontFamily="JetBrains Mono" />
                <YAxis stroke="#94A3B8" fontSize={11} fontFamily="JetBrains Mono" />
                <Tooltip
                  contentStyle={TOOLTIP_STYLE}
                  formatter={(val, name) => [name === 'score' ? `${val} / 100` : `₹${val} Cr`, name === 'score' ? 'Risk Score' : name === 'eal' ? 'Expected Loss' : 'Worst-Case Loss']}
                />
                <Area type="monotone" dataKey="p95" stroke="#D97706" strokeWidth={2} strokeDasharray="3 3" fill="url(#p95Grad)" name="p95" />
                <Area type="monotone" dataKey="eal" stroke="#2563EB" strokeWidth={2.5} fill="url(#ealGrad)" name="eal" />
                <Line type="monotone" dataKey="score" stroke="#DC2626" strokeWidth={2} dot={{ fill: '#DC2626', r: 3 }} name="score" />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          <div className="flex items-center justify-between text-[11px] font-mono text-cv-muted bg-cv-bg p-2.5 rounded border border-cv-border">
            <span>Forecast: MFA rollout + automated patching by May 2026.</span>
            <span className="text-cv-success font-bold">Projected saving: -35.3%</span>
          </div>
        </div>

        {/* Money At Risk */}
        <div className="cyber-card rounded-lg p-5 border-cv-border flex flex-col justify-between space-y-4">
          <div className="border-b border-cv-border pb-3">
            <h3 className="text-sm font-sans font-semibold text-cv-text flex items-center space-x-2">
              <span className="w-2.5 h-2.5 rounded-full bg-cv-danger" />
              <span>MONEY AT RISK</span>
            </h3>
            <p className="text-xs text-cv-muted">Total financial impact if major cyber risks occur</p>
          </div>

          <div className="text-center py-2 bg-cv-bg rounded-lg border border-cv-border">
            <span className="text-xs font-mono text-cv-muted uppercase">Maximum estimated impact</span>
            <div className="text-4xl font-extrabold text-cv-text font-sans mt-1">
              {formatCurrency(data.totalFinancialExposure)}
            </div>
            <span className="text-[11px] font-mono text-cv-danger">
              Across 5 critical business services
            </span>
          </div>

          <div className="space-y-2 font-mono text-xs">
            <div className="flex items-center justify-between p-2 rounded bg-cv-bg border border-cv-border">
              <div>
                <span className="text-cv-text font-semibold block">Typical yearly loss</span>
                <span className="text-cv-muted text-[10px]">What we lose in a normal year</span>
              </div>
              <span className="font-bold text-cv-blue">{formatCurrency(data.expectedAnnualLoss)}</span>
            </div>
            <div className="flex items-center justify-between p-2 rounded bg-cv-bg border border-cv-border">
              <div>
                <span className="text-cv-text font-semibold block">Bad-year scenario</span>
                <span className="text-cv-muted text-[10px]">Likely in 1 out of 10 years</span>
              </div>
              <span className="font-bold text-cv-warning">{formatCurrency(data.p90Loss)}</span>
            </div>
            <div className="flex items-center justify-between p-2 rounded bg-cv-bg border border-cv-border">
              <div>
                <span className="text-cv-text font-semibold block">Severe scenario</span>
                <span className="text-cv-muted text-[10px]">
                  <CyTooltip text="P95 VaR — 95th percentile: only 5% of simulated scenarios exceed this amount." position="left">
                    <span className="cursor-help underline decoration-dotted text-cv-muted">1-in-20 year event ↗</span>
                  </CyTooltip>
                </span>
              </div>
              <span className="font-bold text-cv-danger">{formatCurrency(data.p95Loss)}</span>
            </div>
            <div className="flex items-center justify-between p-2 rounded bg-cv-bg border border-cv-border">
              <div>
                <span className="text-cv-text font-semibold block">Catastrophic scenario</span>
                <span className="text-cv-muted text-[10px]">Rare extreme event</span>
              </div>
              <span className="font-bold text-purple-700">{formatCurrency(data.p99Loss)}</span>
            </div>
          </div>

          <button
            onClick={() => navigate('/risk')}
            className="w-full py-2 rounded-lg bg-cv-bg hover:bg-cv-blueLight text-cv-blue text-xs font-mono font-semibold flex items-center justify-center space-x-2 transition-colors border border-blue-200"
          >
            <span>VIEW FULL RISK ANALYSIS</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

      </div>

      {/* Tabs Section */}
      <div className="cyber-card rounded-lg border-cv-border overflow-hidden">
        
        {/* Tabs Header */}
        <div className="flex flex-wrap items-center justify-between p-4 border-b border-cv-border bg-cv-bg gap-3">
          <div className="flex space-x-2 font-mono text-xs">
            <button
              onClick={() => setActiveTab('contributors')}
              className={`px-3.5 py-2 rounded-lg font-bold transition-all ${
                activeTab === 'contributors'
                  ? 'bg-cv-blue text-white shadow-sm'
                  : 'bg-white text-cv-muted hover:text-cv-text border border-cv-border'
              }`}
            >
              What's Causing Our Risk ({data.topRiskContributors.length})
            </button>
            <button
              onClick={() => setActiveTab('services')}
              className={`px-3.5 py-2 rounded-lg font-bold transition-all ${
                activeTab === 'services'
                  ? 'bg-cv-blue text-white shadow-sm'
                  : 'bg-white text-cv-muted hover:text-cv-text border border-cv-border'
              }`}
            >
              Business Service Risk ({data.criticalBusinessServices.length})
            </button>
            <button
              onClick={() => setActiveTab('opportunities')}
              className={`px-3.5 py-2 rounded-lg font-bold transition-all ${
                activeTab === 'opportunities'
                  ? 'bg-cv-blue text-white shadow-sm'
                  : 'bg-white text-cv-muted hover:text-cv-text border border-cv-border'
              }`}
            >
              Ways We Can Reduce Risk ({data.riskReductionOpportunities.length})
            </button>
          </div>

          <span className="text-xs font-mono text-cv-muted">
            Click any row to see full details
          </span>
        </div>

        {/* Tab 1: What's Causing Our Risk */}
        {activeTab === 'contributors' && (
          <div className="p-4 overflow-x-auto">
            <table className="w-full text-left font-mono text-xs">
              <thead>
                <tr className="border-b border-cv-border text-cv-muted uppercase">
                  <th className="pb-3 px-3">Risk & Vulnerability</th>
                  <th className="pb-3 px-3">Who's Behind It</th>
                  <th className="pb-3 px-3">Business Impact</th>
                  <th className="pb-3 px-3">Money at Risk</th>
                  <th className="pb-3 px-3">Yearly Loss</th>
                  <th className="pb-3 px-3">% of Total</th>
                  <th className="pb-3 px-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-cv-border">
                {data.topRiskContributors.map((rc) => (
                  <tr key={rc.id} className="hover:bg-cv-bg transition-colors group">
                    <td className="py-3 px-3">
                      <div className="font-bold text-cv-text font-sans group-hover:text-cv-blue transition-colors">
                        {rc.title}
                      </div>
                      <div className="flex items-center space-x-2 mt-0.5">
                        <CyTooltip text={`CVE ID: ${rc.cve} — a specific security vulnerability in the system.`} position="right">
                          <span className="text-[10px] text-cv-blue font-bold cursor-help underline decoration-dotted">{rc.cve}</span>
                        </CyTooltip>
                        <span className="text-cv-border">•</span>
                        <span className="text-[10px] text-cv-danger font-semibold">{rc.severity}</span>
                      </div>
                    </td>
                    <td className="py-3 px-3 text-cv-muted">
                      <div className="text-cv-text">{rc.threatActor}</div>
                      <span className="text-[10px] text-cv-muted">{rc.status}</span>
                    </td>
                    <td className="py-3 px-3 text-cv-muted max-w-xs truncate">
                      {rc.businessImpact}
                    </td>
                    <td className="py-3 px-3 text-cv-text font-semibold">
                      {formatCurrency(rc.financialExposure)}
                    </td>
                    <td className="py-3 px-3 text-cv-danger font-bold">
                      {formatCurrency(rc.ealContribution)}
                    </td>
                    <td className="py-3 px-3">
                      <div className="flex items-center space-x-2">
                        <span className="text-cv-text font-bold">{rc.percentage}%</span>
                        <div className="w-12 bg-cv-bg h-1.5 rounded-full overflow-hidden border border-cv-border">
                          <div className="bg-cv-danger h-full" style={{ width: `${rc.percentage}%` }} />
                        </div>
                      </div>
                    </td>
                    <td className="py-3 px-3 text-right">
                      <button
                        onClick={() => navigate('/attack-graph')}
                        className="px-2.5 py-1 rounded bg-cv-bg border border-cv-border hover:bg-cv-blue hover:text-white hover:border-cv-blue text-cv-muted font-bold transition-all text-[11px]"
                      >
                        See Attack Path
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Tab 2: Business Service Risk */}
        {activeTab === 'services' && (
          <div className="p-4 overflow-x-auto">
            <table className="w-full text-left font-mono text-xs">
              <thead>
                <tr className="border-b border-cv-border text-cv-muted uppercase">
                  <th className="pb-3 px-3">Business Service</th>
                  <th className="pb-3 px-3">Business Unit</th>
                  <th className="pb-3 px-3">Downtime Cost / Hour</th>
                  <th className="pb-3 px-3">Risk Score</th>
                  <th className="pb-3 px-3">Money at Risk</th>
                  <th className="pb-3 px-3">Expected Yearly Loss</th>
                  <th className="pb-3 px-3 text-right">Assets & Issues</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-cv-border">
                {data.criticalBusinessServices.map((svc) => (
                  <tr key={svc.id} className="hover:bg-cv-bg transition-colors">
                    <td className="py-3 px-3">
                      <div className="font-bold text-cv-text font-sans">{svc.name}</div>
                      <Badge
                        variant={svc.riskScore >= 80 ? 'critical' : svc.riskScore >= 65 ? 'high' : 'medium'}
                        size="xs"
                        className="mt-1"
                      >
                        {svc.status}
                      </Badge>
                    </td>
                    <td className="py-3 px-3 text-cv-muted">{svc.unit}</td>
                    <td className="py-3 px-3 text-cv-muted">
                      <div className="text-cv-text">{svc.slaTier}</div>
                      <span className="text-[10px] text-cv-warning font-semibold">{svc.outageCostPerHour}</span>
                    </td>
                    <td className="py-3 px-3">
                      <span className={`font-bold font-sans ${svc.riskScore >= 80 ? 'text-cv-danger' : 'text-cv-warning'}`}>
                        {svc.riskScore} / 100
                      </span>
                    </td>
                    <td className="py-3 px-3 text-cv-text font-semibold">
                      {formatCurrency(svc.financialExposure)}
                    </td>
                    <td className="py-3 px-3 text-cv-danger font-bold">
                      {formatCurrency(svc.eal)}
                    </td>
                    <td className="py-3 px-3 text-right text-cv-muted">
                      <span>{svc.assetsCount} Assets • <strong className="text-cv-danger">{svc.criticalVulns} Critical Issues</strong></span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Tab 3: Ways We Can Reduce Risk */}
        {activeTab === 'opportunities' && (
          <div className="p-4 space-y-3 font-mono text-xs">
            {data.riskReductionOpportunities.map((opp) => (
              <div
                key={opp.id}
                className="p-4 rounded-lg bg-cv-bg border border-cv-border hover:border-cv-success hover:bg-green-50/30 transition-all flex flex-col md:flex-row md:items-center justify-between gap-4"
              >
                <div className="space-y-1">
                  <div className="flex items-center space-x-2">
                    <span className="text-cv-success font-bold text-sm font-sans">{opp.initiative}</span>
                    <CyTooltip
                      text={`ROSI: Return on Security Investment — for every ₹1 spent here, the business avoids ₹${Math.round(opp.rosi / 100)} in potential losses.`}
                    >
                      <span className="px-2 py-0.5 rounded text-[10px] bg-cv-successBg text-cv-success border border-green-200 font-bold cursor-help">
                        {opp.rosi}% return
                      </span>
                    </CyTooltip>
                  </div>
                  <p className="text-cv-muted text-xs">
                    Protects: <strong className="text-cv-text">{opp.targetService}</strong> · Ready in: <strong className="text-cv-text">{opp.timeToImplement}</strong>
                  </p>
                  <p className="text-[10px] text-cv-muted">
                    Compliance coverage: {opp.frameworkMapping}
                  </p>
                </div>

                <div className="flex items-center space-x-6 border-t md:border-t-0 md:border-l border-cv-border pt-2 md:pt-0 md:pl-6">
                  <div>
                    <span className="text-cv-muted text-[10px] block">INVESTMENT NEEDED</span>
                    <span className="font-bold text-cv-text">{formatCurrency(opp.implementationCost)}</span>
                  </div>
                  <div>
                    <span className="text-cv-muted text-[10px] block">RISK REDUCTION</span>
                    <span className="font-bold text-cv-success">-{formatCurrency(opp.ealReduction)}/yr</span>
                  </div>
                  <button
                    onClick={() => navigate('/simulation')}
                    className="px-3 py-1.5 rounded-lg bg-cv-success hover:bg-green-700 text-white border border-green-700 font-bold transition-all text-xs flex items-center space-x-1 shadow-sm"
                  >
                    <span>Test This Change</span>
                    <ArrowRight className="w-3 h-3" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

      </div>

    </div>
  );
}
