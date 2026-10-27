import React, { useState, useEffect } from 'react';
import { useAuth } from './context/AuthContext';
import { Sidebar, NavTab } from './components/Sidebar';
import { Login } from './components/Login';
import { Dashboard } from './components/Dashboard';
import { ReportsView } from './components/ReportsView';
import { PipelineView } from './components/PipelineView';
import { AgentView } from './components/AgentView';
import { AgentWidget } from './components/AgentWidget';
import { Earthquake } from './types';

export const App: React.FC = () => {
  const { isAuthenticated, token, isAdmin } = useAuth();
  const [currentTab, setCurrentTab] = useState<NavTab>('dashboard');
  const [sseConnected, setSseConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [newEventsFromSSE, setNewEventsFromSSE] = useState<Earthquake[]>([]);

  // RBAC route guard: viewers have access to Telemetría Sísmica (dashboard) and Agente Sísmico (agent)
  useEffect(() => {
    if (!isAdmin && currentTab !== 'dashboard' && currentTab !== 'agent') {
      setCurrentTab('dashboard');
    }
  }, [isAdmin, currentTab]);

  // SSE Stream Management
  useEffect(() => {
    if (!isAuthenticated || !token) {
      setSseConnected(false);
      return;
    }

    let eventSource: EventSource | null = null;
    let reconnectTimeout: any = null;

    const connectSSE = () => {
      try {
        eventSource = new EventSource(`/api/stream?token=${token}`);

        eventSource.onopen = () => {
          setSseConnected(true);
          setLastUpdate(new Date());
        };

        eventSource.addEventListener('new_earthquake', (e: MessageEvent) => {
          try {
            const data = JSON.parse(e.data);
            setNewEventsFromSSE((prev) => [data, ...prev]);
            setLastUpdate(new Date());
          } catch (err) {
            console.error('Error parsing SSE earthquake payload:', err);
          }
        });

        eventSource.addEventListener('ping', () => {
          setLastUpdate(new Date());
        });

        eventSource.onerror = () => {
          setSseConnected(false);
          eventSource?.close();
          // Auto-reconnect after 5 seconds
          reconnectTimeout = setTimeout(connectSSE, 5000);
        };
      } catch (err) {
        setSseConnected(false);
        reconnectTimeout = setTimeout(connectSSE, 5000);
      }
    };

    connectSSE();

    return () => {
      eventSource?.close();
      clearTimeout(reconnectTimeout);
    };
  }, [isAuthenticated, token]);

  // If visitor is not authenticated, immediate redirection to Login
  if (!isAuthenticated) {
    return <Login />;
  }

  return (
    <div className="min-h-screen bg-transparent text-slate-100 flex flex-col md:flex-row font-sans">
      <Sidebar
        currentTab={currentTab}
        setCurrentTab={setCurrentTab}
        sseConnected={sseConnected}
        lastUpdate={lastUpdate}
      />

      <div className="flex-1 flex flex-col min-w-0">
        <main className="flex-1 max-w-[1560px] w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
          {currentTab === 'dashboard' && <Dashboard newEventsFromSSE={newEventsFromSSE} />}
          {currentTab === 'agent' && <AgentView />}
          {currentTab === 'reports' && isAdmin && <ReportsView />}
          {currentTab === 'pipeline' && isAdmin && <PipelineView />}
        </main>

        <footer className="border-t border-white/[0.06] bg-black/40 backdrop-blur-md py-4 text-center text-xs text-slate-500">
          SismoWatch Platform &copy; {new Date().getFullYear()} SuperApp Data Engineering & AI Solutions Architecture
        </footer>
      </div>

      {/* Floating Quick Agent Assistant across all views */}
      <AgentWidget />
    </div>
  );
};

export default App;
