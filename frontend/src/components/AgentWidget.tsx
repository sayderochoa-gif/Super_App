import React, { useState, useEffect, useRef } from 'react';
import {
  Bot,
  Send,
  X,
  Minimize2,
  Maximize2,
  Trash2,
  Sparkles,
  RefreshCw
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';
import { AgentMessage } from '../types';

export const AgentWidget: React.FC = () => {
  const { user, isAdmin } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const [inputText, setInputText] = useState('');
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState<AgentMessage[]>([
    {
      id: 'welcome-widget',
      sender: 'agent',
      text: `Hola **${user?.username || ''}**. Soy **SeismoAgent**. Pregúntame sobre sismos recientes, estadísticas, tsunamis o consultas SQL.`,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isOpen) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isOpen, loading]);

  const handleSendMessage = async (customQuery?: string) => {
    const text = (customQuery || inputText).trim();
    if (!text || loading) return;

    const userMsg: AgentMessage = {
      id: `w-user-${Date.now()}`,
      sender: 'user',
      text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!customQuery) setInputText('');
    setLoading(true);

    try {
      const res = await api.chatAgent(text);
      setMessages((prev) => [
        ...prev,
        {
          id: `w-agent-${Date.now()}`,
          sender: 'agent',
          text: res.response,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ]);
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          id: `w-err-${Date.now()}`,
          sender: 'agent',
          text: `❌ Error: ${err.message}`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          isError: true
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setMessages([
      {
        id: `clear-${Date.now()}`,
        sender: 'agent',
        text: 'Chat reiniciado. ¿En qué puedo asistirte?',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }
    ]);
  };

  const ADMIN_CHIPS = [
    { label: '⚙️ Acciones Admin', query: '¿Qué acciones puedo hacer como administrador?' },
    { label: '🛠️ Mi Vista', query: '¿Qué veo en mi vista de administrador?' },
    { label: '🚀 Backfill', query: '¿Cómo ejecutar un backfill histórico?' },
    { label: '📦 Cuarentena', query: '¿Por qué entran registros en la tabla de cuarentena?' },
    { label: '✈️ Airflow & DAGs', query: '¿Qué DAGs están activos en Airflow?' },
    { label: '📊 Stats', query: 'Dame un resumen de estadísticas sísmicas' }
  ];

  const VIEWER_CHIPS = [
    { label: '🛡️ En un Sismo', query: '¿Qué hacer durante un sismo?' },
    { label: '🎒 Mochila 72h', query: '¿Qué debe contener la mochila de emergencia?' },
    { label: '🌍 ¿Por qué tiembla?', query: '¿Qué es un sismo y por qué ocurre?' },
    { label: '🌊 Tsunamis', query: 'Protocolo de prevención en tsunamis' },
    { label: '📊 Stats', query: 'Dame un resumen de estadísticas sísmicas' },
    { label: '🔄 Sincronizar', query: 'Sincroniza los últimos sismos de USGS' }
  ];

  const quickChips = isAdmin ? ADMIN_CHIPS : VIEWER_CHIPS;

  const renderCleanText = (text: string) => {
    // Strip triple asterisks and messy bold
    const clean = text.replace(/\*{3,}/g, '').replace(/\*\*\s*\*/g, '').replace(/\*\s*\*\*/g, '');
    const parts = clean.split(/(\*\*.*?\*\*|`.*?`)/g);
    return parts.map((part, i) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={i} className="text-white font-semibold">{part.slice(2, -2)}</strong>;
      }
      if (part.startsWith('`') && part.endsWith('`')) {
        return (
          <code key={i} className="bg-slate-900 text-sky-300 px-1 py-0.5 rounded text-[10px] font-mono border border-slate-700">
            {part.slice(1, -1)}
          </code>
        );
      }
      return part;
    });
  };

  return (
    <div className="fixed bottom-5 right-5 z-50">
      {/* Floating Trigger Button */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="group relative flex items-center gap-2.5 px-4 py-3 bg-gradient-to-r from-sky-600 via-indigo-600 to-purple-600 hover:from-sky-500 hover:to-indigo-500 text-white rounded-full shadow-2xl shadow-sky-600/30 border border-white/20 transition-all transform hover:scale-105 active:scale-95"
        >
          <div className="relative flex items-center justify-center">
            <Bot className="w-5 h-5 text-white animate-bounce" />
            <span className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-emerald-400 rounded-full animate-ping" />
            <span className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-emerald-500 rounded-full" />
          </div>
          <span className="text-xs font-bold tracking-wide">SeismoAgent IA</span>
        </button>
      )}

      {/* Floating Chat Window */}
      {isOpen && (
        <div className="flex flex-col w-[360px] sm:w-[420px] h-[520px] bg-[#0c1222]/95 backdrop-blur-2xl border border-white/15 rounded-2xl shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 bg-slate-950/80 border-b border-white/10">
            <div className="flex items-center gap-2.5">
              <div className="flex items-center justify-center w-7 h-7 rounded-lg bg-gradient-to-tr from-sky-500 to-indigo-600 shadow-sm">
                <Bot className="w-4 h-4 text-white" />
              </div>
              <div>
                <div className="flex items-center gap-1.5">
                  <span className="text-xs font-bold text-white">SeismoAgent</span>
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                </div>
                <span className="text-[10px] text-slate-400">
                  {isAdmin ? 'Admin View' : 'Viewer View'}
                </span>
              </div>
            </div>

            <div className="flex items-center gap-1">
              <button
                onClick={handleClear}
                className="p-1 text-slate-400 hover:text-rose-400 rounded transition-colors"
                title="Limpiar chat"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
              <button
                onClick={() => setIsOpen(false)}
                className="p-1 text-slate-400 hover:text-white rounded transition-colors"
                title="Cerrar asistente"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Quick Prompts */}
          <div className="px-3 py-1.5 bg-slate-950/40 border-b border-white/5 flex items-center gap-1.5 overflow-x-auto no-scrollbar">
            {quickChips.map((chip, idx) => (
              <button
                key={idx}
                onClick={() => handleSendMessage(chip.query)}
                disabled={loading}
                className="px-2 py-0.5 rounded-full bg-slate-800/80 hover:bg-slate-700 text-slate-300 hover:text-white border border-white/10 text-[10px] whitespace-nowrap transition-all disabled:opacity-50"
              >
                {chip.label}
              </button>
            ))}
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3 text-xs">
            {messages.map((m) => (
              <div
                key={m.id}
                className={`flex flex-col ${m.sender === 'user' ? 'items-end' : 'items-start'}`}
              >
                <div
                  className={`max-w-[88%] rounded-2xl px-3 py-2 leading-relaxed shadow-sm ${
                    m.sender === 'user'
                      ? 'bg-gradient-to-r from-sky-600 to-indigo-600 text-white rounded-tr-none'
                      : m.isError
                      ? 'bg-rose-950/70 border border-rose-800 text-rose-200 rounded-tl-none'
                      : 'bg-slate-800/90 border border-white/10 text-slate-200 rounded-tl-none'
                  }`}
                >
                  <div className="whitespace-pre-wrap">{renderCleanText(m.text)}</div>
                </div>
                <span className="text-[9px] text-slate-500 mt-0.5 px-1">{m.timestamp}</span>
              </div>
            ))}

            {loading && (
              <div className="flex items-center gap-2 text-slate-400 text-xs py-1">
                <span className="w-2 h-2 rounded-full bg-sky-400 animate-ping" />
                <span>Consultando telemetría...</span>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSendMessage();
            }}
            className="p-3 bg-slate-950/90 border-t border-white/10 flex items-center gap-2"
          >
            <input
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder="Escribe tu consulta sísmica..."
              disabled={loading}
              className="flex-1 bg-slate-900 text-white text-xs px-3 py-2 rounded-lg border border-white/10 focus:outline-none focus:border-sky-500 placeholder:text-slate-500"
            />
            <button
              type="submit"
              disabled={loading || !inputText.trim()}
              className="p-2 bg-sky-600 hover:bg-sky-500 text-white rounded-lg transition-colors disabled:opacity-40"
            >
              <Send className="w-3.5 h-3.5" />
            </button>
          </form>
        </div>
      )}
    </div>
  );
};
