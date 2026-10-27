import React, { useState, useEffect } from 'react';
import { KPIs, Earthquake, TimeseriesPoint } from '../types';
import { api } from '../services/api';
import { SeismicMap } from './SeismicMap';
import { EventFeed } from './EventFeed';
import { Activity, AlertTriangle, ShieldCheck, Waves, TrendingUp, BarChart3, Clock } from 'lucide-react';

interface DashboardProps {
  newEventsFromSSE: Earthquake[];
}

export const Dashboard: React.FC<DashboardProps> = ({ newEventsFromSSE }) => {
  const [kpis, setKpis] = useState<KPIs | null>(null);
  const [events, setEvents] = useState<Earthquake[]>([]);
  const [totalEvents, setTotalEvents] = useState<number>(0);
  const [timeseries, setTimeseries] = useState<TimeseriesPoint[]>([]);
  const [magDist, setMagDist] = useState<{ tier: string; count: number }[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedEventId, setSelectedEventId] = useState<string | null>(null);

  // Filters
  const [minMagFilter, setMinMagFilter] = useState<number>(0);
  const [searchTerm, setSearchTerm] = useState<string>('');

  const loadData = async () => {
    try {
      const [kpiData, eventsData, tsData, distData] = await Promise.all([
        api.getKPIs(),
        api.getEvents({
          min_magnitude: minMagFilter > 0 ? minMagFilter : undefined,
          region: searchTerm || undefined,
          limit: 100
        }),
        api.getTimeseries(24),
        api.getMagnitudeDistribution()
      ]);

      setKpis(kpiData);
      setEvents(eventsData.items);
      setTotalEvents(eventsData.total);
      setTimeseries(tsData.data);
      setMagDist(distData);
    } catch (err) {
      console.error('Error fetching dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 30000); // refresh every 30s
    return () => clearInterval(interval);
  }, [minMagFilter, searchTerm]);

  // Merge incoming SSE events dynamically
  useEffect(() => {
    if (newEventsFromSSE.length > 0) {
      setEvents((prev) => {
        const existingIds = new Set(prev.map((e) => e.id));
        const toAdd = newEventsFromSSE.filter((e) => !existingIds.has(e.id));
        return [...toAdd, ...prev];
      });
    }
  }, [newEventsFromSSE]);

  if (loading && !kpis) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="flex flex-col items-center gap-3">
          <div className="animate-spin rounded-full h-8 w-8 border-2 border-sky-500 border-t-transparent"></div>
          <span className="text-sm text-slate-400">Cargando telemetría sísmica...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* KPI Cards Row */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        {/* Total Events */}
        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl shadow-lg relative overflow-hidden">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Sismos (24h)</span>
            <Activity className="w-4 h-4 text-sky-400" />
          </div>
          <div className="text-2xl font-extrabold text-slate-100">{kpis?.events_24h ?? 0}</div>
          <div className="text-[11px] text-slate-500 mt-1 flex items-center gap-1">
            <Clock className="w-3 h-3" />
            <span>Último: {kpis?.last_earthquake_time ? new Date(kpis.last_earthquake_time).toLocaleTimeString() : 'N/A'}</span>
          </div>
        </div>

        {/* Max Magnitude */}
        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl shadow-lg relative overflow-hidden">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Magnitud Máx</span>
            <TrendingUp className="w-4 h-4 text-rose-400" />
          </div>
          <div className="text-2xl font-extrabold text-rose-400">M {kpis?.max_magnitude_24h.toFixed(1) ?? '0.0'}</div>
          <div className="text-[11px] text-slate-500 mt-1">Pico máximo en 24h</div>
        </div>

        {/* Avg Magnitude */}
        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl shadow-lg relative overflow-hidden">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Magnitud Promedio</span>
            <BarChart3 className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-extrabold text-amber-400">M {kpis?.avg_magnitude_24h.toFixed(1) ?? '0.0'}</div>
          <div className="text-[11px] text-slate-500 mt-1">Nivel base global</div>
        </div>

        {/* Tsunami Alerts */}
        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl shadow-lg relative overflow-hidden">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Alertas Tsunami</span>
            <Waves className="w-4 h-4 text-cyan-400" />
          </div>
          <div className={`text-2xl font-extrabold ${(kpis?.tsunami_alerts_24h ?? 0) > 0 ? 'text-rose-500 animate-pulse' : 'text-slate-100'}`}>
            {kpis?.tsunami_alerts_24h ?? 0}
          </div>
          <div className="text-[11px] text-slate-500 mt-1">Disparos de advertencia</div>
        </div>

        {/* Quality Score */}
        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl shadow-lg relative overflow-hidden">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Calidad de Datos</span>
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-extrabold text-emerald-400">{kpis?.last_quality_score ?? 100}%</div>
          <div className="text-[11px] text-slate-500 mt-1">Pandera Quality Gate</div>
        </div>
      </div>

      {/* Main Interactive Grid: Map + Event Feed */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <SeismicMap
            events={events}
            selectedEventId={selectedEventId}
            onSelectEvent={(id) => setSelectedEventId(id)}
          />
        </div>
        <div>
          <EventFeed
            events={events}
            totalEvents={totalEvents}
            selectedEventId={selectedEventId}
            onSelectEvent={(id) => setSelectedEventId(id)}
            minMagFilter={minMagFilter}
            setMinMagFilter={setMinMagFilter}
            searchTerm={searchTerm}
            setSearchTerm={setSearchTerm}
          />
        </div>
      </div>

      {/* Magnitude Distribution & Activity Summary */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {magDist.map((item, idx) => (
          <div key={idx} className="bg-slate-900/60 border border-slate-800/80 p-4 rounded-xl flex items-center justify-between">
            <div>
              <div className="text-xs text-slate-400">{item.tier}</div>
              <div className="text-lg font-bold text-slate-100 mt-0.5">{item.count} eventos</div>
            </div>
            <div className="w-8 h-8 rounded-full bg-slate-800 flex items-center justify-center text-xs font-bold text-slate-400">
              #{idx + 1}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
