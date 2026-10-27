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
  X
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

      // If user is admin, fetch quarantine records
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
    dag_ingestion_realtime: 'Ingesta en Tiempo Real (USGS)',
    dag_transformation_quality: 'Transformación & Quality Gate',
    dag_ai_daily_report: 'Reporte Diario IA & Anomalías',
    dag_backfill_historical: 'Backfill Histórico Parametrizado'
  };

  return (
    <div className="space-y-6">
      {/* Header and Admin Action Controls */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 bg-slate-900 border border-slate-800 p-5 rounded-xl shadow-lg">
        <div>
          <div className="flex items-center gap-2">
            <Database className="w-5 h-5 text-sky-400" />
            <h2 className="text-lg font-bold text-slate-100">Monitoreo de Pipelines & Calidad de Datos</h2>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Orquestación Apache Airflow, auditorías Pandera y cuarentena de anomalías.
          </p>
        </div>

        {/* Action Controls - Strictly Visible to Admin Only */}
        {isAdmin && (
          <div className="flex items-center gap-2">
            <button
              onClick={() => setIsBackfillOpen(true)}
              className="flex items-center gap-1.5 px-3 py-2 bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold rounded-lg shadow-md transition-all"
            >
              <Play className="w-3.5 h-3.5" />
              <span>Disparar Backfill (Admin)</span>
            </button>

            <button
              onClick={handleRegenerateReports}
              className="flex items-center gap-1.5 px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-lg border border-slate-700 transition-all"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Regenerar Reporte (Admin)</span>
            </button>
          </div>
        )}
      </div>

      {actionSuccessMsg && (
        <div className="p-3 bg-emerald-950/40 border border-emerald-500/30 text-emerald-300 text-xs rounded-lg flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <span>{actionSuccessMsg}</span>
          </div>
          <button onClick={() => setActionSuccessMsg(null)} className="text-slate-400 hover:text-white">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Tabs navigation: Health vs Quarantine (Quarantine only visible to admin) */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
        <button
          onClick={() => setActiveTab('health')}
          className={`px-4 py-2 text-xs font-semibold rounded-lg transition-colors ${
            activeTab === 'health'
              ? 'bg-sky-600 text-white'
              : 'text-slate-400 hover:text-white hover:bg-slate-800'
          }`}
        >
          Estado de DAGs y Frescura
        </button>

        {/* Quarantine Tab - Hidden from Viewers */}
        {isAdmin && (
          <button
            onClick={() => setActiveTab('quarantine')}
            className={`flex items-center gap-1.5 px-4 py-2 text-xs font-semibold rounded-lg transition-colors ${
              activeTab === 'quarantine'
                ? 'bg-purple-600 text-white'
                : 'text-slate-400 hover:text-white hover:bg-slate-800'
            }`}
          >
            <ShieldAlert className="w-3.5 h-3.5" />
            <span>Eventos en Cuarentena ({quarantineTotal})</span>
            <span className="text-[10px] bg-purple-900/60 text-purple-300 px-1.5 py-0.2 rounded font-mono">
              Admin
            </span>
          </button>
        )}
      </div>

      {/* TAB 1: DAG Health, Freshness & Quality History */}
      {activeTab === 'health' && (
        <div className="space-y-6">
          {/* Airflow DAG Status Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {status?.dag_statuses &&
              Object.entries(status.dag_statuses).map(([dagId, dagInfo]: [string, any]) => (
                <div
                  key={dagId}
                  className="bg-slate-900 border border-slate-800 p-4 rounded-xl shadow-md space-y-2"
                >
                  <div className="text-xs font-semibold text-slate-300">
                    {dagNamesMap[dagId] || dagId}
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-[11px] text-slate-500">{dagId}</span>
                    <span
                      className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase ${
                        dagInfo.state === 'success'
                          ? 'bg-emerald-950/60 text-emerald-400 border border-emerald-500/30'
                          : dagInfo.state === 'running'
                          ? 'bg-sky-950/60 text-sky-400 border border-sky-500/30 animate-pulse'
                          : 'bg-slate-800 text-slate-400'
                      }`}
                    >
                      {dagInfo.state || 'activo'}
                    </span>
                  </div>
                </div>
              ))}
          </div>

          {/* Freshness & Quality Gate Summary */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl shadow-lg space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                  Frescura del Feed
                </span>
                <Clock className="w-4 h-4 text-sky-400" />
              </div>
              <div className="text-3xl font-extrabold text-slate-100">
                {status?.data_freshness_hours !== null ? `${status?.data_freshness_hours} h` : 'N/A'}
              </div>
              <div className="text-xs text-slate-400">
                {status?.is_fresh ? (
                  <span className="text-emerald-400 font-medium">✓ Dentro del umbral (&le; 6h)</span>
                ) : (
                  <span className="text-rose-400 font-medium">⚠ Alerta: Desfase mayor a 6h</span>
                )}
              </div>
            </div>

            <div className="md:col-span-2 bg-slate-900 border border-slate-800 p-5 rounded-xl shadow-lg space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                  Última Auditoría de Calidad (Pandera)
                </span>
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
              </div>

              {status?.latest_quality_audit ? (
                <div className="grid grid-cols-3 gap-3 text-center pt-2">
                  <div className="bg-slate-800/60 p-3 rounded-lg border border-slate-700/60">
                    <div className="text-xs text-slate-400">Puntaje Calidad</div>
                    <div className="text-2xl font-bold text-emerald-400 mt-1">
                      {status.latest_quality_audit.quality_score}%
                    </div>
                  </div>
                  <div className="bg-slate-800/60 p-3 rounded-lg border border-slate-700/60">
                    <div className="text-xs text-slate-400">Registros Aprobados</div>
                    <div className="text-2xl font-bold text-slate-100 mt-1">
                      {status.latest_quality_audit.passed_records}
                    </div>
                  </div>
                  <div className="bg-slate-800/60 p-3 rounded-lg border border-slate-700/60">
                    <div className="text-xs text-slate-400">Cuarentena (Rechazados)</div>
                    <div className="text-2xl font-bold text-rose-400 mt-1">
                      {status.latest_quality_audit.rejected_records}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-xs text-slate-500 py-4">No hay auditorías registradas todavía.</div>
              )}
            </div>
          </div>

          {/* Quality Audit History Table */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg space-y-3">
            <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
              Historial Reciente de Calidad
            </h4>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-800/60 text-slate-400 uppercase font-semibold text-[10px]">
                  <tr>
                    <th className="py-2 px-3">Fecha Evaluación</th>
                    <th className="py-2 px-3">Run ID</th>
                    <th className="py-2 px-3">Total Evaluados</th>
                    <th className="py-2 px-3">Aprobados</th>
                    <th className="py-2 px-3">Rechazados</th>
                    <th className="py-2 px-3">Score</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800 text-slate-300">
                  {qualityHistory.map((item) => (
                    <tr key={item.id} className="hover:bg-slate-800/40">
                      <td className="py-2.5 px-3">{new Date(item.evaluated_at).toLocaleString()}</td>
                      <td className="py-2.5 px-3 font-mono text-[11px] text-slate-400">{item.dag_run_id}</td>
                      <td className="py-2.5 px-3 font-semibold">{item.total_records}</td>
                      <td className="py-2.5 px-3 text-emerald-400">{item.passed_records}</td>
                      <td className="py-2.5 px-3 text-rose-400">{item.rejected_records}</td>
                      <td className="py-2.5 px-3 font-bold text-emerald-400">{item.quality_score}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: Quarantined Records Table (Admin Only) */}
      {activeTab === 'quarantine' && isAdmin && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div>
              <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-rose-400" />
                <span>Detalle de Registros Aislados en Cuarentena</span>
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Eventos rechazados por el Quality Gate para salvaguardar la integridad analítica.
              </p>
            </div>
            <span className="text-xs font-mono bg-rose-950/60 text-rose-300 border border-rose-500/30 px-2.5 py-1 rounded-full">
              {quarantineTotal} eventos aislados
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-800/60 text-slate-400 uppercase font-semibold text-[10px]">
                <tr>
                  <th className="py-2 px-3">ID Origen</th>
                  <th className="py-2 px-3">Fecha de Rechazo</th>
                  <th className="py-2 px-3">Causa / Violación de Regla</th>
                  <th className="py-2 px-3 text-right">Acción</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800 text-slate-300">
                {quarantineRecords.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="py-8 text-center text-slate-500">
                      No hay registros en cuarentena. Todos los sismos procesados han cumplido el Quality Gate.
                    </td>
                  </tr>
                ) : (
                  quarantineRecords.map((item) => (
                    <tr key={item.id} className="hover:bg-slate-800/40">
                      <td className="py-2.5 px-3 font-mono font-semibold text-slate-200">{item.source_id}</td>
                      <td className="py-2.5 px-3">{new Date(item.rejected_at).toLocaleString()}</td>
                      <td className="py-2.5 px-3">
                        <span className="text-rose-400 bg-rose-950/40 px-2 py-0.5 rounded border border-rose-500/20 font-mono text-[11px]">
                          {item.reason}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 text-right">
                        <button
                          onClick={() => setSelectedRawData(item.raw_data)}
                          className="inline-flex items-center gap-1 px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded text-[11px] font-medium transition-colors"
                        >
                          <Eye className="w-3 h-3" />
                          <span>Ver Payload</span>
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
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-2xl w-full p-6 shadow-2xl relative space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <FileCode className="w-5 h-5 text-sky-400" />
                <h3 className="font-bold text-slate-100 text-sm">Payload Crudo del Evento Rechazado</h3>
              </div>
              <button
                onClick={() => setSelectedRawData(null)}
                className="text-slate-400 hover:text-slate-200"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <pre className="bg-slate-950 p-4 rounded-lg text-xs font-mono text-emerald-400 max-h-96 overflow-y-auto border border-slate-800">
              {JSON.stringify(selectedRawData, null, 2)}
            </pre>

            <div className="text-right">
              <button
                onClick={() => setSelectedRawData(null)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-lg"
              >
                Cerrar
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
