import React from 'react';
import { Activity, Radio, FileText, Database, LogOut, Shield, Sparkles } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

interface NavbarProps {
  currentTab: 'dashboard' | 'reports' | 'pipeline';
  setCurrentTab: (tab: 'dashboard' | 'reports' | 'pipeline') => void;
  sseConnected: boolean;
  lastUpdate: Date | null;
}

export const Navbar: React.FC<NavbarProps> = ({
  currentTab,
  setCurrentTab,
  sseConnected,
  lastUpdate
}) => {
  const { user, logout, isAdmin } = useAuth();

  return (
    <header className="sticky top-0 z-50 bg-[#080b11]/80 backdrop-blur-xl border-b border-white/[0.07]">
      <div className="max-w-[1560px] mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-14">
          
          {/* Brand Logo & Platform Name */}
          <div className="flex items-center gap-3">
            <div className="relative flex items-center justify-center w-8 h-8 rounded-lg bg-gradient-to-tr from-sky-600 to-indigo-600 shadow-md shadow-sky-600/20">
              <Activity className="w-4 h-4 text-white" />
            </div>
            <div className="flex items-baseline gap-2">
              <span className="text-sm font-bold tracking-tight text-white font-mono uppercase">
                SismoWatch
              </span>
              <span className="text-[10px] text-slate-500 font-mono tracking-wider">v1.0</span>
            </div>
          </div>

          {/* Segmented Pill Navigation */}
          <nav className="flex items-center p-1 rounded-xl bg-slate-900/60 border border-white/[0.06] text-xs">
            <button
              onClick={() => setCurrentTab('dashboard')}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg font-medium transition-all duration-150 ${
                currentTab === 'dashboard'
                  ? 'bg-slate-800 text-white shadow-sm border border-white/[0.08]'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
              }`}
            >
              <Activity className="w-3.5 h-3.5" />
              <span>Telemetría Sísmica</span>
            </button>

            <button
              onClick={() => setCurrentTab('reports')}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg font-medium transition-all duration-150 ${
                currentTab === 'reports'
                  ? 'bg-slate-800 text-white shadow-sm border border-white/[0.08]'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
              }`}
            >
              <FileText className="w-3.5 h-3.5" />
              <span>Reportes IA</span>
            </button>

            <button
              onClick={() => setCurrentTab('pipeline')}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg font-medium transition-all duration-150 ${
                currentTab === 'pipeline'
                  ? 'bg-slate-800 text-white shadow-sm border border-white/[0.08]'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
              }`}
            >
              <Database className="w-3.5 h-3.5" />
              <span>Pipeline & Calidad</span>
            </button>
          </nav>

          {/* Real-time Status & Profile Controls */}
          <div className="flex items-center gap-3">
            {/* Live SSE Pulse Chip */}
            <div className="hidden md:flex items-center gap-2 px-2.5 py-1 rounded-full bg-slate-900/80 border border-white/[0.06] text-[11px] font-mono">
              <span className="relative flex h-2 w-2">
                {sseConnected ? (
                  <>
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                  </>
                ) : (
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-rose-500"></span>
                )}
              </span>
              <span className={sseConnected ? 'text-emerald-400 font-semibold' : 'text-rose-400 font-semibold'}>
                {sseConnected ? 'LIVE' : 'DISCONNECTED'}
              </span>
              {lastUpdate && (
                <span className="text-slate-500 border-l border-slate-800 pl-2">
                  {lastUpdate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                </span>
              )}
            </div>

            {/* User Pill Badge */}
            <div className="flex items-center gap-2 px-2.5 py-1 rounded-lg bg-slate-900/60 border border-white/[0.06]">
              <div className="w-5 h-5 rounded-full bg-slate-800 flex items-center justify-center text-[10px] font-bold text-slate-300">
                {user?.username.charAt(0).toUpperCase()}
              </div>
              <span className="text-xs font-medium text-slate-300 hidden sm:inline">
                {user?.username.split('@')[0]}
              </span>
              <span
                className={`text-[9px] uppercase font-mono font-bold px-1.5 py-0.5 rounded ${
                  isAdmin
                    ? 'bg-purple-500/10 text-purple-300 border border-purple-500/30'
                    : 'bg-sky-500/10 text-sky-300 border border-sky-500/30'
                }`}
              >
                {isAdmin ? 'ADMIN' : 'VIEWER'}
              </span>
            </div>

            {/* Logout Action */}
            <button
              onClick={logout}
              title="Cerrar sesión"
              className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-slate-800/60 rounded-lg transition-colors border border-transparent hover:border-rose-500/20"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>

        </div>
      </div>
    </header>
  );
};
