import React from 'react';
import clsx from 'clsx';

export default function Badge({ children, variant = 'default', size = 'sm', className = '' }) {
  const baseClasses = 'inline-flex items-center font-mono font-semibold rounded border tracking-wide transition-all';
  
  const sizeClasses = {
    xs: 'text-[10px] px-1.5 py-0.5 leading-none',
    sm: 'text-xs px-2.5 py-0.5',
    md: 'text-sm px-3 py-1',
  };

  const variantClasses = {
    default:      'bg-slate-100 text-slate-600 border-slate-200',
    critical:     'bg-red-50 text-cv-danger border-red-200',
    high:         'bg-orange-50 text-orange-700 border-orange-200',
    medium:       'bg-amber-50 text-cv-warning border-amber-200',
    low:          'bg-blue-50 text-cv-blue border-blue-200',
    success:      'bg-green-50 text-cv-success border-green-200',
    cyan:         'bg-cyan-50 text-cv-info border-cyan-200',
    purple:       'bg-purple-50 text-purple-700 border-purple-200',
    compliant:    'bg-green-50 text-cv-success border-green-200',
    partial:      'bg-amber-50 text-cv-warning border-amber-200',
    noncompliant: 'bg-red-50 text-cv-danger border-red-200',
  };

  return (
    <span className={clsx(baseClasses, sizeClasses[size], variantClasses[variant] || variantClasses.default, className)}>
      {children}
    </span>
  );
}
