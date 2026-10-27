export type UserRole = 'admin' | 'viewer';

export interface User {
  id: number;
  username: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isAdmin: boolean;
}

export interface KPIs {
  events_24h: number;
  max_magnitude_24h: number;
  avg_magnitude_24h: number;
  tsunami_alerts_24h: number;
  tsunami_alerts_total?: number;
  last_quality_score: number;
  last_earthquake_time: string | null;
}

export interface Earthquake {
  id: string;
  mag: number;
  place: string | null;
  time: string;
  updated?: string | null;
  latitude: number;
  longitude: number;
  depth_km: number;
  tsunami: number;
  alert: string | null;
  status?: string | null;
  magType?: string | null;
  url?: string | null;
}

export interface PaginatedEarthquakes {
  total: number;
  limit: number;
  offset: number;
  items: Earthquake[];
}

export interface Anomaly {
  id: number;
  detected_at: string;
  anomaly_type: string;
  metric_trigger: string;
  description: string;
  event_ids?: string[] | null;
}

export interface AIReport {
  id: number;
  report_date: string;
  narrative_text: string;
  structured_kpis: {
    total_events: number;
    max_magnitude: number;
    avg_magnitude: number;
    tsunami_alerts: number;
    most_active_region: string;
    avg_depth_km: number;
  };
  model_name: string;
  tokens_used: number;
  latency_sec: number;
  created_at: string;
}

export interface QualityAudit {
  id: number;
  dag_run_id: string | null;
  evaluated_at: string;
  total_records: number;
  passed_records: number;
  rejected_records: number;
  quality_score: number;
  rules_summary: any;
}

export interface QuarantineRecord {
  id: number;
  source_id: string | null;
  rejected_at: string;
  reason: string;
  raw_data: any;
}

export interface PipelineStatus {
  dag_statuses: Record<string, { state: string; execution_date?: string }>;
  data_freshness_hours: number | null;
  is_fresh: boolean;
  latest_quality_audit: any | null;
  last_event_time: string | null;
}

export interface TimeseriesPoint {
  bucket: string;
  count: number;
  avg_magnitude: number;
  max_magnitude: number;
}

export interface AgentMessage {
  id: string;
  sender: 'user' | 'agent';
  text: string;
  timestamp: string;
  isError?: boolean;
}
