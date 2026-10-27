import React from 'react';
import { Activity, Shield, LogOut, Radio, FileText, Database, RefreshCw } from 'lucide-react';
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
    <header className="sticky top-0 z-50 bg-slate-900/90 backdrop-blur-md border-b border-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Brand */}
          <div className="flex items-center gap-3">
            <div className="bg-sky-500/10 p-2 rounded-lg border border-sky-500/30">
              <Activity className="w-6 h-6 text-sky-400 animate-pulse" />
            </div>
            <div>
              <span className="text-xl font-bold tracking-tight bg-gradient-to-r from-sky-400 via-cyan-300 to-indigo-400 bg-clip-text text-transparent">
                SismoWatch
              </span>
              <span className="text-xs text-slate-400 ml-2 font-mono">SuperApp</span>
            </div>
          </div>

          {/* Navigation Tabs */}
          <nav className="flex items-center gap-1 sm:gap-2">
            <button
              onClick={() => setCurrentTab('dashboard')}
              className={`flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-all ${
                currentTab === 'dashboard'
                  ? 'bg-sky-600 text-white shadow-md shadow-sky-600/20'
                  : 'text-slate-300 hover:text-white hover:bg-slate-800'
              }`}
            >
              <Activity className="w-4 h-4" />
              <span>Dashboard</span>
            </button>

            <button
              onClick={() => setCurrentTab('reports')}
              className={`flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-all ${
                currentTab === 'reports'
                  ? 'bg-sky-600 text-white shadow-md shadow-sky-600/20'
                  : 'text-slate-300 hover:text-white hover:bg-slate-800'
              }`}
            >
              <FileText className="w-4 h-4" />
              <span>Reportes IA</span>
            </button>

            <button
              onClick={() => setCurrentTab('pipeline')}
              className={`flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-all ${
                currentTab === 'pipeline'
                  ? 'bg-sky-600 text-white shadow-md shadow-sky-600/20'
                  : 'text-slate-300 hover:text-white hover:bg-slate-800'
              }`}
            >
              <Database className="w-4 h-4" />
              <span>Pipeline & Calidad</span>
            </button>
          </nav>

          {/* Live Status & User Info */}
          <div className="flex items-center gap-4">
            {/* Live SSE Pulse Indicator */}
            <div className="hidden md:flex items-center gap-2 px-2.5 py-1 rounded-full bg-slate-800/80 border border-slate-700 text-xs">
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
              <span className={sseConnected ? 'text-emerald-400 font-medium' : 'text-rose-400 font-medium'}>
                {sseConnected ? 'EN VIVO (SSE)' : 'RECONECTANDO'}
              </span>
              {lastUpdate && (
                <span className="text-slate-400 border-l border-slate-700 pl-2">
                  {lastUpdate.toLocaleTimeString()}
                </span>
              )}
            </div>

            {/* User Badge */}
            <div className="flex items-center gap-2 bg-slate-800/60 py-1 px-2.5 rounded-lg border border-slate-700/60">
              <div className="text-right hidden sm:block">
                <div className="text-xs font-semibold text-slate-200">{user?.username}</div>
                <div className="text-[10px] text-slate-400 uppercase tracking-wider">{user?.role}</div>
              </div>
              <span
                className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded ${
                  isAdmin
                    ? 'bg-purple-900/50 text-purple-300 border border-purple-500/30'
                    : 'bg-sky-900/50 text-sky-300 border border-sky-500/30'
                }`}
              >
                {isAdmin ? 'ADMIN' : 'VIEWER'}
              </span>
            </div>

            {/* Logout Button */}
            <button
              onClick={logout}
              title="Cerrar sesión"
              className="p-2 text-slate-400 hover:text-rose-400 hover:bg-slate-800 rounded-lg transition-colors"
            >
              <LogOut className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};
