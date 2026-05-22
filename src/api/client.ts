const API_BASE = '/api';

export interface UploadResponse {
  job_id: string;
  filename: string;
  file_type: string;
  text_preview: string;
  char_count: number;
}

export interface ScreenResponse {
  job_id: string;
  status: 'uploaded' | 'processing' | 'completed' | 'failed';
}

export interface RiskIssue {
  id: string;
  title: string;
  clause_text: string;
  risk_level: 'HIGH' | 'MEDIUM' | 'LOW';
  description: string;
  legal_basis?: string | null;
  legal_basis_text?: string | null;
  citations: string[];
}

export interface ScreeningResult {
  job_id: string;
  status: string;
  issues: RiskIssue[];
  verified_issues: RiskIssue[];
  retrieved_docs?: { id: string; category: string; clause: string; content: string }[];
  output_report: string;
  output_email: string;
  contract_masked?: string | null;
  high_risk_count: number;
  medium_risk_count: number;
  low_risk_count: number;
  safety_score: number | null;
}

export interface HealthResponse {
  status: string;
  llm_enabled: boolean;
  rag_enabled: boolean;
  chroma_status: string;
  embedding_model: string;
}

export async function getHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

async function parseError(res: Response): Promise<string> {
  try {
    const body = await res.json();
    if (body?.message) return String(body.message);
    if (body?.detail) {
      if (typeof body.detail === 'string') return body.detail;
      if (body.detail?.message) return String(body.detail.message);
    }
  } catch {
    /* ignore */
  }
  return res.statusText || `HTTP ${res.status}`;
}

export async function uploadContract(file: File): Promise<UploadResponse> {
  const form = new FormData();
  form.append('file', file);
  const res = await fetch(`${API_BASE}/upload`, { method: 'POST', body: form });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function runScreen(jobId: string): Promise<ScreenResponse> {
  const res = await fetch(`${API_BASE}/screen`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ job_id: jobId }),
  });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function getResult(jobId: string): Promise<ScreeningResult> {
  const res = await fetch(`${API_BASE}/result/${jobId}`);
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}
