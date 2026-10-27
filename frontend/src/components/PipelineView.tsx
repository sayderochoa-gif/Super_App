import React, { useState, useEffect } from 'react';
import { PipelineStatus, QualityAudit } from '../types';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { BackfillModal } from './BackfillModal';
import {
  ShieldCheck,
  CheckCircle2,
  Clock,
  Play,
  RefreshCw,
  X,
  Server
} from 'lucide-react';

export const PipelineView: React.FC = () => {
  const { isAdmin } = useAuth();
  const [status, setStatus] = useState<PipelineStatus | null>(null);
  const [qualityHistory, setQualityHistory] = useState<QualityAudit[]>([]);
  const [isBackfillOpen, setIsBackfillOpen] = useState(false);
  const [actionSuccessMsg, setActionSuccessMsg] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const loadPipelineData = async () => {
    try {
      setLoading(true);
      const [pStatus, qHist] = await Promise.all([
        api.getPipelineStatus(),
        api.getQualityHistory(10)
      ]);
      setStatus(pStatus);
      setQualityHistory(qHist);
    } catch (err) {
      console.error('Error fetching pipeline status:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPipelineData();
  }, [isAdmin]);

  const handleRegenerateReports = async () => {
    if (!isAdmin) return;
    try {
      const res = await api.triggerReportRegenerate();
      setActionSuccessMsg(res.message);
    } catch (err: any) {
      alert(`Error: ${err.message}`);
    }
  };

  const dagNamesMap: Record<string, string> = {
    dag_ingestion_realtime: 'Ingesta Real-Time (USGS)',
    dag_transformation_quality: 'Transformación & Quality Gate',
    dag_ai_daily_report: 'Reporte Diario IA & Anomalías',
    dag_backfill_historical: 'Backfill Histórico Parametrizado'
  };

  return (
    <div className="space-y-5">
      
      {/* Header and Admin Action Controls */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 p-4 rounded-xl bg-[#0d121c]/90 border border-white/[0.07] shadow-sm">
        <div>
          <div className="flex items-center gap-2">
            <Server className="w-4 h-4 text-sky-400" />
            <h2 className="text-sm font-bold text-white font-mono uppercase tracking-wider">
              Orquestación & Observabilidad del Pipeline
            </h2>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            Monitoreo en tiempo real de Apache Airflow 2.8+ y certificación de calidad con Pandera
          </p>
        </div>

        {isAdmin && (
          <div className="flex items-center gap-2">
            <button
              onClick={() => setIsBackfillOpen(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-purple-600/90 hover:bg-purple-600 text-white text-xs font-mono font-semibold rounded-lg shadow-sm transition-all"
            >
              <Play className="w-3 h-3" />
              <span>Backfill Manual (Admin)</span>
            </button>

            <button
              onClick={handleRegenerateReports}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-900 hover:bg-slate-800 text-slate-300 text-xs font-mono font-medium rounded-lg border border-white/[0.07] transition-all"
            >
              <RefreshCw className="w-3 h-3" />
              <span>Forzar DAG Reportes</span>
            </button>
          </div>
        )}
      </div>

      {actionSuccessMsg && (
        <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-xs rounded-lg flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <span>{actionSuccessMsg}</span>
          </div>
          <button onClick={() => setActionSuccessMsg(null)} className="text-slate-400 hover:text-white">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* DAG Health & Quality */}
      <div className="space-y-5">
        {/* Airflow DAG Status Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {status?.dag_statuses &&
            Object.entries(status.dag_statuses).map(([dagId, dagInfo]: [string, any]) => (
              <div
                key={dagId}
                className="p-3.5 rounded-xl bg-[#0d121c]/90 border border-white/[0.06] shadow-sm space-y-2"
              >
                <div className="text-xs font-semibold text-slate-200 truncate">
                  {dagNamesMap[dagId] || dagId}
                </div>
                <div className="flex items-center justify-between">
                  <span className="font-mono text-[10px] text-slate-500">{dagId}</span>
                  <span
                    className={`text-[9px] font-mono font-bold px-2 py-0.5 rounded uppercase ${
                      dagInfo.state === 'success'
                        ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                        : dagInfo.state === 'running'
                        ? 'bg-sky-500/10 text-sky-400 border border-sky-500/20 animate-pulse'
                        : 'bg-slate-800 text-slate-400 border border-white/[0.05]'
                    }`}
                  >
                    {dagInfo.state || 'ACTIVO'}
                  </span>
                </div>
              </div>
            ))}
        </div>

        {/* Freshness & Quality Gate Summary */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          <div className="p-4 rounded-xl bg-[#0d121c]/90 border border-white/[0.06] shadow-sm space-y-2">
            <div className="flex items-center justify-between text-slate-400">
              <span className="text-[10px] font-mono uppercase tracking-wider">Frescura del Feed</span>
              <Clock className="w-3.5 h-3.5 text-sky-400" />
            </div>
            <div className="text-2xl font-bold font-mono text-white">
              {status?.data_freshness_hours !== null ? `${status?.data_freshness_hours} h` : 'N/A'}
            </div>
            <div className="text-xs">
              {status?.is_fresh ? (
                <span className="text-emerald-400 font-mono text-[11px]">✓ Conforme al SLA (&le; 6h)</span>
              ) : (
                <span className="text-rose-400 font-mono text-[11px]">⚠ Desfase mayor a 6h</span>
              )}
            </div>
          </div>

          <div className="md:col-span-2 p-4 rounded-xl bg-[#0d121c]/90 border border-white/[0.06] shadow-sm space-y-3">
            <div className="flex items-center justify-between text-slate-400">
              <span className="text-[10px] font-mono uppercase tracking-wider">
                Última Evaluación Quality Gate (Pandera)
              </span>
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            </div>

            {status?.latest_quality_audit ? (
              <div className="grid grid-cols-3 gap-3 text-center">
                <div className="p-2.5 rounded-lg bg-slate-900/60 border border-white/[0.05]">
                  <div className="text-[10px] font-mono uppercase text-slate-400">Quality Score</div>
                  <div className="text-xl font-bold font-mono text-emerald-400 mt-0.5">
                    {status.latest_quality_audit.quality_score}%
                  </div>
                </div>
                <div className="p-2.5 rounded-lg bg-slate-900/60 border border-white/[0.05]">
                  <div className="text-[10px] font-mono uppercase text-slate-400">Aprobados</div>
                  <div className="text-xl font-bold font-mono text-slate-100 mt-0.5">
                    {status.latest_quality_audit.passed_records}
                  </div>
                </div>
                <div className="p-2.5 rounded-lg bg-slate-900/60 border border-white/[0.05]">
                  <div className="text-[10px] font-mono uppercase text-slate-400">Rechazados</div>
                  <div className="text-xl font-bold font-mono text-rose-400 mt-0.5">
                    {status.latest_quality_audit.rejected_records}
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-xs text-slate-500 py-2">No hay auditorías registradas todavía.</div>
            )}
          </div>
        </div>

        {/* Quality Audit History Table */}
        <div className="p-4 rounded-xl bg-[#0d121c]/90 border border-white/[0.06] shadow-sm space-y-3">
          <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-semibold">
            Historial de Auditorías de Calidad
          </span>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-slate-900/80 text-slate-400 uppercase text-[10px] border-b border-white/[0.05]">
                <tr>
                  <th className="py-2 px-3">Fecha Evaluación</th>
                  <th className="py-2 px-3">Run ID</th>
                  <th className="py-2 px-3">Total</th>
                  <th className="py-2 px-3">Aprobados</th>
                  <th className="py-2 px-3">Rechazados</th>
                  <th className="py-2 px-3">Score</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/[0.03] text-slate-300">
                {qualityHistory.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-800/30">
                    <td className="py-2 px-3 text-slate-400">{new Date(item.evaluated_at).toLocaleString()}</td>
                    <td className="py-2 px-3 text-slate-500 text-[11px] truncate max-w-[200px]">{item.dag_run_id}</td>
                    <td className="py-2 px-3 text-white font-bold">{item.total_records}</td>
                    <td className="py-2 px-3 text-emerald-400">{item.passed_records}</td>
                    <td className="py-2 px-3 text-rose-400">{item.rejected_records}</td>
                    <td className="py-2 px-3 font-bold text-emerald-400">{item.quality_score}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Backfill Modal */}
      <BackfillModal
        isOpen={isBackfillOpen}
        onClose={() => setIsBackfillOpen(false)}
        onSuccess={(msg) => setActionSuccessMsg(msg)}
      />
    </div>
  );
};
