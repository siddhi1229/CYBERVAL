import React from 'react';
import clsx from 'clsx';

export default function RiskGauge({
  score = 71,
  max = 100,
  size = 200,
  strokeWidth = 14,
  label = "Enterprise Risk Score",
  delta = -4.2
}) {
  const radius = (size - strokeWidth) / 2;
  const startAngle = 150;
  const endAngle = 390;
  const totalAngle = endAngle - startAngle;
  
  const percentage = Math.min(Math.max(score / max, 0), 1);
  
  const polarToCartesian = (centerX, centerY, radius, angleInDegrees) => {
    const angleInRadians = ((angleInDegrees - 90) * Math.PI) / 180.0;
    return {
      x: centerX + radius * Math.cos(angleInRadians),
      y: centerY + radius * Math.sin(angleInRadians)
    };
  };

  const describeArc = (x, y, radius, startAngle, endAngle) => {
    const start = polarToCartesian(x, y, radius, endAngle);
    const end = polarToCartesian(x, y, radius, startAngle);
    const largeArcFlag = endAngle - startAngle <= 180 ? '0' : '1';
    return ['M', start.x, start.y, 'A', radius, radius, 0, largeArcFlag, 0, end.x, end.y].join(' ');
  };

  const center = size / 2;
  const backgroundArc = describeArc(center, center, radius, startAngle, endAngle);
  const filledAngle = startAngle + totalAngle * percentage;
  const valueArc = describeArc(center, center, radius, startAngle, filledAngle);

  const getRiskDetails = (val) => {
    if (val >= 80) return { label: 'CRITICAL',   description: 'Immediate action required',    color: 'text-cv-danger',   stroke: '#DC2626' };
    if (val >= 60) return { label: 'HIGH RISK',  description: 'Significant exposure exists',  color: 'text-orange-600',  stroke: '#EA580C' };
    if (val >= 35) return { label: 'MODERATE',   description: 'Some risk areas to address',   color: 'text-cv-warning',  stroke: '#D97706' };
    return           { label: 'CONTROLLED', description: 'Risk well managed',              color: 'text-cv-success',  stroke: '#16A34A' };
  };

  const details = getRiskDetails(score);

  return (
    <div className="flex flex-col items-center justify-center p-4">
      <div className="relative" style={{ width: size, height: size * 0.85 }}>
        <svg width={size} height={size * 0.85} viewBox={`0 0 ${size} ${size * 0.9}`} className="overflow-visible">
          {/* Background track */}
          <path
            d={backgroundArc}
            fill="none"
            stroke="#E4E7EC"
            strokeWidth={strokeWidth}
            strokeLinecap="round"
          />

          {/* Value track */}
          <path
            d={valueArc}
            fill="none"
            stroke={details.stroke}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
          />
        </svg>

        {/* Center Display */}
        <div className="absolute inset-0 flex flex-col items-center justify-center pt-6 text-center pointer-events-none">
          <span className="text-4xl font-black font-sans tracking-tight text-cv-text">
            {score}
            <span className="text-lg font-mono text-cv-muted font-normal"> / {max}</span>
          </span>

          <span className={clsx("text-xs font-mono font-bold tracking-wider mt-1 px-2.5 py-0.5 rounded border", details.color,
            details.label === 'CRITICAL'   ? 'bg-red-50 border-red-200'    :
            details.label === 'HIGH RISK'  ? 'bg-orange-50 border-orange-200' :
            details.label === 'MODERATE'   ? 'bg-amber-50 border-amber-200' :
            'bg-green-50 border-green-200'
          )}>
            {details.label}
          </span>

          {details.description && (
            <span className="text-[10px] font-sans text-cv-muted mt-1 px-2 text-center leading-tight">
              {details.description}
            </span>
          )}

          {delta !== undefined && (
            <span className={clsx("text-[11px] font-mono mt-1 flex items-center", delta < 0 ? 'text-cv-success' : 'text-cv-danger')}>
              {delta < 0 ? `▼ ${Math.abs(delta)} pts (30d)` : `▲ +${delta} pts (30d)`}
            </span>
          )}
        </div>
      </div>

      <div className="text-xs font-mono uppercase tracking-widest text-cv-muted mt-2 font-semibold">
        {label}
      </div>
    </div>
  );
}
