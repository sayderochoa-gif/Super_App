import React, { useState, useEffect } from 'react';
import { KPIs, Earthquake, TimeseriesPoint } from '../types';
import { api } from '../services/api';
import { SeismicMap } from './SeismicMap';
import { EventFeed } from './EventFeed';
import { Activity, ShieldCheck, Waves, TrendingUp, BarChart2, Clock, Globe } from 'lucide-react';

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
          limit: 500
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
    const interval = setInterval(loadData, 20000); // 20s auto-refresh
    return () => clearInterval(interval);
  }, [minMagFilter, searchTerm]);

  // Merge live incoming SSE events dynamically
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
      <div className="flex items-center justify-center h-[500px]">
        <div className="flex flex-col items-center gap-3">
          <div className="animate-spin rounded-full h-6 w-6 border-2 border-sky-500 border-t-transparent"></div>
          <span className="text-xs font-mono text-slate-400">Sincronizando telemetría sísmica...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      
      {/* Sleek KPI Metric Row */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-3">
        {/* Metric 1: 24h Count */}
        <div className="p-4 rounded-xl bg-[#0d121c]/90 border border-white/[0.07] shadow-sm space-y-1.5">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400">Eventos (24h)</span>
            <Activity className="w-3.5 h-3.5 text-sky-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-white tracking-tight">
            {kpis?.events_24h ?? 0}
          </div>
          <div className="flex items-center gap-1.5 text-[10px] text-slate-500 font-mono">
            <Clock className="w-2.5 h-2.5" />
            <span>Último: {kpis?.last_earthquake_time ? new Date(kpis.last_earthquake_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'N/A'}</span>
          </div>
        </div>

        {/* Metric 2: Max Mag */}
        <div className="p-4 rounded-xl bg-[#0d121c]/90 border border-white/[0.07] shadow-sm space-y-1.5">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400">Magnitud Pico</span>
            <TrendingUp className="w-3.5 h-3.5 text-rose-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-rose-400 tracking-tight">
            M {kpis?.max_magnitude_24h.toFixed(1) ?? '0.0'}
          </div>
          <div className="text-[10px] text-slate-500 font-mono">
            Umbral máximo registrado
          </div>
        </div>

        {/* Metric 3: Avg Mag */}
        <div className="p-4 rounded-xl bg-[#0d121c]/90 border border-white/[0.07] shadow-sm space-y-1.5">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400">Promedio</span>
            <BarChart2 className="w-3.5 h-3.5 text-amber-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-amber-400 tracking-tight">
            M {kpis?.avg_magnitude_24h.toFixed(1) ?? '0.0'}
          </div>
          <div className="text-[10px] text-slate-500 font-mono">
            Media ponderada 24h
          </div>
        </div>

        {/* Metric 4: Tsunami Alerts */}
        <div className="p-4 rounded-xl bg-[#0d121c]/90 border border-white/[0.07] shadow-sm space-y-1.5">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400">Alertas Tsunami</span>
            <Waves className="w-3.5 h-3.5 text-cyan-400" />
          </div>
          <div className={`text-2xl font-bold font-mono tracking-tight ${(kpis?.tsunami_alerts_24h ?? 0) > 0 ? 'text-rose-400 animate-pulse' : 'text-slate-100'}`}>
            {kpis?.tsunami_alerts_24h ?? 0}
          </div>
          <div className="text-[10px] text-slate-400 font-mono">
            {(kpis?.tsunami_alerts_24h ?? 0) > 0 ? 'Eventos con alerta costera activa' : 'Sin alertas vigentes'}
          </div>
        </div>

        {/* Metric 5: Quality Gate */}
        <div className="p-4 rounded-xl bg-[#0d121c]/90 border border-white/[0.07] shadow-sm space-y-1.5 col-span-2 lg:col-span-1">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400">Calidad (Pandera)</span>
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-emerald-400 tracking-tight">
            {kpis?.last_quality_score ?? 100}%
          </div>
          <div className="text-[10px] text-slate-500 font-mono">
            Registros íntegros validados
          </div>
        </div>
      </div>

      {/* Main Grid: Interactive Map + Event Feed */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        <div className="lg:col-span-8">
          <SeismicMap
            events={events}
            selectedEventId={selectedEventId}
            onSelectEvent={(id) => setSelectedEventId(id)}
          />
        </div>
        <div className="lg:col-span-4">
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

      {/* Magnitude Tiers Breakdown Bar */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {magDist.map((item, idx) => (
          <div
            key={idx}
            className="p-3.5 rounded-xl bg-[#0d121c]/70 border border-white/[0.05] flex items-center justify-between"
          >
            <div>
              <div className="text-[11px] font-medium text-slate-400">{item.tier}</div>
              <div className="text-base font-bold font-mono text-slate-100 mt-0.5">{item.count}</div>
            </div>
            <span className="text-[10px] font-mono text-slate-500 px-2 py-0.5 rounded bg-slate-900 border border-white/[0.04]">
              {totalEvents > 0 ? `${Math.round((item.count / totalEvents) * 100)}%` : '0%'}
            </span>
          </div>
        ))}
      </div>

    </div>
  );
};
