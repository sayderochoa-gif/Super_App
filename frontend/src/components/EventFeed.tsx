import React from 'react';
import { Earthquake } from '../types';
import { Waves, Search, Filter } from 'lucide-react';

interface EventFeedProps {
  events: Earthquake[];
  totalEvents: number;
  selectedEventId: string | null;
  onSelectEvent: (id: string) => void;
  minMagFilter: number;
  setMinMagFilter: (mag: number) => void;
  searchTerm: string;
  setSearchTerm: (term: string) => void;
}

export const EventFeed: React.FC<EventFeedProps> = ({
  events,
  totalEvents,
  selectedEventId,
  onSelectEvent,
  minMagFilter,
  setMinMagFilter,
  searchTerm,
  setSearchTerm
}) => {
  const getMagBadge = (mag: number) => {
    if (mag >= 6.0) return 'bg-rose-500/15 text-rose-300 border-rose-500/30';
    if (mag >= 4.5) return 'bg-orange-500/15 text-orange-300 border-orange-500/30';
    if (mag >= 3.0) return 'bg-amber-500/15 text-amber-300 border-amber-500/30';
    return 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30';
  };

  return (
    <div className="bg-[#0d121c]/90 border border-white/[0.07] rounded-xl shadow-xl flex flex-col h-[520px] overflow-hidden">
      
      {/* Header & Filter Controls */}
      <div className="p-3.5 border-b border-white/[0.06] space-y-2.5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold text-white uppercase font-mono tracking-wider">Feed en Vivo</span>
            <span className="text-[10px] font-mono text-slate-400 bg-slate-900 px-2 py-0.5 rounded-full border border-white/[0.05]">
              {totalEvents} sismos
            </span>
          </div>
        </div>

        {/* Search & Magnitude Filter Bar */}
        <div className="flex items-center gap-2">
          <div className="relative flex-1">
            <Search className="w-3.5 h-3.5 text-slate-500 absolute left-2.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Buscar por región..."
              className="w-full bg-slate-900 border border-white/[0.06] rounded-lg pl-8 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-sky-500/70"
            />
          </div>

          <div className="flex items-center gap-1 p-0.5 rounded-lg bg-slate-900 border border-white/[0.05]">
            {[0, 3.0, 4.5, 6.0].map((val) => (
              <button
                key={val}
                onClick={() => setMinMagFilter(val)}
                className={`px-2 py-1 text-[10px] font-mono font-medium rounded transition-all ${
                  minMagFilter === val
                    ? 'bg-slate-800 text-white shadow-sm border border-white/[0.08]'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {val === 0 ? 'ALL' : `M${val}+`}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Events List */}
      <div className="flex-1 overflow-y-auto divide-y divide-white/[0.04] p-2 space-y-1">
        {events.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-slate-500 text-xs py-8">
            <p>No hay eventos que coincidan con los filtros.</p>
          </div>
        ) : (
          events.map((ev) => {
            const isSelected = ev.id === selectedEventId;
            return (
              <div
                key={ev.id}
                onClick={() => onSelectEvent(ev.id)}
                className={`p-2.5 rounded-lg cursor-pointer transition-all duration-150 ${
                  isSelected
                    ? 'bg-sky-500/[0.08] border border-sky-500/30'
                    : 'hover:bg-slate-800/40 border border-transparent'
                }`}
              >
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2 min-w-0">
                    <span
                      className={`font-mono font-bold text-xs px-2 py-0.5 rounded border flex-shrink-0 ${getMagBadge(
                        ev.mag
                      )}`}
                    >
                      M {ev.mag.toFixed(1)}
                    </span>
                    <span className="text-xs font-medium text-slate-200 truncate">
                      {ev.place || 'Ubicación sin nombre'}
                    </span>
                  </div>

                  {ev.tsunami > 0 && (
                    <span className="flex items-center gap-1 text-[9px] font-bold text-rose-400 bg-rose-500/10 border border-rose-500/20 px-1.5 py-0.5 rounded flex-shrink-0">
                      <Waves className="w-2.5 h-2.5" />
                      TSUNAMI
                    </span>
                  )}
                </div>

                <div className="flex items-center justify-between mt-2 text-[10px] text-slate-500 font-mono">
                  <div className="flex items-center gap-3">
                    <span>Prof: <b className="text-slate-400">{ev.depth_km} km</b></span>
                    <span>{ev.latitude.toFixed(1)}°, {ev.longitude.toFixed(1)}°</span>
                  </div>
                  <span className="text-slate-400">
                    {new Date(ev.time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                  </span>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
