import React, { useState, useEffect } from 'react';
import {
  BarChart3,
  TrendingDown,
  ShieldAlert,
  Sliders,
  DollarSign,
  PieChart as PieIcon,
  Activity,
  Layers,
  AlertCircle
} from 'lucide-react';
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid
} from 'recharts';
import MetricCard from '../components/common/MetricCard';
import LossExceedanceChart from '../components/common/LossExceedanceChart';
import LoadingSpinner from '../components/common/LoadingSpinner';
import Badge from '../components/common/Badge';
import { useTelemetry } from '../context/TelemetryContext';
import { riskApi } from '../api/riskApi';

const TOOLTIP_STYLE = {
  backgroundColor: '#FFFFFF',
  borderColor: '#E4E7EC',
  borderRadius: '8px',
  fontSize: '11px',
  fontFamily: 'JetBrains Mono',
  color: '#17212B',
  boxShadow: '0 4px 6px -1px rgba(0,0,0,0.08)'
};

export default function RiskDashboard() {
  const { formatCurrency, refreshKey } = useTelemetry();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function loadRiskData() {
      try {
        setLoading(true);
        const result = await riskApi.getQuantitativeModeling();
        setData(result);
        setError(null);
      } catch (err) {
        console.error('Error loading risk data:', err);
        setError('Failed to fetch quantitative risk data.');
      } finally {
        setLoading(false);
      }
    }
    loadRiskData();
  }, [refreshKey]);

  if (loading) return <LoadingSpinner text="Running risk simulations..." />;
  if (error || !data) {
    return (
      <div className="p-8 text-center text-cv-danger border border-red-200 rounded-lg bg-red-50 font-mono">
        <ShieldAlert className="w-8 h-8 mx-auto mb-2 text-cv-danger" />
        <p>{error || 'Risk telemetry unavailable.'}</p>
      </div>
    );
  }

  const lossTypeData = [
    { name: 'Productivity Loss',               value: data.fairDecomposition.lossMagnitude.primaryLosses.productivityLoss,                      color: '#2563EB' },
    { name: 'Incident Response & Forensics',   value: data.fairDecomposition.lossMagnitude.primaryLosses.responseCost,                          color: '#0891B2' },
    { name: 'Asset Replacement & Rebuild',     value: data.fairDecomposition.lossMagnitude.primaryLosses.replacementCost,                       color: '#7C3AED' },
    { name: 'RBI/SEBI & DPDP Fines',          value: data.fairDecomposition.lossMagnitude.secondaryLosses.rbiSebiRegulatoryFines,               color: '#DC2626' },
    { name: 'Extortion / Ransom Demands',      value: data.fairDecomposition.lossMagnitude.secondaryLosses.ransomExtortionDemand,               color: '#EA580C' },
    { name: 'Reputational Brand Damage',       value: data.fairDecomposition.lossMagnitude.secondaryLosses.reputationalBrandDamage,             color: '#D97706' },
  ];

  return (
    <div className="space-y-6">
      
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 rounded-lg cyber-card border-cv-border">
        <div>
          <div className="flex items-center space-x-2">
            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-cv-blueLight text-cv-blue border border-blue-200">
              RISK SIMULATION
            </span>
            <span className="text-xs font-mono text-cv-muted">
              50,000 simulated scenarios · Live risk model
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-cv-text mt-1 tracking-tight">
            Risk Analysis & Loss Scenarios
          </h1>
          <p className="text-xs sm:text-sm text-cv-muted mt-0.5">
            Thousands of simulated cyber-attack scenarios to estimate how much the business could lose — and how likely each scenario is.
          </p>
        </div>

        <div className="flex items-center space-x-3 font-mono text-xs">
          <div className="px-3 py-2 rounded-lg bg-cv-bg border border-cv-border text-cv-text">
            SCENARIOS: <strong className="text-cv-blue">{data.confidenceLevel}% confidence</strong>
          </div>
          <div className="px-3 py-2 rounded-lg bg-cv-bg border border-cv-border text-cv-text">
            SIMULATIONS: <strong className="text-cv-text">{data.simulationIterations.toLocaleString()}</strong>
          </div>
        </div>
      </div>

      {/* Primary VaR KPI Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Typical Yearly Loss"
          explanation="What the business loses in a normal year"
          value={formatCurrency(data.p50Loss)}
          subtitle="50% of years are below this"
          icon={DollarSign}
          variant="cyan"
          technicalBadge="P50 EAL"
          technicalTooltip="P50 Expected Annual Loss — the median outcome. Half of all simulated years result in losses below this level."
        />

        <MetricCard
          title="Bad-Year Loss"
          explanation="Likely loss in a difficult but plausible year"
          value={formatCurrency(data.p90Loss)}
          subtitle="Exceeds this once every ~10 years"
          icon={ShieldAlert}
          variant="warning"
          technicalBadge="P90"
          technicalTooltip="P90 Value at Risk — 90% of simulated scenarios result in losses below this figure. Expect this level roughly 1-in-10 years."
        />

        <MetricCard
          title="Severe Scenario"
          explanation="Loss in a severe but realistic cyber attack"
          value={formatCurrency(data.p95Loss)}
          subtitle="Exceeds this once every ~20 years"
          icon={AlertCircle}
          variant="critical"
          technicalBadge="P95 VaR"
          technicalTooltip="P95 Value at Risk — 95% of simulated scenarios result in losses below this figure. The regulatory capital planning baseline."
        />

        <MetricCard
          title="Catastrophic Scenario"
          explanation="Worst-case rare extreme event"
          value={formatCurrency(data.p99Loss)}
          subtitle="Exceeds this once every ~100 years"
          icon={Layers}
          variant="purple"
          technicalBadge="P99"
          technicalTooltip="P99 Tail Risk — only 1% of simulated scenarios exceed this level. Represents a rare, catastrophic cyber event."
        />
      </div>

      {/* Loss Exceedance Curve */}
      <div className="cyber-card rounded-lg p-5 border-cv-border space-y-3">
        <LossExceedanceChart
          data={data.lossExceedanceCurve}
          p50={data.p50Loss}
          p90={data.p90Loss}
          p95={data.p95Loss}
          p99={data.p99Loss}
          height={320}
        />
      </div>

      {/* Risk Factor Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* How Risk is Calculated */}
        <div className="lg:col-span-2 cyber-card rounded-lg p-5 border-cv-border space-y-4">
          <div className="border-b border-cv-border pb-3">
            <h3 className="text-sm font-sans font-semibold text-cv-text flex items-center space-x-2">
              <span className="w-2.5 h-2.5 rounded-full bg-cv-blue" />
              <span>HOW THE RISK IS CALCULATED</span>
            </h3>
            <p className="text-xs text-cv-muted">Two factors drive financial loss: how often attacks succeed × how much each one costs</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 font-mono text-xs">
            
            {/* Left: Attack Frequency */}
            <div className="p-4 rounded-lg bg-cv-bg border border-cv-border space-y-3">
              <div className="flex items-center justify-between border-b border-cv-border pb-2">
                <span className="font-bold text-cv-blue">1. HOW OFTEN ATTACKS SUCCEED</span>
                <Badge variant="cyan" size="xs">14.2 / YEAR</Badge>
              </div>

              <div className="space-y-2">
                <div className="flex justify-between text-cv-muted">
                  <span>Attack frequency:</span>
                  <span className="font-semibold text-cv-text">{data.fairDecomposition.threatEventFrequency.contactFrequency}</span>
                </div>
                <div className="flex justify-between text-cv-muted">
                  <span>Attacker skill level:</span>
                  <span className="font-semibold text-cv-danger">{data.fairDecomposition.threatEventFrequency.threatCapability}</span>
                </div>
                <div className="flex justify-between text-cv-muted">
                  <span>Defence strength:</span>
                  <span className="font-semibold text-cv-warning">{data.fairDecomposition.vulnerabilityResistance.overallStrength}</span>
                </div>
              </div>

              <div className="space-y-1.5 pt-2 border-t border-cv-border">
                <div className="flex justify-between text-[11px] text-cv-muted">
                  <span>Perimeter defence</span>
                  <span className="text-cv-text">62%</span>
                </div>
                <div className="w-full bg-cv-border rounded-full h-1.5 overflow-hidden">
                  <div className="bg-cv-blue h-full" style={{ width: '62%' }} />
                </div>

                <div className="flex justify-between text-[11px] text-cv-muted">
                  <span>Internal movement defence (weakest)</span>
                  <span className="text-cv-danger">38%</span>
                </div>
                <div className="w-full bg-cv-border rounded-full h-1.5 overflow-hidden">
                  <div className="bg-cv-danger h-full" style={{ width: '38%' }} />
                </div>
              </div>
            </div>

            {/* Right: Cost per Attack */}
            <div className="p-4 rounded-lg bg-cv-bg border border-cv-border space-y-3">
              <div className="flex items-center justify-between border-b border-cv-border pb-2">
                <span className="font-bold text-cv-warning">2. COST PER INCIDENT</span>
                <Badge variant="medium" size="xs">DIRECT + INDIRECT</Badge>
              </div>

              <div className="space-y-2">
                <div className="flex justify-between text-cv-muted">
                  <span>Primary Losses (Ops/Tech):</span>
                  <span className="font-bold text-cv-text">{formatCurrency(8.4)}</span>
                </div>
                <div className="flex justify-between text-cv-muted">
                  <span>Secondary Losses (Fines/Ransom):</span>
                  <span className="font-bold text-cv-danger">{formatCurrency(10.0)}</span>
                </div>
                <div className="flex justify-between text-cv-muted">
                  <span>Max Catastrophe (P99):</span>
                  <span className="font-bold text-purple-700">{formatCurrency(data.p99Loss)}</span>
                </div>
              </div>

              <div className="p-2.5 rounded bg-white border border-cv-border text-[11px] text-cv-muted">
                Secondary regulatory losses (RBI/SEBI penalties) exceed primary direct response costs by <strong className="text-cv-text">19.0%</strong> in high-impact banking scenarios.
              </div>
            </div>

          </div>
        </div>

        {/* Primary vs Secondary Loss Pie */}
        <div className="cyber-card rounded-lg p-5 border-cv-border space-y-3 flex flex-col justify-between">
          <div className="border-b border-cv-border pb-3">
            <h3 className="text-sm font-sans font-semibold text-cv-text flex items-center space-x-2">
              <PieIcon className="w-4 h-4 text-cv-blue" />
              <span>LOSS COMPONENT BREAKDOWN</span>
            </h3>
            <p className="text-xs text-cv-muted">Financial distribution of annual cyber loss</p>
          </div>

          <div className="h-44 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={lossTypeData}
                  cx="50%"
                  cy="50%"
                  innerRadius={35}
                  outerRadius={65}
                  paddingAngle={3}
                  dataKey="value"
                >
                  {lossTypeData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(value) => formatCurrency(value)}
                  contentStyle={TOOLTIP_STYLE}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="space-y-1 font-mono text-[10px]">
            {lossTypeData.map((item, idx) => (
              <div key={idx} className="flex items-center justify-between">
                <span className="flex items-center text-cv-muted">
                  <span className="w-2 h-2 rounded-full mr-1.5" style={{ backgroundColor: item.color }} />
                  {item.name}
                </span>
                <span className="text-cv-text font-bold">{formatCurrency(item.value)}</span>
              </div>
            ))}
          </div>
        </div>

      </div>

      {/* Cyber Catastrophe Stress-Testing Scenarios */}
      <div className="cyber-card rounded-lg p-5 border-cv-border space-y-4">
        <div className="border-b border-cv-border pb-3 flex items-center justify-between">
          <div>
            <h3 className="text-sm font-sans font-semibold text-cv-text flex items-center space-x-2">
              <span className="w-2.5 h-2.5 rounded-full bg-cv-danger" />
              <span>CYBER CATASTROPHE STRESS-TEST SCENARIOS</span>
            </h3>
            <p className="text-xs text-cv-muted">Deterministic tail-risk scenario simulation</p>
          </div>
          <Badge variant="critical">BOARD STRESS-TEST</Badge>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 font-mono text-xs">
          {data.scenarioStressTests.map((sc, idx) => (
            <div key={idx} className="p-4 rounded-lg bg-cv-bg border border-cv-border space-y-2 hover:border-red-300 transition-all">
              <div className="flex items-center justify-between">
                <span className="text-[10px] text-cv-danger font-bold uppercase">Scenario #{idx + 1}</span>
                <span className="text-[10px] text-cv-muted">{sc.lossProbability}</span>
              </div>
              <h4 className="font-bold text-cv-text font-sans text-sm">{sc.scenario}</h4>
              
              <div className="pt-2 border-t border-cv-border flex justify-between">
                <span className="text-cv-muted">P95 Exposure:</span>
                <span className="font-bold text-cv-danger">{sc.p95Exposure}</span>
              </div>

              <div className="text-[11px] text-cv-muted">
                <span className="text-cv-muted block">Primary Root Vector:</span>
                {sc.primaryDriver}
              </div>

              <div className="p-2 rounded bg-green-50 border border-green-200 text-[11px] text-cv-success">
                <strong>Mitigating Control:</strong> {sc.keyControlMitigant}
              </div>
            </div>
          ))}
        </div>
      </div>

    </div>
  );
}
