import { KPIs, PaginatedEarthquakes, AIReport, Anomaly, PipelineStatus, QualityAudit, QuarantineRecord } from '../types';

const API_BASE = '';

function getAuthHeader(): Record<string, string> {
  const token = localStorage.getItem('sismowatch_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const headers = {
    'Content-Type': 'application/json',
    ...getAuthHeader(),
    ...(options.headers || {})
  };

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers
  });

  if (response.status === 401) {
    localStorage.removeItem('sismowatch_token');
    localStorage.removeItem('sismowatch_user');
    window.location.href = '#login';
    throw new Error('Sesión expirada o no autorizada');
  }

  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(errorBody.detail || `Error ${response.status}`);
  }

  return response.json();
}

export const api = {
  // Auth
  login: (username: string, password: string) =>
    request<{ access_token: string; role: 'admin' | 'viewer'; username: string }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password })
    }),

  // KPIs & Events
  getKPIs: () => request<KPIs>('/api/kpis'),

  getEvents: (params: {
    min_magnitude?: number;
    max_magnitude?: number;
    region?: string;
    limit?: number;
    offset?: number;
  }) => {
    const query = new URLSearchParams();
    if (params.min_magnitude !== undefined) query.set('min_magnitude', String(params.min_magnitude));
    if (params.max_magnitude !== undefined) query.set('max_magnitude', String(params.max_magnitude));
    if (params.region) query.set('region', params.region);
    if (params.limit) query.set('limit', String(params.limit));
    if (params.offset) query.set('offset', String(params.offset));
    return request<PaginatedEarthquakes>(`/api/events?${query.toString()}`);
  },

  getTimeseries: (hours: number = 24) =>
    request<{ data: any[] }>(`/api/stats/timeseries?hours=${hours}`),

  getMagnitudeDistribution: () =>
    request<{ tier: string; count: number }[]>('/api/stats/magnitude-distribution'),

  // AI Reports & Anomalies
  getReports: (limit: number = 30) => request<AIReport[]>(`/api/reports?limit=${limit}`),

  getLatestReport: () => request<AIReport | null>('/api/reports/latest'),

  getAnomalies: (limit: number = 50) => request<Anomaly[]>(`/api/reports/anomalies?limit=${limit}`),

  // Pipeline & Quality
  getPipelineStatus: () => request<PipelineStatus>('/api/pipeline/status'),

  getQualityHistory: (limit: number = 20) => request<QualityAudit[]>(`/api/pipeline/quality-history?limit=${limit}`),

  // Admin Only
  getQuarantine: (limit: number = 50, offset: number = 0) =>
    request<{ total: number; limit: number; offset: number; items: QuarantineRecord[] }>(
      `/api/quality/quarantine?limit=${limit}&offset=${offset}`
    ),

  triggerBackfill: (payload: { start_date: string; end_date: string; min_mag: number }) =>
    request<{ status: string; message: string }>('/api/admin/backfill', {
      method: 'POST',
      body: JSON.stringify(payload)
    }),

  triggerReportRegenerate: () =>
    request<{ status: string; message: string }>('/api/admin/reports/regenerate', {
      method: 'POST'
    }),

  // Seismic Relational Agent (Viewer & Admin)
  chatAgent: (message: string, reset: boolean = false) =>
    request<{ response: string; user_role: string; timestamp: string }>('/api/agent/chat', {
      method: 'POST',
      body: JSON.stringify({ message, reset })
    }),

  syncAgent: () =>
    request<{ status: string; triggered_by: string; role: string; data: any }>('/api/agent/sync', {
      method: 'POST'
    }),

  getAgentStats: () =>
    request<any>('/api/agent/stats'),

  getAgentTsunami: () =>
    request<any>('/api/agent/tsunami'),

  getAgentSchema: () =>
    request<{ schema: string }>('/api/agent/schema')
};
