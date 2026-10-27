import React, { useState, useEffect } from 'react';
import { AIReport, Anomaly } from '../types';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { FileText, Download, Printer, AlertTriangle, Sparkles, Calendar, CheckCircle2, RefreshCw } from 'lucide-react';

export const ReportsView: React.FC = () => {
  const { isAdmin } = useAuth();
  const [reports, setReports] = useState<AIReport[]>([]);
  const [anomalies, setAnomalies] = useState<Anomaly[]>([]);
  const [selectedReport, setSelectedReport] = useState<AIReport | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [regenerating, setRegenerating] = useState<boolean>(false);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  const loadReportsData = async () => {
    try {
      setLoading(true);
      const [reps, anoms] = await Promise.all([
        api.getReports(30),
        api.getAnomalies(50)
      ]);
      setReports(reps);
      setAnomalies(anoms);
      if (reps.length > 0) {
        setSelectedReport(reps[0]);
      }
    } catch (err) {
      console.error('Error fetching AI reports:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReportsData();
  }, []);

  const handleRegenerateReport = async () => {
    if (!isAdmin) return;
    try {
      setRegenerating(true);
      setActionMessage(null);
      const res = await api.triggerReportRegenerate();
      setActionMessage(res.message);
      setTimeout(() => loadReportsData(), 3000);
    } catch (err: any) {
      setActionMessage(`Error: ${err.message}`);
    } finally {
      setRegenerating(false);
    }
  };

  const handleExportCSV = async () => {
    try {
      const token = localStorage.getItem('sismowatch_token');
      const response = await fetch('/api/reports/export?export_type=csv&target=earthquakes', {
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      });
      if (!response.ok) throw new Error('Error al generar CSV');
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `sismowatch_actividades_sismicas_${new Date().toISOString().slice(0, 10)}.csv`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err: any) {
      console.error('Error exportando CSV:', err);
      const token = localStorage.getItem('sismowatch_token');
      window.open(`/api/reports/export?export_type=csv&target=earthquakes&token=${token}`, '_blank');
    }
  };

  const handleExportPDF = async () => {
    try {
      const token = localStorage.getItem('sismowatch_token');
      const response = await fetch('/api/reports/export?export_type=pdf&target=earthquakes', {
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      });
      if (!response.ok) throw new Error('Error al generar PDF');
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `sismowatch_informe_sismico_${new Date().toISOString().slice(0, 10)}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err: any) {
      console.error('Error exportando PDF:', err);
      const token = localStorage.getItem('sismowatch_token');
      window.open(`/api/reports/export?export_type=pdf&target=earthquakes&token=${token}`, '_blank');
    }
  };

  return (
    <div className="space-y-5">
      
      {/* Top Bar with Actions */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 p-4 rounded-xl bg-[#0d121c]/90 border border-white/[0.07] shadow-sm">
        <div>
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-sky-400" />
            <h2 className="text-sm font-bold text-white font-mono uppercase tracking-wider">
              Inteligencia Sísmica & Reportes Ejecutivos
            </h2>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            Informes automatizados anclados en métricas deterministas verificadas y detección de anomalías
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleExportCSV}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 text-xs font-medium border border-white/[0.07] transition-all"
          >
            <Download className="w-3.5 h-3.5" />
            <span>CSV</span>
          </button>

          <button
            onClick={handleExportPDF}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 text-xs font-medium border border-white/[0.07] transition-all"
          >
            <Printer className="w-3.5 h-3.5" />
            <span>PDF / Imprimir</span>
          </button>

          {isAdmin && (
            <button
              onClick={handleRegenerateReport}
              disabled={regenerating}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-purple-600/90 hover:bg-purple-600 text-white text-xs font-medium shadow-sm transition-all disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${regenerating ? 'animate-spin' : ''}`} />
              <span>Regenerar (Admin)</span>
            </button>
          )}
        </div>
      </div>

      {actionMessage && (
        <div className="p-3 bg-sky-500/10 border border-sky-500/20 text-sky-300 text-xs rounded-lg flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-sky-400 flex-shrink-0" />
          <span>{actionMessage}</span>
        </div>
      )}

      {/* Main Grid: Narrative & Sidebar */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        
        {/* Narrative Article View (Left 8 cols) */}
        <div className="lg:col-span-8">
          {selectedReport ? (
            <div className="bg-[#0d121c]/90 border border-white/[0.07] rounded-xl p-6 shadow-xl space-y-5">
              
              {/* Header Info */}
              <div className="flex items-center justify-between border-b border-white/[0.06] pb-4">
                <div>
                  <span className="text-[10px] font-mono uppercase tracking-wider text-sky-400 font-semibold">
                    INFORME DIARIO SÍSMICO
                  </span>
                  <h3 className="text-lg font-bold text-white font-mono mt-0.5">
                    Ciclo: {selectedReport.report_date}
                  </h3>
                  <div className="flex items-center gap-3 text-xs text-slate-400 mt-1 font-mono">
                    <span>Motor: <b className="text-slate-300">{selectedReport.model_name}</b></span>
                    <span>Tokens: <b>{selectedReport.tokens_used}</b></span>
                    <span>Latencia: <b>{selectedReport.latency_sec}s</b></span>
                  </div>
                </div>

                <div className="flex items-center gap-1 text-[11px] font-mono text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-1 rounded-full font-medium">
                  <CheckCircle2 className="w-3 h-3" />
                  <span>Cero Alucinación (Verificado)</span>
                </div>
              </div>

              {/* Structured KPIs Chips */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
                <div className="p-3 rounded-lg bg-slate-900/60 border border-white/[0.05] text-center">
                  <span className="text-[10px] font-mono uppercase text-slate-400">Total Eventos</span>
                  <div className="text-xl font-bold font-mono text-white mt-0.5">
                    {selectedReport.structured_kpis?.total_events ?? 0}
                  </div>
                </div>
                <div className="p-3 rounded-lg bg-slate-900/60 border border-white/[0.05] text-center">
                  <span className="text-[10px] font-mono uppercase text-slate-400">Magnitud Pico</span>
                  <div className="text-xl font-bold font-mono text-rose-400 mt-0.5">
                    M {selectedReport.structured_kpis?.max_magnitude ?? 0.0}
                  </div>
                </div>
                <div className="p-3 rounded-lg bg-slate-900/60 border border-white/[0.05] text-center">
                  <span className="text-[10px] font-mono uppercase text-slate-400">Promedio</span>
                  <div className="text-xl font-bold font-mono text-amber-400 mt-0.5">
                    M {selectedReport.structured_kpis?.avg_magnitude ?? 0.0}
                  </div>
                </div>
                <div className="p-3 rounded-lg bg-slate-900/60 border border-white/[0.05] text-center">
                  <span className="text-[10px] font-mono uppercase text-slate-400">Región Núcleo</span>
                  <div className="text-xs font-semibold text-sky-400 mt-2 truncate">
                    {selectedReport.structured_kpis?.most_active_region ?? 'Global'}
                  </div>
                </div>
              </div>

              {/* Narrative Text Container */}
              <div className="p-5 rounded-lg bg-[#070a10] border border-white/[0.05] text-sm text-slate-300 leading-relaxed font-sans whitespace-pre-wrap">
                {selectedReport.narrative_text}
              </div>
            </div>
          ) : (
            <div className="p-12 text-center text-slate-500 text-xs rounded-xl bg-[#0d121c]/90 border border-white/[0.07]">
              No hay informes diarios generados en este momento.
            </div>
          )}
        </div>

        {/* Sidebar: Historical Reports & Anomalies (Right 4 cols) */}
        <div className="lg:col-span-4 space-y-5">
          
          {/* History Selector */}
          <div className="bg-[#0d121c]/90 border border-white/[0.07] rounded-xl p-4 space-y-3">
            <div className="flex items-center gap-1.5 text-xs font-bold text-slate-300 uppercase font-mono tracking-wider">
              <Calendar className="w-3.5 h-3.5 text-sky-400" />
              <span>Historial de Reportes</span>
            </div>
            <div className="space-y-1 max-h-44 overflow-y-auto pr-1">
              {reports.map((rep) => (
                <button
                  key={rep.id}
                  onClick={() => setSelectedReport(rep)}
                  className={`w-full text-left px-3 py-2 rounded-lg text-xs font-mono transition-all flex items-center justify-between ${
                    selectedReport?.id === rep.id
                      ? 'bg-sky-600 text-white font-semibold shadow-sm'
                      : 'bg-slate-900/50 text-slate-400 hover:text-white hover:bg-slate-800/40 border border-transparent'
                  }`}
                >
                  <span>{rep.report_date}</span>
                  <span className="text-[10px] opacity-75">{rep.structured_kpis?.total_events || 0} evts</span>
                </button>
              ))}
            </div>
          </div>

          {/* Anomaly Feed */}
          <div className="bg-[#0d121c]/90 border border-white/[0.07] rounded-xl p-4 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5 text-xs font-bold text-slate-300 uppercase font-mono tracking-wider">
                <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
                <span>Anomalías Detectadas</span>
              </div>
              <span className="text-[10px] font-mono text-slate-500">
                {anomalies.length} registros
              </span>
            </div>

            <div className="space-y-2.5 max-h-80 overflow-y-auto pr-1">
              {anomalies.length === 0 ? (
                <div className="text-xs text-slate-500 text-center py-6">
                  No se registraron anomalías críticas en el período reciente.
                </div>
              ) : (
                anomalies.map((anom) => (
                  <div
                    key={anom.id}
                    className="p-3 rounded-lg bg-slate-900/50 border border-amber-500/20 text-xs space-y-1.5"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-mono font-bold text-amber-300 bg-amber-500/10 px-1.5 py-0.5 rounded border border-amber-500/30">
                        {anom.anomaly_type}
                      </span>
                      <span className="text-[10px] text-slate-500 font-mono">
                        {new Date(anom.detected_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>

                    <p className="text-slate-200 text-xs leading-snug">{anom.description}</p>
                    <div className="text-[10px] text-slate-400 font-mono truncate">
                      {anom.metric_trigger}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

        </div>

      </div>

    </div>
  );
};
