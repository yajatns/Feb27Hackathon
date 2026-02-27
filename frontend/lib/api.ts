const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://backoffice-api-ep7k.onrender.com';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const err = await res.text().catch(() => res.statusText);
    throw new Error(`API error ${res.status}: ${err}`);
  }
  return res.json();
}

// --- Types ---

export interface HireRequestCreate {
  employee_name: string;
  role: string;
  department: string;
  salary: number;
  location: string;
  start_date: string;
}

export interface AgentTask {
  id: string;
  agent_name: string;
  tool_used: string;
  input_data: string | null;
  output_data: string | null;
  status: string;
  started_at: string | null;
  completed_at: string | null;
}

export interface HireRequest {
  id: string;
  employee_name: string;
  role: string;
  department: string;
  salary: number;
  location: string;
  start_date: string;
  status: string;
  reasoning_summary: string | null;
  created_at: string;
  tasks: AgentTask[];
}

export interface QueryRequest {
  message: string;
}

export interface QueryResponse {
  response: string;
  tools_used: string[];
  reasoning: string | null;
  hire_request_id: string | null;
}

export interface GraphNode {
  id: string;
  label: string;
  type: string;
  properties: Record<string, unknown>;
}

export interface GraphEdge {
  source: string;
  target: string;
  type: string;
  properties: Record<string, unknown>;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface AgentStatus {
  name: string;
  status: string;
  current_task: string | null;
  last_active: string | null;
}

export interface PipelineStatus {
  hire_request_id: string | null;
  overall_status: string;
  agents: AgentStatus[];
  progress_pct: number;
}

// --- API Functions ---

export const api = {
  hire: (data: HireRequestCreate) =>
    request<HireRequest>('/api/hire', { method: 'POST', body: JSON.stringify(data) }),

  getHire: (id: string) =>
    request<HireRequest>(`/api/hire/${id}`),

  listHires: (limit = 20) =>
    request<HireRequest[]>(`/api/hires?limit=${limit}`),

  query: (message: string) =>
    request<QueryResponse>('/api/query', { method: 'POST', body: JSON.stringify({ message }) }),

  getGraph: (hireRequestId?: string) =>
    request<GraphData>(`/api/graph${hireRequestId ? `?hire_request_id=${hireRequestId}` : ''}`),

  getStatus: (hireRequestId?: string) =>
    request<PipelineStatus>(`/api/status${hireRequestId ? `?hire_request_id=${hireRequestId}` : ''}`),
};

// --- WebSocket ---

export function connectStream(onMessage: (msg: { type: string; data: Record<string, unknown> }) => void) {
  const wsUrl = API_URL.replace(/^http/, 'ws') + '/api/stream';
  const ws = new WebSocket(wsUrl);
  ws.onmessage = (e) => {
    try {
      onMessage(JSON.parse(e.data));
    } catch { /* ignore parse errors */ }
  };
  ws.onerror = () => { /* silent reconnect handled by caller */ };
  return ws;
}
