import React, { useState, useEffect } from 'react';
import { AIReport, Anomaly } from '../types';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { FileText, Download, Printer, AlertTriangle, Cpu, Calendar, CheckCircle2, RefreshCw } from 'lucide-react';

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

  const handleExportCSV = () => {
    const token = localStorage.getItem('sismowatch_token');
    window.open(`/api/reports/export?export_type=csv&target=reports&token=${token}`, '_blank');
  };

  const handleExportPrintable = () => {
    const token = localStorage.getItem('sismowatch_token');
    window.open(`/api/reports/export?export_type=html&target=reports&token=${token}`, '_blank');
  };

  return (
    <div className="space-y-6">
      {/* Top Banner and Actions */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 bg-slate-900 border border-slate-800 p-5 rounded-xl shadow-lg">
        <div>
          <div className="flex items-center gap-2">
            <Cpu className="w-5 h-5 text-sky-400" />
            <h2 className="text-lg font-bold text-slate-100">Reportes Ejecutivos & Inteligencia de Anomalías</h2>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Narrativas analíticas generadas automáticamente con validación determinista y detección no supervisada de enjambres.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {/* Export Buttons */}
          <button
            onClick={handleExportCSV}
            className="flex items-center gap-1.5 px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-lg border border-slate-700 transition-colors"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Exportar CSV</span>
          </button>

          <button
            onClick={handleExportPrintable}
            className="flex items-center gap-1.5 px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-lg border border-slate-700 transition-colors"
          >
            <Printer className="w-3.5 h-3.5" />
            <span>Vista Imprimible / PDF</span>
          </button>

          {/* Admin-only Regenerate Button */}
          {isAdmin && (
            <button
              onClick={handleRegenerateReport}
              disabled={regenerating}
              className="flex items-center gap-1.5 px-3 py-2 bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold rounded-lg shadow-md transition-all disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${regenerating ? 'animate-spin' : ''}`} />
              <span>Regenerar Reporte (Admin)</span>
            </button>
          )}
        </div>
      </div>

      {actionMessage && (
        <div className="p-3 bg-sky-950/40 border border-sky-500/30 text-sky-300 text-xs rounded-lg flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-sky-400 flex-shrink-0" />
          <span>{actionMessage}</span>
        </div>
      )}

      {/* Main Grid: Narrative reader + History / Anomalies */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Narrative & Grounded KPIs (Left 2 cols) */}
        <div className="lg:col-span-2 space-y-6">
          {selectedReport ? (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl space-y-5">
              {/* Report Header Metadata */}
              <div className="flex items-center justify-between border-b border-slate-800 pb-4">
                <div className="flex items-center gap-3">
                  <div className="bg-sky-500/10 p-2.5 rounded-lg border border-sky-500/20">
                    <FileText className="w-6 h-6 text-sky-400" />
                  </div>
                  <div>
                    <h3 className="font-bold text-slate-100 text-base">
                      Informe Diario: {selectedReport.report_date}
                    </h3>
                    <div className="flex items-center gap-3 text-xs text-slate-400 mt-0.5">
                      <span>Modelo: <b className="text-slate-300 font-mono">{selectedReport.model_name}</b></span>
                      <span>Latencia: <b>{selectedReport.latency_sec}s</b></span>
                      <span>Tokens: <b>{selectedReport.tokens_used}</b></span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-1 text-xs text-emerald-400 bg-emerald-950/40 border border-emerald-500/30 px-2.5 py-1 rounded-full font-medium">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>Verificado Determinista</span>
                </div>
              </div>

              {/* Structured KPIs Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="bg-slate-800/60 p-3 rounded-lg border border-slate-700/60 text-center">
                  <div className="text-xs text-slate-400">Total Eventos</div>
                  <div className="text-xl font-bold text-slate-100 mt-1">
                    {selectedReport.structured_kpis?.total_events ?? 0}
                  </div>
                </div>
                <div className="bg-slate-800/60 p-3 rounded-lg border border-slate-700/60 text-center">
                  <div className="text-xs text-slate-400">Magnitud Máx</div>
                  <div className="text-xl font-bold text-rose-400 mt-1">
                    M {selectedReport.structured_kpis?.max_magnitude ?? 0.0}
                  </div>
                </div>
                <div className="bg-slate-800/60 p-3 rounded-lg border border-slate-700/60 text-center">
                  <div className="text-xs text-slate-400">Magnitud Prom</div>
                  <div className="text-xl font-bold text-amber-400 mt-1">
                    M {selectedReport.structured_kpis?.avg_magnitude ?? 0.0}
                  </div>
                </div>
                <div className="bg-slate-800/60 p-3 rounded-lg border border-slate-700/60 text-center">
                  <div className="text-xs text-slate-400">Región Activa</div>
                  <div className="text-xs font-semibold text-sky-400 mt-2 truncate">
                    {selectedReport.structured_kpis?.most_active_region ?? 'Global'}
                  </div>
                </div>
              </div>

              {/* Narrative Content */}
              <div className="bg-slate-950/70 border border-slate-800 rounded-lg p-5 font-sans text-sm text-slate-200 leading-relaxed whitespace-pre-wrap">
                {selectedReport.narrative_text}
              </div>
            </div>
          ) : (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-12 text-center text-slate-400 text-sm">
              No hay reportes diarios generados aún. Los reportes se ejecutan automáticamente cada 24 horas.
            </div>
          )}
        </div>

        {/* Sidebar: Historical Reports & Detected Anomalies */}
        <div className="space-y-6">
          {/* History Picker */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-lg">
            <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-3 flex items-center gap-1.5">
              <Calendar className="w-3.5 h-3.5 text-sky-400" />
              <span>Historial de Reportes</span>
            </h4>
            <div className="space-y-1.5 max-h-48 overflow-y-auto">
              {reports.map((rep) => (
                <button
                  key={rep.id}
                  onClick={() => setSelectedReport(rep)}
                  className={`w-full text-left px-3 py-2 rounded-lg text-xs font-medium transition-colors flex items-center justify-between ${
                    selectedReport?.id === rep.id
                      ? 'bg-sky-600 text-white'
                      : 'bg-slate-800/60 text-slate-300 hover:bg-slate-800'
                  }`}
                >
                  <span>Fecha: {rep.report_date}</span>
                  <span className="text-[10px] opacity-80">{rep.structured_kpis?.total_events || 0} evts</span>
                </button>
              ))}
            </div>
          </div>

          {/* Anomaly Detection Feed */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-lg">
            <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-3 flex items-center gap-1.5">
              <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
              <span>Anomalías Detectadas ({anomalies.length})</span>
            </h4>

            <div className="space-y-3 max-h-96 overflow-y-auto pr-1">
              {anomalies.length === 0 ? (
                <div className="text-xs text-slate-500 text-center py-4">
                  No se han registrado anomalías críticas en el período reciente.
                </div>
              ) : (
                anomalies.map((anom) => (
                  <div
                    key={anom.id}
                    className="p-3 rounded-lg bg-slate-950/60 border border-amber-500/20 text-xs space-y-1.5"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-amber-400 text-[11px] bg-amber-950/60 px-1.5 py-0.5 rounded border border-amber-500/30">
                        {anom.anomaly_type}
                      </span>
                      <span className="text-[10px] text-slate-500">
                        {new Date(anom.detected_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>

                    <p className="text-slate-200">{anom.description}</p>
                    <div className="text-[10px] text-slate-400 font-mono">
                      Disparador: {anom.metric_trigger}
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
