import React from 'react';
import { ShieldAlert } from 'lucide-react';

export default function LoadingSpinner({ text = 'Ingesting Telemetry Data...' }) {
  return (
    <div className="flex flex-col items-center justify-center p-12 space-y-4">
      <div className="relative flex items-center justify-center">
        <div className="w-14 h-14 border-2 border-cv-border rounded-full animate-spin border-t-cv-blue border-r-cv-blue"></div>
        <ShieldAlert className="w-6 h-6 text-cv-blue absolute" />
      </div>
      <p className="text-sm font-mono text-cv-muted tracking-wider uppercase">
        {text}
      </p>
    </div>
  );
}
