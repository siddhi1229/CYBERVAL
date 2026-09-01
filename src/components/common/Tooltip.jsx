import React, { useState } from 'react';
import { HelpCircle, Info } from 'lucide-react';
import clsx from 'clsx';

export default function Tooltip({ text, children, position = 'top', className = '' }) {
  const [visible, setVisible] = useState(false);

  const positionClasses = {
    top: 'bottom-full left-1/2 -translate-x-1/2 mb-2',
    bottom: 'top-full left-1/2 -translate-x-1/2 mt-2',
    left: 'right-full top-1/2 -translate-y-1/2 mr-2',
    right: 'left-full top-1/2 -translate-y-1/2 ml-2',
  };

  return (
    <span
      className={clsx('relative inline-flex items-center', className)}
      onMouseEnter={() => setVisible(true)}
      onMouseLeave={() => setVisible(false)}
      onFocus={() => setVisible(true)}
      onBlur={() => setVisible(false)}
    >
      {children || <Info className="w-3.5 h-3.5 text-cv-muted hover:text-cv-blue cursor-help transition-colors" />}

      {visible && text && (
        <span
          role="tooltip"
          className={clsx(
            'absolute z-50 px-3 py-2 text-[11px] font-sans leading-relaxed text-cv-text bg-white border border-cv-border rounded-lg shadow-card-md pointer-events-none whitespace-normal min-w-[200px] max-w-[280px] animate-in fade-in zoom-in-95 duration-150',
            positionClasses[position]
          )}
        >
          {text}
          <span className="block absolute w-2 h-2 bg-white border-r border-b border-cv-border rotate-45 left-1/2 -translate-x-1/2 -bottom-1" />
        </span>
      )}
    </span>
  );
}
