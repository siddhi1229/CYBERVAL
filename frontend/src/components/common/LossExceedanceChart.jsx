import React from 'react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ReferenceLine
} from 'recharts';
import { useTelemetry } from '../../context/TelemetryContext';

export default function LossExceedanceChart({
  data = [],
  p50 = 18.4,
  p90 = 22.1,
  p95 = 31.7,
  p99 = 48.9,
  height = 300
}) {
  const { formatCurrency } = useTelemetry();

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const item = payload[0].payload;
      return (
        <div className="bg-white border border-cv-border p-3 rounded-lg shadow-card-md font-mono text-xs space-y-1">
          <p className="text-cv-blue font-bold">Financial Loss: {formatCurrency(item.loss)}</p>
          <p className="text-cv-muted">Probability of Exceedance: <span className="text-cv-danger font-bold">{item.probability}%</span></p>
          {item.exceedancePercent && <p className="text-cv-muted text-[10px]">{item.exceedancePercent}</p>}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="w-full h-full flex flex-col">
      <div className="flex items-center justify-between mb-2">
        <div className="text-xs font-mono text-cv-muted">
          Loss Exceedance Curve (Monte Carlo 50,000 Iterations)
        </div>
        <div className="flex items-center space-x-3 text-[11px] font-mono">
          <span className="flex items-center text-cv-info"><span className="w-2 h-2 rounded-full bg-cv-info mr-1"></span>EAL (P50): {formatCurrency(p50)}</span>
          <span className="flex items-center text-cv-warning"><span className="w-2 h-2 rounded-full bg-cv-warning mr-1"></span>P90: {formatCurrency(p90)}</span>
          <span className="flex items-center text-cv-danger"><span className="w-2 h-2 rounded-full bg-cv-danger mr-1"></span>P95 VaR: {formatCurrency(p95)}</span>
        </div>
      </div>

      <div style={{ width: '100%', height: height }}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
            <defs>
              <linearGradient id="lossGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%"  stopColor="#DC2626" stopOpacity={0.35} />
                <stop offset="50%" stopColor="#D97706" stopOpacity={0.15} />
                <stop offset="95%" stopColor="#2563EB" stopOpacity={0.04} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#E4E7EC" vertical={false} />
            <XAxis
              dataKey="loss"
              stroke="#94A3B8"
              fontSize={11}
              fontFamily="JetBrains Mono"
              tickFormatter={(val) => `₹${val}Cr`}
            />
            <YAxis
              stroke="#94A3B8"
              fontSize={11}
              fontFamily="JetBrains Mono"
              tickFormatter={(val) => `${val}%`}
              domain={[0, 100]}
            />
            <Tooltip content={<CustomTooltip />} />
            
            <ReferenceLine x={p50} stroke="#0891B2" strokeDasharray="4 4" label={{ value: 'EAL', fill: '#0891B2', fontSize: 10, position: 'top' }} />
            <ReferenceLine x={p95} stroke="#DC2626" strokeWidth={1.5} label={{ value: 'P95 VaR', fill: '#DC2626', fontSize: 10, position: 'top' }} />
            <ReferenceLine x={p99} stroke="#9333EA" strokeDasharray="2 2" label={{ value: 'P99 Tail', fill: '#9333EA', fontSize: 10, position: 'top' }} />

            <Area
              type="monotone"
              dataKey="probability"
              stroke="#DC2626"
              strokeWidth={2.5}
              fillOpacity={1}
              fill="url(#lossGradient)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
