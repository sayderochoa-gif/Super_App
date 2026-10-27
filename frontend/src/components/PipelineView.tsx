import React, { useState, useEffect } from 'react';
import { PipelineStatus, QualityAudit, QuarantineRecord } from '../types';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { BackfillModal } from './BackfillModal';
import {
  Database,
  ShieldAlert,
  ShieldCheck,
  CheckCircle2,
  Clock,
  Play,
  RefreshCw,
  Eye,
  FileCode,
  X,
  Server
} from 'lucide-react';

export const PipelineView: React.FC = () => {
  const { isAdmin } = useAuth();
  const [status, setStatus] = useState<PipelineStatus | null>(null);
  const [qualityHistory, setQualityHistory] = useState<QualityAudit[]>([]);
  const [quarantineRecords, setQuarantineRecords] = useState<QuarantineRecord[]>([]);
  const [quarantineTotal, setQuarantineTotal] = useState<number>(0);
  const [activeTab, setActiveTab] = useState<'health' | 'quarantine'>('health');
  const [selectedRawData, setSelectedRawData] = useState<any | null>(null);
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

      if (isAdmin) {
        const qData = await api.getQuarantine(50, 0);
        setQuarantineRecords(qData.items);
        setQuarantineTotal(qData.total);
      }
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

      {/* Tabs navigation */}
      <div className="flex items-center gap-1 border-b border-white/[0.06] pb-2 text-xs">
        <button
          onClick={() => setActiveTab('health')}
          className={`px-3 py-1.5 rounded-lg font-mono font-medium transition-all ${
            activeTab === 'health'
              ? 'bg-slate-800 text-white shadow-sm border border-white/[0.08]'
              : 'text-slate-400 hover:text-white hover:bg-slate-800/40'
          }`}
        >
          Estado de DAGs & Frescura
        </button>

        {isAdmin && (
          <button
            onClick={() => setActiveTab('quarantine')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-mono font-medium transition-all ${
              activeTab === 'quarantine'
                ? 'bg-purple-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-white hover:bg-slate-800/40'
            }`}
          >
            <ShieldAlert className="w-3.5 h-3.5" />
            <span>Cuarentena ({quarantineTotal})</span>
            <span className="text-[9px] bg-purple-950 px-1 py-0.2 rounded text-purple-300 border border-purple-400/20">
              Admin
            </span>
          </button>
        )}
      </div>

      {/* TAB 1: DAG Health & Quality */}
      {activeTab === 'health' && (
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
      )}

      {/* TAB 2: Quarantine Table (Admin Only) */}
      {activeTab === 'quarantine' && isAdmin && (
        <div className="p-4 rounded-xl bg-[#0d121c]/90 border border-white/[0.06] shadow-sm space-y-3">
          <div className="flex items-center justify-between border-b border-white/[0.06] pb-3">
            <div>
              <span className="text-xs font-bold text-white font-mono uppercase tracking-wider flex items-center gap-1.5">
                <ShieldAlert className="w-3.5 h-3.5 text-rose-400" />
                <span>Registros Aislados en Cuarentena</span>
              </span>
              <p className="text-[11px] text-slate-400 mt-0.5">
                Eventos descartados para preservar la integridad analítica y modelos predictivos
              </p>
            </div>
            <span className="text-[10px] font-mono bg-rose-500/10 text-rose-300 border border-rose-500/20 px-2 py-0.5 rounded-full">
              {quarantineTotal} eventos
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-slate-900/80 text-slate-400 uppercase text-[10px] border-b border-white/[0.05]">
                <tr>
                  <th className="py-2 px-3">ID Evento</th>
                  <th className="py-2 px-3">Fecha de Aislamiento</th>
                  <th className="py-2 px-3">Motivo de Rechazo</th>
                  <th className="py-2 px-3 text-right">Detalle</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/[0.03] text-slate-300">
                {quarantineRecords.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="py-6 text-center text-slate-500 text-xs font-sans">
                      No hay registros en cuarentena. La totalidad de eventos ha pasado las reglas de calidad.
                    </td>
                  </tr>
                ) : (
                  quarantineRecords.map((item) => (
                    <tr key={item.id} className="hover:bg-slate-800/30">
                      <td className="py-2 px-3 text-slate-200 font-bold">{item.source_id}</td>
                      <td className="py-2 px-3 text-slate-400">{new Date(item.rejected_at).toLocaleString()}</td>
                      <td className="py-2 px-3">
                        <span className="text-rose-400 bg-rose-500/10 px-2 py-0.5 rounded text-[11px]">
                          {item.reason}
                        </span>
                      </td>
                      <td className="py-2 px-3 text-right">
                        <button
                          onClick={() => setSelectedRawData(item.raw_data)}
                          className="px-2 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded text-[11px] transition-colors"
                        >
                          Ver Raw JSON
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Raw Payload Inspector Modal */}
      {selectedRawData && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
          <div className="bg-[#0f141f] border border-white/[0.1] rounded-2xl max-w-2xl w-full p-5 shadow-2xl relative space-y-4">
            <div className="flex items-center justify-between border-b border-white/[0.06] pb-3">
              <div className="flex items-center gap-2">
                <FileCode className="w-4 h-4 text-sky-400" />
                <h3 className="font-bold text-slate-100 text-xs font-mono uppercase tracking-wider">
                  Payload Crudo del Evento
                </h3>
              </div>
              <button
                onClick={() => setSelectedRawData(null)}
                className="text-slate-400 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <pre className="bg-[#070a10] p-4 rounded-xl text-xs font-mono text-emerald-400 max-h-96 overflow-y-auto border border-white/[0.05]">
              {JSON.stringify(selectedRawData, null, 2)}
            </pre>

            <div className="text-right">
              <button
                onClick={() => setSelectedRawData(null)}
                className="px-3.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-mono rounded-lg transition-colors"
              >
                Cerrar Visor
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Backfill Modal */}
      <BackfillModal
        isOpen={isBackfillOpen}
        onClose={() => setIsBackfillOpen(false)}
        onSuccess={(msg) => setActionSuccessMsg(msg)}
      />
    </div>
  );
};
