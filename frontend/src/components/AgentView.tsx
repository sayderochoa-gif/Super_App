import React, { useState, useEffect, useRef } from 'react';
import {
  Bot,
  Send,
  RefreshCw,
  Trash2,
  Database,
  Sparkles,
  AlertTriangle,
  Waves,
  BarChart2,
  Terminal,
  ShieldCheck,
  CheckCircle2
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';
import { AgentMessage } from '../types';

export const AgentView: React.FC = () => {
  const { user, isAdmin } = useAuth();

  const getWelcomeText = () => {
    if (isAdmin) {
      return `👋 **¡Hola Administrador ${user?.username || ''}!** Soy **SeismoAgent**, tu asistente inteligente con privilegios de Administrador.\n\nDesde tu cuenta tienes supervisión y control total sobre:\n• **Telemetría Sísmica:** Globo 3D, KPIs en tiempo real y feed exportable.\n• **Reportes IA:** Resumen narrativo diario, anomalías analíticas y botón de regeneración forzada.\n• **Pipeline & Calidad:** Monitoreo de los 4 DAGs de Airflow, SLA de frescura (< 1h), auditorías Pandera, tabla de Cuarentena y ejecución de Backfill Histórico.\n\nPregúntame sobre lo que ves en tus paneles, cómo ejecutar acciones avanzadas o cualquier duda sismológica y de prevención.`;
    }
    return `👋 **¡Hola ${user?.username || ''}!** Soy **SeismoAgent**, tu asistente inteligente para monitoreo y análisis sísmico en tiempo real.\n\nPuedo consultar sismos por magnitud y región, calcular estadísticas, verificar alertas de tsunami o responder cualquier pregunta sobre sismos y protocolos de prevención civil.\n\n*¿En qué puedo ayudarte hoy?*`;
  };

  const [messages, setMessages] = useState<AgentMessage[]>([
    {
      id: 'welcome',
      sender: 'agent',
      text: getWelcomeText(),
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ]);
  const [inputText, setInputText] = useState('');
  const [loading, setLoading] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [showSchemaModal, setShowSchemaModal] = useState(false);
  const [schemaText, setSchemaText] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSendMessage = async (customText?: string) => {
    const textToSend = (customText || inputText).trim();
    if (!textToSend || loading) return;

    const userMsg: AgentMessage = {
      id: `user-${Date.now()}`,
      sender: 'user',
      text: textToSend,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!customText) setInputText('');
    setLoading(true);

    try {
      const res = await api.chatAgent(textToSend);
      const agentMsg: AgentMessage = {
        id: `agent-${Date.now()}`,
        sender: 'agent',
        text: res.response,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages((prev) => [...prev, agentMsg]);
    } catch (err: any) {
      const errorMsg: AgentMessage = {
        id: `err-${Date.now()}`,
        sender: 'agent',
        text: `❌ **Error al consultar el agente:** ${err.message || 'No se pudo contactar al servicio de análisis sísmico.'}`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        isError: true
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  const handleSyncData = async () => {
    setSyncing(true);
    try {
      const res = await api.syncAgent();
      const summary = res.data;
      const syncMsg: AgentMessage = {
        id: `sync-${Date.now()}`,
        sender: 'agent',
        text: `🔄 **Sincronización USGS Completada**\n\n- **Fuente:** \`${summary.feed_title || 'USGS Feed'}\`\n- **Total de sismos leídos:** ${summary.total_fetched ?? 'N/A'}\n- **Nuevos eventos insertados:** ${summary.new_inserted ?? 0}\n- **Eventos existentes actualizados:** ${summary.existing_updated ?? 0}\n- **Marca de tiempo:** \`${summary.timestamp || new Date().toISOString()}\``,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages((prev) => [...prev, syncMsg]);
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          id: `sync-err-${Date.now()}`,
          sender: 'agent',
          text: `❌ Error al sincronizar con USGS: ${err.message}`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          isError: true
        }
      ]);
    } finally {
      setSyncing(false);
    }
  };

  const handleClearChat = async () => {
    try {
      await api.chatAgent('', true);
    } catch (_) {}
    setMessages([
      {
        id: 'reset',
        sender: 'agent',
        text: '🔄 Contexto conversacional reiniciado. Hazme cualquier pregunta sobre los eventos sísmicos.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }
    ]);
  };

  const handleOpenSchema = async () => {
    setShowSchemaModal(true);
    if (!schemaText) {
      try {
        const res = await api.getAgentSchema();
        setSchemaText(res.schema);
      } catch (err: any) {
        setSchemaText(`Error al cargar esquema: ${err.message}`);
      }
    }
  };

  // Helper to render basic Markdown formatting (tables, bold, code)
  const renderFormattedText = (content: string) => {
    // Clean any triple asterisks or raw clutter
    const cleanContent = content.replace(/\*{3,}/g, '').replace(/\*\*\s*\*/g, '').replace(/\*\s*\*\*/g, '');
    const lines = cleanContent.split('\n');
    const elements: React.ReactNode[] = [];
    let tableBuffer: string[] = [];
    let inTable = false;

    const flushTable = (keyPrefix: string) => {
      if (tableBuffer.length === 0) return;
      const headerLine = tableBuffer[0];
      const rowLines = tableBuffer.slice(2); // Skip separator line

      const headers = headerLine
        .split('|')
        .map((h) => h.trim())
        .filter(Boolean);

      elements.push(
        <div key={`${keyPrefix}-table`} className="overflow-x-auto my-3 border border-white/10 rounded-lg">
          <table className="min-w-full text-xs text-left">
            <thead className="bg-slate-800/80 text-sky-400 font-semibold border-b border-white/10">
              <tr>
                {headers.map((h, idx) => (
                  <th key={idx} className="px-3 py-2 whitespace-nowrap">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5 bg-slate-900/60 font-mono">
              {rowLines.map((r, rIdx) => {
                const cells = r
                  .split('|')
                  .map((c) => c.trim())
                  .filter((_, idx, arr) => idx > 0 && idx < arr.length - 1);
                return (
                  <tr key={rIdx} className="hover:bg-slate-800/40">
                    {cells.map((cell, cIdx) => (
                      <td key={cIdx} className="px-3 py-1.5 whitespace-nowrap text-slate-300">
                        {cell}
                      </td>
                    ))}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      );
      tableBuffer = [];
      inTable = false;
    };

    lines.forEach((line, index) => {
      // Check if markdown table row
      if (line.trim().startsWith('|') && line.trim().endsWith('|')) {
        inTable = true;
        tableBuffer.push(line.trim());
        return;
      }

      if (inTable) {
        flushTable(`flush-${index}`);
      }

      // Check bullet items
      if (line.trim().startsWith('- ') || line.trim().startsWith('• ')) {
        const bulletText = line.trim().replace(/^[-•]\s*/, '');
        elements.push(
          <div key={index} className="flex items-start gap-2 my-1 text-slate-200">
            <span className="text-sky-400 font-bold mt-0.5">•</span>
            <div>{renderInlineFormatting(bulletText)}</div>
          </div>
        );
        return;
      }

      // Plain line
      if (line.trim() === '') {
        elements.push(<div key={index} className="h-2" />);
      } else {
        elements.push(
          <div key={index} className="my-1 text-slate-200 leading-relaxed">
            {renderInlineFormatting(line)}
          </div>
        );
      }
    });

    if (inTable) {
      flushTable('flush-final');
    }

    return elements;
  };

  const renderInlineFormatting = (text: string) => {
    // Basic inline bold and code
    const parts = text.split(/(\*\*.*?\*\*|`.*?`)/g);
    return parts.map((part, i) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={i} className="text-white font-semibold">{part.slice(2, -2)}</strong>;
      }
      if (part.startsWith('`') && part.endsWith('`')) {
        return (
          <code key={i} className="bg-slate-800 text-sky-300 px-1.5 py-0.5 rounded text-[11px] font-mono border border-slate-700">
            {part.slice(1, -1)}
          </code>
        );
      }
      return part;
    });
  };

  const ADMIN_PROMPTS = [
    { label: '⚙️ Acciones de Administrador', query: '¿Qué acciones puedo hacer como administrador?' },
    { label: '🛠️ Mi Vista & Paneles', query: '¿Qué veo en mi vista de administrador?' },
    { label: '🚀 ¿Cómo hacer Backfill?', query: '¿Cómo ejecutar un backfill histórico?' },
    { label: '📦 Registros en Cuarentena', query: '¿Por qué entran registros en la tabla de cuarentena?' },
    { label: '✈️ Airflow & DAGs', query: '¿Qué DAGs están activos en Airflow y cuáles son las credenciales?' },
    { label: '🛡️ ¿Qué hacer en un sismo?', query: '¿Qué hacer durante un sismo?' },
    { label: '🎒 Mochila de Emergencia', query: '¿Qué debe tener una mochila de emergencia?' },
    { label: '💻 Top 5 Sismos (SQL)', query: 'SELECT magnitude, place_name, time FROM earthquakes JOIN locations ON earthquakes.location_id = locations.id ORDER BY magnitude DESC LIMIT 5' }
  ];

  const VIEWER_PROMPTS = [
    { label: '🛡️ ¿Qué hacer en un sismo?', query: '¿Qué hacer durante un sismo?' },
    { label: '🎒 Mochila de Emergencia', query: '¿Qué debe tener una mochila de emergencia?' },
    { label: '🌍 ¿Por qué tiembla?', query: '¿Qué es un sismo y por qué ocurre?' },
    { label: '🌊 Prevención Tsunami', query: 'Protocolo de prevención y qué hacer en un tsunami' },
    { label: '📊 Estadísticas Sísmicas', query: 'Dame un resumen estadístico de la actividad sísmica' },
    { label: '📍 Zonas Más Activas', query: '¿Cuáles son las zonas con mayor sismicidad?' },
    { label: '💻 Top 5 Sismos (SQL)', query: 'SELECT magnitude, place_name, time FROM earthquakes JOIN locations ON earthquakes.location_id = locations.id ORDER BY magnitude DESC LIMIT 5' }
  ];

  const quickPrompts = isAdmin ? ADMIN_PROMPTS : VIEWER_PROMPTS;

  return (
    <div className="flex flex-col h-[calc(100vh-6.5rem)] max-w-5xl mx-auto bg-slate-900/60 backdrop-blur-xl border border-white/10 rounded-2xl shadow-2xl overflow-hidden">
      {/* Agent Top Header */}
      <div className="flex items-center justify-between px-6 py-4 bg-slate-950/70 border-b border-white/10">
        <div className="flex items-center gap-3">
          <div className="relative flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-tr from-sky-500 to-indigo-600 shadow-lg shadow-sky-500/20">
            <Bot className="w-5 h-5 text-white" />
            <span className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-emerald-500 border-2 border-slate-950 rounded-full" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base font-bold text-white tracking-wide">SeismoAgent</h1>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-sky-500/15 text-sky-400 border border-sky-500/30">
                IA Relacional
              </span>
              <span
                className={`px-2 py-0.5 rounded-full text-[10px] font-medium border ${
                  isAdmin
                    ? 'bg-purple-500/15 text-purple-300 border-purple-500/30'
                    : 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30'
                }`}
              >
                {isAdmin ? 'Modo Admin' : 'Modo Viewer'}
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Monitoreo analítico, SQL seguro y telemetría USGS en tiempo real
            </p>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2">
          <button
            onClick={handleSyncData}
            disabled={syncing}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-sky-300 bg-sky-950/60 hover:bg-sky-900/80 border border-sky-700/50 rounded-lg transition-colors disabled:opacity-50"
            title="Consumir y sincronizar última telemetría del USGS"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${syncing ? 'animate-spin' : ''}`} />
            <span className="hidden sm:inline">{syncing ? 'Sincronizando...' : 'Sincronizar USGS'}</span>
          </button>

          <button
            onClick={handleOpenSchema}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-300 bg-slate-800/80 hover:bg-slate-700 border border-white/10 rounded-lg transition-colors"
            title="Ver esquema relacional de tablas"
          >
            <Database className="w-3.5 h-3.5 text-indigo-400" />
            <span className="hidden sm:inline">Esquema SQL</span>
          </button>

          <button
            onClick={handleClearChat}
            className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-slate-800/80 rounded-lg transition-colors"
            title="Limpiar conversación"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Quick Prompts Bar */}
      <div className="px-6 py-2.5 bg-slate-950/40 border-b border-white/5 flex items-center gap-2 overflow-x-auto text-xs no-scrollbar">
        <span className="text-[11px] font-semibold text-slate-400 whitespace-nowrap flex items-center gap-1">
          <Sparkles className="w-3.5 h-3.5 text-amber-400" />
          Sugerencias:
        </span>
        {quickPrompts.map((p, idx) => (
          <button
            key={idx}
            onClick={() => handleSendMessage(p.query)}
            disabled={loading}
            className="px-2.5 py-1 rounded-full bg-slate-800/70 hover:bg-slate-700/80 text-slate-300 hover:text-white border border-white/10 whitespace-nowrap transition-all text-[11px] disabled:opacity-50"
          >
            {p.label}
          </button>
        ))}
      </div>

      {/* Messages Conversation Container */}
      <div className="flex-1 overflow-y-auto px-6 py-6 space-y-5">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex items-start gap-3 ${msg.sender === 'user' ? 'flex-row-reverse' : ''}`}
          >
            {/* Avatar */}
            {msg.sender === 'agent' ? (
              <div className="flex-shrink-0 flex items-center justify-center w-8 h-8 rounded-lg bg-gradient-to-tr from-sky-600 to-indigo-600 text-white shadow-md">
                <Bot className="w-4 h-4" />
              </div>
            ) : (
              <div className="flex-shrink-0 flex items-center justify-center w-8 h-8 rounded-lg bg-slate-700 text-sky-400 font-bold text-xs border border-white/10">
                {user?.username ? user.username.charAt(0).toUpperCase() : 'U'}
              </div>
            )}

            {/* Bubble */}
            <div
              className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm shadow-lg ${
                msg.sender === 'user'
                  ? 'bg-gradient-to-r from-sky-600 to-indigo-600 text-white rounded-tr-none'
                  : msg.isError
                  ? 'bg-rose-950/60 border border-rose-800/60 text-rose-200 rounded-tl-none'
                  : 'bg-slate-800/80 border border-white/10 text-slate-100 rounded-tl-none'
              }`}
            >
              <div className="text-[13px]">{renderFormattedText(msg.text)}</div>
              <div
                className={`text-[10px] mt-1.5 flex items-center gap-1 ${
                  msg.sender === 'user' ? 'text-sky-200/80 justify-end' : 'text-slate-400'
                }`}
              >
                <span>{msg.timestamp}</span>
              </div>
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex items-start gap-3">
            <div className="flex-shrink-0 flex items-center justify-center w-8 h-8 rounded-lg bg-gradient-to-tr from-sky-600 to-indigo-600 text-white animate-pulse">
              <Bot className="w-4 h-4" />
            </div>
            <div className="bg-slate-800/80 border border-white/10 rounded-2xl rounded-tl-none px-4 py-3 text-sm text-slate-400 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-sky-400 animate-ping" />
              <span>Consultando telemetría sísmica y procesando respuesta...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Form Bar */}
      <div className="p-4 bg-slate-950/80 border-t border-white/10">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSendMessage();
          }}
          className="flex items-center gap-2"
        >
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="Pregunta sobre sismos (ej. '¿Hay alertas de tsunami?') o escribe una consulta SQL SELECT..."
            disabled={loading}
            className="flex-1 bg-slate-900/90 text-white text-sm px-4 py-3 rounded-xl border border-white/15 focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500 transition-all placeholder:text-slate-500 disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={loading || !inputText.trim()}
            className="flex items-center justify-center px-4 py-3 bg-gradient-to-r from-sky-500 to-indigo-600 hover:from-sky-400 hover:to-indigo-500 text-white rounded-xl font-medium transition-all shadow-md shadow-sky-500/20 disabled:opacity-50 disabled:pointer-events-none"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>

      {/* Schema Modal */}
      {showSchemaModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-white/15 rounded-2xl max-w-2xl w-full p-6 shadow-2xl flex flex-col max-h-[80vh]">
            <div className="flex items-center justify-between pb-4 border-b border-white/10">
              <div className="flex items-center gap-2 text-sky-400 font-bold">
                <Database className="w-5 h-5" />
                <span>Esquema Relacional Normalizado (3NF)</span>
              </div>
              <button
                onClick={() => setShowSchemaModal(false)}
                className="text-slate-400 hover:text-white text-sm"
              >
                ✕ Cerrar
              </button>
            </div>
            <div className="flex-1 overflow-y-auto my-4 bg-slate-950 p-4 rounded-xl border border-white/5 font-mono text-xs text-slate-300 whitespace-pre">
              {schemaText || 'Cargando esquema...'}
            </div>
            <div className="text-xs text-slate-400 pt-2 border-t border-white/10 flex items-center justify-between">
              <span>Tablas: <code>locations</code>, <code>earthquakes</code>, <code>impact_metrics</code></span>
              <button
                onClick={() => setShowSchemaModal(false)}
                className="px-4 py-1.5 bg-slate-800 hover:bg-slate-700 text-white rounded-lg text-xs"
              >
                Entendido
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
