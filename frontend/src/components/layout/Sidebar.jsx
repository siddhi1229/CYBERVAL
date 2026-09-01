import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Cpu,
  BarChart3,
  Network,
  SlidersHorizontal,
  TrendingUp,
  ShieldCheck,
  BotMessageSquare,
  Layers,
  FileText
} from 'lucide-react';
import clsx from 'clsx';

export default function Sidebar() {
  const navSections = [
    {
      title: 'COMMAND CENTER',
      items: [
        {
          to: '/executive',
          label: 'Executive',
          badge: null,
          icon: LayoutDashboard,
          description: 'Overall risk & financial exposure'
        },
        {
          to: '/risk',
          label: 'Risk Analysis',
          badge: null,
          icon: BarChart3,
          description: 'Loss scenarios & risk breakdown'
        },
        {
          to: '/attack-graph',
          label: 'Attack Paths',
          badge: null,
          icon: Network,
          description: 'How attackers could reach your systems'
        },
        {
          to: '/simulation',
          label: 'What-If',
          badge: null,
          icon: SlidersHorizontal,
          description: 'Test security changes before investing'
        },
        {
          to: '/investment',
          label: 'Investment',
          badge: null,
          icon: TrendingUp,
          description: 'Where to spend your security budget'
        },
      ]
    },
    {
      title: 'SECURITY',
      items: [
        {
          to: '/technical',
          label: 'Technical',
          badge: null,
          icon: Cpu,
          description: 'Assets, vulnerabilities & controls'
        },
      ]
    },
    {
      title: 'GOVERNANCE',
      items: [
        {
          to: '/compliance',
          label: 'Compliance',
          badge: null,
          icon: ShieldCheck,
          description: 'NIST, ISO, RBI, SEBI, CIS status'
        },
        {
          to: '/reports',
          label: 'Reports',
          badge: null,
          icon: FileText,
          description: 'Executive & board briefings'
        },
      ]
    },
    {
      title: 'INTELLIGENCE',
      items: [
        {
          to: '/copilot',
          label: 'Ask CYBERVAL',
          badge: 'AI',
          icon: BotMessageSquare,
          description: 'Ask any security or risk question'
        },
      ]
    }
  ];

  return (
    <aside className="w-64 flex-shrink-0 border-r border-slate-700/50 bg-cv-sidebar flex flex-col justify-between hidden md:flex h-[calc(100vh-4rem)] sticky top-16 select-none">
      
      {/* Navigation List with Section Headers */}
      <div className="p-3 space-y-4 overflow-y-auto">
        {navSections.map((section, sIdx) => (
          <div key={sIdx} className="space-y-1">
            <div className="px-3 pt-1 text-[10px] font-mono uppercase tracking-widest text-slate-500 font-bold">
              {section.title}
            </div>
            {section.items.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) =>
                    clsx(
                      'group flex items-center justify-between px-3 py-2 rounded-md text-xs font-sans transition-all duration-150 relative',
                      isActive
                        ? 'bg-cv-blue text-white font-semibold'
                        : 'text-slate-400 hover:text-white hover:bg-slate-700/60 border border-transparent'
                    )
                  }
                >
                  {({ isActive }) => (
                    <>
                      <div className="flex items-center space-x-2.5">
                        <Icon className={clsx("w-4 h-4 flex-shrink-0 transition-transform group-hover:scale-105", isActive ? "text-white" : "text-slate-400 group-hover:text-slate-200")} />
                        <div className="truncate">
                          <div className={clsx("font-medium", isActive ? "text-white" : "text-slate-300 group-hover:text-white")}>{item.label}</div>
                          <div className="text-[10px] text-slate-500 line-clamp-1">{item.description}</div>
                        </div>
                      </div>

                      {item.badge && (
                        <span className={clsx(
                          "text-[9px] px-1.5 py-0.5 rounded uppercase font-bold tracking-wider flex-shrink-0",
                          isActive
                            ? "bg-white/20 text-white"
                            : "bg-slate-700 text-slate-400 group-hover:text-slate-300"
                        )}>
                          {item.badge}
                        </span>
                      )}
                    </>
                  )}
                </NavLink>
              );
            })}
          </div>
        ))}
      </div>

      {/* Bottom Status Panel */}
      <div className="p-3 m-3 rounded-lg bg-slate-800/60 border border-slate-700/50 space-y-2 font-mono text-[11px]">
        <div className="flex items-center justify-between text-slate-400">
          <span className="flex items-center space-x-1.5">
            <span className="w-2 h-2 rounded-full bg-cv-success" />
            <span className="text-cv-success font-bold">LIVE DATA</span>
          </span>
          <span className="text-[10px] text-slate-500">v1.0.4</span>
        </div>

        <div className="flex items-center justify-between text-slate-400">
          <span className="flex items-center space-x-1.5">
            <span className="w-2 h-2 rounded-full bg-cv-blue" />
            <span className="text-slate-300">RISK ENGINE ONLINE</span>
          </span>
        </div>

        <div className="pt-2 border-t border-slate-700/60 flex items-center justify-between text-[10px] text-slate-500">
          <span>SIH 2026 · CYBERVAL</span>
          <span className="text-cv-success font-semibold">ACTIVE</span>
        </div>
      </div>

    </aside>
  );
}
