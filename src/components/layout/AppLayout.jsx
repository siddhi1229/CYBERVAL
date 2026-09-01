import React, { useState } from 'react';
import { Outlet, useLocation, Link } from 'react-router-dom';
import Navbar from './Navbar';
import Sidebar from './Sidebar';
import {
  LayoutDashboard,
  Cpu,
  BarChart3,
  Network,
  SlidersHorizontal,
  TrendingUp,
  ShieldCheck,
  BotMessageSquare,
  AlertTriangle,
  Menu,
  X
} from 'lucide-react';

export default function AppLayout() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const location = useLocation();

  const mobileNavItems = [
    { to: '/executive', label: 'Executive', icon: LayoutDashboard },
    { to: '/technical', label: 'Technical', icon: Cpu },
    { to: '/risk', label: 'Risk & FAIR', icon: BarChart3 },
    { to: '/attack-graph', label: 'Attack Graph', icon: Network },
    { to: '/simulation', label: 'What-If', icon: SlidersHorizontal },
    { to: '/investment', label: 'Investment', icon: TrendingUp },
    { to: '/compliance', label: 'Compliance', icon: ShieldCheck },
    { to: '/copilot', label: 'Copilot', icon: BotMessageSquare },
    { to: '/reports', label: 'Reports', icon: AlertTriangle },
  ];

  return (
    <div className="min-h-screen bg-cv-bg text-cv-text flex flex-col font-sans">
      <Navbar />

      {/* Mobile Top Bar */}
      <div className="md:hidden flex items-center justify-between px-4 py-2 bg-cv-sidebar border-b border-slate-700/50">
        <span className="text-xs font-mono font-bold text-slate-300 uppercase">
          {location.pathname.replace('/', '') || 'executive'} view
        </span>
        <button
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="p-1.5 rounded bg-slate-700 text-slate-300 hover:text-white"
        >
          {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>
      </div>

      {/* Mobile Menu Dropdown */}
      {mobileMenuOpen && (
        <div className="md:hidden bg-cv-sidebar border-b border-slate-700/50 p-3 grid grid-cols-2 gap-2 z-50">
          {mobileNavItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.to;
            return (
              <Link
                key={item.to}
                to={item.to}
                onClick={() => setMobileMenuOpen(false)}
                className={`flex items-center space-x-2 p-2 rounded text-xs font-sans ${
                  isActive
                    ? 'bg-cv-blue text-white font-bold'
                    : 'bg-slate-700 text-slate-300'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </div>
      )}

      {/* Main Body */}
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        <main className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8 space-y-6 max-w-7xl mx-auto w-full">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
