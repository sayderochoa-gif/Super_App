import React from 'react';
import { Earthquake } from '../types';
import { Waves, ExternalLink, Search, Filter } from 'lucide-react';

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
  const getMagBadgeClass = (mag: number) => {
    if (mag >= 6.0) return 'bg-rose-500/20 text-rose-400 border-rose-500/40';
    if (mag >= 4.5) return 'bg-orange-500/20 text-orange-400 border-orange-500/40';
    if (mag >= 3.0) return 'bg-amber-500/20 text-amber-400 border-amber-500/40';
    return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40';
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl shadow-xl flex flex-col h-[520px]">
      {/* Header and Controls */}
      <div className="p-4 border-b border-slate-800 space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <h3 className="font-semibold text-slate-100 text-sm">Flujo de Sismos en Vivo</h3>
            <span className="text-xs bg-slate-800 text-slate-400 px-2 py-0.5 rounded-full border border-slate-700">
              {totalEvents} registrados
            </span>
          </div>
        </div>

        {/* Search & Filter Bar */}
        <div className="flex items-center gap-2">
          <div className="relative flex-1">
            <Search className="w-3.5 h-3.5 text-slate-500 absolute left-2.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Filtrar por región..."
              className="w-full bg-slate-800/80 border border-slate-700 rounded-lg pl-8 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-sky-500"
            />
          </div>

          <div className="flex items-center gap-1">
            {[0, 3.0, 4.5, 6.0].map((val) => (
              <button
                key={val}
                onClick={() => setMinMagFilter(val)}
                className={`px-2 py-1 text-xs rounded font-medium transition-colors ${
                  minMagFilter === val
                    ? 'bg-sky-600 text-white'
                    : 'bg-slate-800 text-slate-400 hover:text-slate-200'
                }`}
              >
                {val === 0 ? 'Todos' : `M${val}+`}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Events List */}
      <div className="flex-1 overflow-y-auto divide-y divide-slate-800/60 p-2">
        {events.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-slate-500 text-xs py-8">
            <p>No se encontraron sismos con los filtros actuales.</p>
          </div>
        ) : (
          events.map((ev) => {
            const isSelected = ev.id === selectedEventId;
            return (
              <div
                key={ev.id}
                onClick={() => onSelectEvent(ev.id)}
                className={`p-3 rounded-lg cursor-pointer transition-all ${
                  isSelected
                    ? 'bg-sky-950/40 border border-sky-500/40 shadow-md'
                    : 'hover:bg-slate-800/50'
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span
                      className={`font-mono font-bold text-xs px-2 py-0.5 rounded border ${getMagBadgeClass(
                        ev.mag
                      )}`}
                    >
                      M {ev.mag.toFixed(1)}
                    </span>
                    <span className="text-xs font-medium text-slate-200 line-clamp-1">
                      {ev.place || 'Ubicación sin nombre'}
                    </span>
                  </div>

                  {ev.tsunami > 0 && (
                    <span className="flex items-center gap-1 text-[10px] font-bold text-rose-400 bg-rose-950/50 border border-rose-500/30 px-1.5 py-0.5 rounded">
                      <Waves className="w-3 h-3" />
                      TSUNAMI
                    </span>
                  )}
                </div>

                <div className="flex items-center justify-between mt-2 text-[11px] text-slate-400">
                  <div className="flex items-center gap-3">
                    <span>Prof: <b className="text-slate-300">{ev.depth_km} km</b></span>
                    <span>Lat/Lon: {ev.latitude.toFixed(1)}°, {ev.longitude.toFixed(1)}°</span>
                  </div>
                  <span>{new Date(ev.time).toLocaleTimeString()}</span>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
