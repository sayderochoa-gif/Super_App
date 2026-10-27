import React, { useState } from 'react';
import { Activity, FileText, Database, LogOut, Radio, Menu, X, Bot } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export type NavTab = 'dashboard' | 'agent' | 'reports' | 'pipeline';

interface SidebarProps {
  currentTab: NavTab;
  setCurrentTab: (tab: NavTab) => void;
  sseConnected: boolean;
  lastUpdate: Date | null;
}

const APP_TITLE_LETTERS = [
  { char: 'S', rot: '18deg', delay: '0ms' },
  { char: 'I', rot: '-22deg', delay: '80ms' },
  { char: 'S', rot: '16deg', delay: '160ms' },
  { char: 'M', rot: '-18deg', delay: '240ms' },
  { char: 'O', rot: '24deg', delay: '320ms' },
  { char: 'W', rot: '-20deg', delay: '400ms' },
  { char: 'A', rot: '18deg', delay: '480ms' },
  { char: 'T', rot: '-15deg', delay: '560ms' },
  { char: 'C', rot: '20deg', delay: '640ms' },
  { char: 'H', rot: '-18deg', delay: '720ms' },
];

export const Sidebar: React.FC<SidebarProps> = ({
  currentTab,
  setCurrentTab,
  sseConnected,
  lastUpdate
}) => {
  const { user, logout, isAdmin } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);

  const allNavItems = [
    {
      id: 'dashboard' as const,
      label: 'Telemetría Sísmica',
      icon: Activity,
      desc: 'Globo 3D, KPIs & feed',
      adminOnly: false
    },
    {
      id: 'agent' as const,
      label: 'Agente Sísmico',
      icon: Bot,
      desc: 'Chat IA, análisis & SQL',
      adminOnly: false
    },
    {
      id: 'reports' as const,
      label: 'Reportes IA',
      icon: FileText,
      desc: 'Informes diarios & exportación',
      adminOnly: true
    },
    {
      id: 'pipeline' as const,
      label: 'Pipeline & Calidad',
      icon: Database,
      desc: 'Airflow SLA & Pandera',
      adminOnly: true
    }
  ];

  // Viewer sees Telemetría Sísmica + Agente Sísmico; Admin sees all
  const navItems = allNavItems.filter((item) => !item.adminOnly || isAdmin);

  const handleSelectTab = (tab: NavTab) => {
    setCurrentTab(tab);
    setMobileOpen(false);
  };

  return (
    <>
      {/* Mobile Header Bar */}
      <div className="md:hidden flex items-center justify-between px-4 h-14 bg-[#080b11]/90 backdrop-blur-xl border-b border-white/[0.08] sticky top-0 z-50">
        <div className="flex items-center gap-2.5">
          <div className="flex items-center justify-center w-7 h-7 rounded-lg bg-gradient-to-tr from-sky-600 to-indigo-600 shadow-sm">
            <Activity className="w-3.5 h-3.5 text-white" />
          </div>
          <span className="text-xs font-bold tracking-tight text-white font-mono uppercase inline-flex select-none">
            {APP_TITLE_LETTERS.map((item, idx) => (
              <span
                key={idx}
                className="seismic-letter inline-block"
                style={{
                  animationDelay: item.delay,
                  ['--fall-rot' as any]: item.rot
                }}
              >
                {item.char}
              </span>
            ))}
          </span>
        </div>
        <button
          onClick={() => setMobileOpen(!mobileOpen)}
          className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800"
        >
          {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>
      </div>

      {/* Backdrop for mobile */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm md:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Left Vertical Sidebar */}
      <aside
        className={`fixed md:sticky top-0 left-0 z-50 h-screen w-64 bg-[#080b11]/80 backdrop-blur-2xl border-r border-white/[0.07] flex flex-col justify-between p-4 transition-transform duration-200 ease-in-out shrink-0 ${
          mobileOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
        }`}
      >
        <div className="space-y-6">
          {/* Brand Logo & Platform Title (Centrado) */}
          <div className="flex items-center justify-center relative border-b border-white/[0.07] pb-4">
            <div className="flex items-center justify-center gap-2.5">
              <div className="relative flex items-center justify-center w-7 h-7 rounded-lg bg-gradient-to-tr from-sky-600 to-indigo-600 shadow-md shadow-sky-600/20">
                <Activity className="w-3.5 h-3.5 text-white" />
              </div>
              <span className="text-sm font-bold tracking-wider text-white font-mono uppercase inline-flex select-none">
                {APP_TITLE_LETTERS.map((item, idx) => (
                  <span
                    key={idx}
                    className="seismic-letter inline-block"
                    style={{
                      animationDelay: item.delay,
                      ['--fall-rot' as any]: item.rot
                    }}
                  >
                    {item.char}
                  </span>
                ))}
              </span>
            </div>

            <button
              onClick={() => setMobileOpen(false)}
              className="md:hidden absolute right-0 text-slate-400 hover:text-white"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Live Telemetry Status Badge */}
          <div className="flex items-center justify-between px-3 py-2 rounded-xl bg-slate-900/40 text-[11px] font-mono">
            <div className="flex items-center gap-2">
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
                {sseConnected ? 'STREAM ACTIVO' : 'OFFLINE'}
              </span>
            </div>
            {lastUpdate && (
              <span className="text-[10px] text-slate-500">
                {lastUpdate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </span>
            )}
          </div>

          {/* Vertical Navigation Items */}
          <div className="space-y-1.5">
            <div className="px-3 pb-1 text-[10px] font-mono uppercase tracking-wider text-slate-500 font-semibold">
              Módulos del Sistema
            </div>

            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = currentTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => handleSelectTab(item.id)}
                  className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-left transition-all duration-150 ${
                    isActive
                      ? 'bg-sky-500/15 text-white shadow-sm border border-sky-500/30'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40 border border-transparent'
                  }`}
                >
                  <div
                    className={`p-1.5 rounded-lg transition-colors ${
                      isActive
                        ? 'bg-sky-500 text-white shadow-sm shadow-sky-500/30'
                        : 'bg-slate-900/80 text-slate-400'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                  </div>
                  <div>
                    <div className={`text-xs font-semibold ${isActive ? 'text-white' : 'text-slate-300'}`}>
                      {item.label}
                    </div>
                    <div className="text-[10px] text-slate-500 font-mono">
                      {item.desc}
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* User Card & Logout Controls (Bottom) */}
        <div className="border-t border-white/[0.07] pt-3 space-y-2">
          <div className="flex items-center justify-between p-2 rounded-xl bg-slate-900/60 border border-white/[0.05]">
            <div className="flex items-center gap-2 min-w-0">
              <div className="w-7 h-7 rounded-full bg-slate-800 flex items-center justify-center text-xs font-bold text-slate-300 shrink-0">
                {user?.username.charAt(0).toUpperCase()}
              </div>
              <div className="min-w-0">
                <div className="text-xs font-medium text-slate-200 truncate">
                  {user?.username.split('@')[0]}
                </div>
                <div
                  className={`text-[9px] uppercase font-mono font-bold ${
                    isAdmin ? 'text-purple-400' : 'text-sky-400'
                  }`}
                >
                  {isAdmin ? 'ADMINISTRADOR' : 'OBSERVADOR'}
                </div>
              </div>
            </div>

            <button
              onClick={logout}
              title="Cerrar sesión"
              className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-slate-800/60 rounded-lg transition-colors"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </aside>
    </>
  );
};
