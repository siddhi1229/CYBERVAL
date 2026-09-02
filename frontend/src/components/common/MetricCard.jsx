import React from 'react';
import { TrendingUp, TrendingDown, Shield, HelpCircle } from 'lucide-react';
import clsx from 'clsx';
import Tooltip from './Tooltip';

export default function MetricCard({
  title,
  explanation,
  value,
  unit = '',
  subtitle,
  delta,
  deltaType = 'neutral', // 'positive_is_good', 'negative_is_good', 'neutral'
  icon: Icon = Shield,
  variant = 'default', // 'default', 'critical', 'warning', 'success', 'cyan', 'purple'
  badge,
  technicalBadge,
  technicalTooltip,
  children
}) {
  const getDeltaColor = () => {
    if (!delta) return 'text-cv-muted';
    if (deltaType === 'negative_is_good') {
      return delta < 0 ? 'text-cv-success' : 'text-cv-danger';
    }
    if (deltaType === 'positive_is_good') {
      return delta > 0 ? 'text-cv-success' : 'text-cv-danger';
    }
    return 'text-cv-blue';
  };

  // Icon container colors per variant
  const getIconStyle = () => {
    switch (variant) {
      case 'critical': return 'bg-red-50 text-cv-danger border-red-200';
      case 'warning':  return 'bg-amber-50 text-cv-warning border-amber-200';
      case 'success':  return 'bg-green-50 text-cv-success border-green-200';
      case 'cyan':     return 'bg-cyan-50 text-cv-info border-cyan-200';
      case 'purple':   return 'bg-purple-50 text-purple-700 border-purple-200';
      default:         return 'bg-blue-50 text-cv-blue border-blue-200';
    }
  };

  // Main value color per variant
  const getValueColor = () => {
    switch (variant) {
      case 'critical': return 'text-cv-danger';
      case 'warning':  return 'text-cv-warning';
      case 'success':  return 'text-cv-success';
      case 'cyan':     return 'text-cv-info';
      case 'purple':   return 'text-purple-700';
      default:         return 'text-cv-text';
    }
  };

  return (
    <div className="cyber-card rounded-lg p-5 relative overflow-hidden transition-all duration-150 flex flex-col justify-between">
      {/* Top Header Row */}
      <div className="space-y-1">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className={clsx('p-1.5 rounded border', getIconStyle())}>
              <Icon className="w-4 h-4" />
            </div>
            <h3 className="text-xs font-sans font-semibold uppercase tracking-wider text-cv-muted">
              {title}
            </h3>
          </div>

          <div className="flex items-center space-x-1.5">
            {technicalBadge && (
              <Tooltip text={technicalTooltip}>
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-cv-bg border border-cv-border text-cv-muted hover:text-cv-blue cursor-help transition-colors">
                  {technicalBadge}
                </span>
              </Tooltip>
            )}

            {badge && (
              <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded border border-cv-border bg-cv-bg text-cv-muted">
                {badge}
              </span>
            )}
          </div>
        </div>

        {/* Plain English Explanation */}
        {explanation && (
          <p className="text-[11px] text-cv-muted font-sans leading-relaxed pt-0.5">
            {explanation}
          </p>
        )}
      </div>

      {/* Main Metric Value */}
      <div className="my-3">
        <div className="flex items-baseline space-x-2">
          <div className={clsx('text-3xl font-black tracking-tight font-sans', getValueColor())}>
            {value}
          </div>
          {unit && <span className="text-sm font-mono text-cv-muted font-normal">{unit}</span>}
        </div>
      </div>

      {/* Subtitle & Delta Footer */}
      <div>
        {(subtitle || delta !== undefined) && (
          <div className="flex items-center justify-between text-xs font-mono pt-2 border-t border-cv-border">
            <span className="text-cv-muted truncate max-w-[70%]">
              {subtitle}
            </span>

            {delta !== undefined && (
              <div className={clsx('flex items-center space-x-1 font-semibold flex-shrink-0', getDeltaColor())}>
                {delta > 0 ? <TrendingUp className="w-3.5 h-3.5" /> : <TrendingDown className="w-3.5 h-3.5" />}
                <span>{delta > 0 ? `+${delta}` : delta}</span>
              </div>
            )}
          </div>
        )}

        {children && <div className="mt-2">{children}</div>}
      </div>
    </div>
  );
}
