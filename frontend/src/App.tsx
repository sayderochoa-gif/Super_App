import React, { useState, useEffect } from 'react';
import { useAuth } from './context/AuthContext';
import { Navbar } from './components/Navbar';
import { Login } from './components/Login';
import { Dashboard } from './components/Dashboard';
import { ReportsView } from './components/ReportsView';
import { PipelineView } from './components/PipelineView';
import { Earthquake } from './types';

export const App: React.FC = () => {
  const { isAuthenticated, token } = useAuth();
  const [currentTab, setCurrentTab] = useState<'dashboard' | 'reports' | 'pipeline'>('dashboard');
  const [sseConnected, setSseConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [newEventsFromSSE, setNewEventsFromSSE] = useState<Earthquake[]>([]);

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
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      <Navbar
        currentTab={currentTab}
        setCurrentTab={setCurrentTab}
        sseConnected={sseConnected}
        lastUpdate={lastUpdate}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {currentTab === 'dashboard' && <Dashboard newEventsFromSSE={newEventsFromSSE} />}
        {currentTab === 'reports' && <ReportsView />}
        {currentTab === 'pipeline' && <PipelineView />}
      </main>

      <footer className="border-t border-slate-900 bg-slate-950 py-4 text-center text-xs text-slate-500">
        SismoWatch Platform &copy; {new Date().getFullYear()} SuperApp Data Engineering & AI Solutions Architecture
      </footer>
    </div>
  );
};

export default App;
