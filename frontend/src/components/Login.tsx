import React, { useState } from 'react';
import { Activity, Lock, Mail, AlertCircle, ArrowRight, Shield, Eye } from 'lucide-react';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';

export const Login: React.FC = () => {
  const { login } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const data = await api.login(username, password);
      login(data.access_token, data.role, data.username);
    } catch (err: any) {
      setError(err.message || 'Error de autenticación. Verifique sus credenciales.');
    } finally {
      setLoading(false);
    }
  };

  const handleQuickLogin = (userRole: 'admin' | 'viewer') => {
    if (userRole === 'admin') {
      setUsername('admin@sismowatch.com');
      setPassword('AdminSismoWatch2025!');
    } else {
      setUsername('viewer@sismowatch.com');
      setPassword('ViewerSismoWatch2025!');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-transparent px-4 relative overflow-hidden">
      {/* Subtle ambient lighting backdrop */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[350px] bg-gradient-to-tr from-sky-600/10 via-indigo-600/10 to-transparent rounded-full blur-[120px] pointer-events-none"></div>

      <div className="max-w-[420px] w-full relative z-10">
        <div className="bg-[#0f141f]/90 border border-white/[0.08] p-8 rounded-2xl shadow-2xl backdrop-blur-2xl space-y-6">
          
          {/* Header */}
          <div className="text-center space-y-2">
            <div className="inline-flex p-2.5 rounded-xl bg-gradient-to-br from-sky-500/10 to-indigo-500/10 border border-sky-500/20 shadow-inner">
              <Activity className="w-6 h-6 text-sky-400" />
            </div>
            <h1 className="text-xl font-bold tracking-tight text-white font-mono uppercase">
              SismoWatch Platform
            </h1>
            <p className="text-xs text-slate-400 leading-relaxed">
              Consola analítica de sismicidad global y telemetría en tiempo real
            </p>
          </div>

          {error && (
            <div className="flex items-center gap-2.5 p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Login Form */}
          <form className="space-y-4" onSubmit={handleSubmit}>
            <div>
              <label className="block text-[11px] font-mono uppercase tracking-wider text-slate-400 mb-1.5 font-medium">
                Usuario / Correo
              </label>
              <div className="relative">
                <Mail className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  required
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="admin@sismowatch.com"
                  className="w-full bg-slate-900/80 border border-white/[0.08] rounded-lg pl-9 pr-3.5 py-2 text-xs text-slate-100 placeholder-slate-600 focus:outline-none focus:ring-1 focus:ring-sky-500/80 focus:border-sky-500/80 transition-all font-mono"
                />
              </div>
            </div>

            <div>
              <label className="block text-[11px] font-mono uppercase tracking-wider text-slate-400 mb-1.5 font-medium">
                Contraseña
              </label>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="w-full bg-slate-900/80 border border-white/[0.08] rounded-lg pl-9 pr-3.5 py-2 text-xs text-slate-100 placeholder-slate-600 focus:outline-none focus:ring-1 focus:ring-sky-500/80 focus:border-sky-500/80 transition-all font-mono"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg bg-sky-600 hover:bg-sky-500 text-white font-medium text-xs transition-all duration-150 shadow-md shadow-sky-600/25 disabled:opacity-50"
            >
              {loading ? (
                <span className="flex items-center gap-2 font-mono">
                  <span className="animate-spin rounded-full h-3 w-3 border-2 border-white border-t-transparent"></span>
                  Validando...
                </span>
              ) : (
                <>
                  <span>Ingresar a la Plataforma</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </>
              )}
            </button>
          </form>

          {/* Quick Demo Access Bar */}
          <div className="pt-4 border-t border-white/[0.06] space-y-2">
            <span className="block text-[10px] text-center font-mono uppercase tracking-wider text-slate-500">
              Acceso Rápido de Evaluación
            </span>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => handleQuickLogin('admin')}
                className="flex items-center justify-center gap-1.5 py-1.5 px-2.5 rounded-lg bg-purple-500/10 hover:bg-purple-500/20 border border-purple-500/20 text-purple-300 text-xs font-mono font-medium transition-all"
              >
                <Shield className="w-3 h-3 text-purple-400" />
                <span>Rol Admin</span>
              </button>
              <button
                type="button"
                onClick={() => handleQuickLogin('viewer')}
                className="flex items-center justify-center gap-1.5 py-1.5 px-2.5 rounded-lg bg-sky-500/10 hover:bg-sky-500/20 border border-sky-500/20 text-sky-300 text-xs font-mono font-medium transition-all"
              >
                <Eye className="w-3 h-3 text-sky-400" />
                <span>Rol Viewer</span>
              </button>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
};
