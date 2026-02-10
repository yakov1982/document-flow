const API_BASE = import.meta.env.VITE_API_URL || '/api';

function getToken(): string | null {
  return localStorage.getItem('token');
}

function getHeaders(includeAuth = true): HeadersInit {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };
  const token = getToken();
  if (includeAuth && token) {
    (headers as Record<string, string>)['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

export async function login(username: string, password: string): Promise<{ access_token: string }> {
  const form = new URLSearchParams();
  form.append('username', username);
  form.append('password', password);
  const res = await fetch(`${API_BASE}/auth/token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: form,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Ошибка входа');
  }
  return res.json();
}

export interface User {
  id: number;
  username: string;
  role: string;
  created_at: string;
}

export async function getMe(): Promise<User> {
  const res = await fetch(`${API_BASE}/auth/me`, { headers: getHeaders() });
  if (!res.ok) throw new Error('Не авторизован');
  return res.json();
}

export async function getAuthInfo(): Promise<{ ldap_enabled: boolean }> {
  const res = await fetch(`${API_BASE}/auth/info`);
  if (!res.ok) return { ldap_enabled: false };
  return res.json();
}

export interface DocumentListParams {
  q?: string;
  status_filter?: string;
  doc_type_filter?: string;
  author_id?: number;
  counterparty?: string;
  date_from?: string;
  date_to?: string;
  sort?: string;
  skip?: number;
  limit?: number;
}

export interface DocumentListItem {
  id: number;
  title: string;
  doc_type: string;
  reg_number: string | null;
  status: string;
  created_at: string;
  created_by_username?: string;
}

export async function listDocuments(params?: DocumentListParams): Promise<DocumentListItem[]> {
  const p = new URLSearchParams();
  if (params?.q) p.append('q', params.q);
  if (params?.status_filter) p.append('status_filter', params.status_filter);
  if (params?.doc_type_filter) p.append('doc_type_filter', params.doc_type_filter);
  if (params?.author_id) p.append('author_id', String(params.author_id));
  if (params?.counterparty) p.append('counterparty', params.counterparty);
  if (params?.date_from) p.append('date_from', params.date_from);
  if (params?.date_to) p.append('date_to', params.date_to);
  if (params?.sort) p.append('sort', params.sort);
  if (params?.skip != null) p.append('skip', String(params.skip));
  if (params?.limit != null) p.append('limit', String(params.limit));
  const res = await fetch(`${API_BASE}/documents?${p}`, { headers: getHeaders() });
  if (!res.ok) throw new Error('Ошибка загрузки документов');
  return res.json();
}

export async function exportDocumentsCsv(params?: { q?: string; status_filter?: string }): Promise<void> {
  const p = new URLSearchParams();
  if (params?.q) p.append('q', params.q);
  if (params?.status_filter) p.append('status_filter', params.status_filter);
  const res = await fetch(`${API_BASE}/documents/export/csv?${p}`, { headers: getHeaders() });
  if (!res.ok) throw new Error('Ошибка экспорта');
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'documents.csv';
  a.click();
  URL.revokeObjectURL(url);
}

export interface DocumentVersionOut {
  id: number;
  version: number;
  filename: string;
  content_type: string | null;
  size: number;
  uploaded_at: string;
  uploaded_by_user_id: number;
}

export interface ApprovalStepOut {
  id: number;
  step_order: number;
  approver_user_id: number;
  approver_username?: string;
  delegated_to_user_id?: number | null;
  delegated_to_username?: string | null;
  state: string;
  comment: string | null;
  acted_at: string | null;
  deadline?: string | null;
}

export interface DocumentSignatureOut {
  id: number;
  user_id: number;
  signed_at: string;
  cert_subject: string | null;
  cert_thumbprint: string | null;
  has_detached_signature?: boolean;
}

export interface DocumentOut {
  id: number;
  title: string;
  doc_type: string;
  reg_number: string | null;
  status: string;
  created_at: string;
  document_date?: string | null;
  counterparty_from?: string | null;
  counterparty_to?: string | null;
  custom_attributes?: Record<string, unknown> | null;
  created_by_user_id: number;
  versions: DocumentVersionOut[];
  steps: ApprovalStepOut[];
  signatures: DocumentSignatureOut[];
  assignments?: Record<string, unknown>[];
}

export async function getDocument(id: number): Promise<DocumentOut> {
  const res = await fetch(`${API_BASE}/documents/${id}`, { headers: getHeaders() });
  if (!res.ok) throw new Error('Документ не найден');
  return res.json();
}

export async function createDocument(data: {
  title: string;
  doc_type?: string;
  reg_number?: string;
  document_date?: string;
  counterparty_from?: string;
  counterparty_to?: string;
  approvers?: string;
  file?: File;
}): Promise<DocumentOut> {
  const form = new FormData();
  form.append('title', data.title);
  form.append('doc_type', data.doc_type || 'generic');
  if (data.reg_number) form.append('reg_number', data.reg_number);
  if (data.document_date) form.append('document_date', data.document_date);
  if (data.counterparty_from) form.append('counterparty_from', data.counterparty_from);
  if (data.counterparty_to) form.append('counterparty_to', data.counterparty_to);
  if (data.approvers) form.append('approvers', data.approvers);
  if (data.file) form.append('file', data.file);

  const headers: Record<string, string> = {};
  const token = getToken();
  if (token) headers['Authorization'] = `Bearer ${token}`;
  // Don't set Content-Type for FormData - browser sets it with boundary

  const res = await fetch(`${API_BASE}/documents`, {
    method: 'POST',
    headers,
    body: form,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Ошибка создания документа');
  }
  return res.json();
}

export async function uploadVersion(docId: number, file: File): Promise<DocumentOut> {
  const form = new FormData();
  form.append('file', file);

  const headers: Record<string, string> = {};
  const token = getToken();
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}/documents/${docId}/versions`, {
    method: 'POST',
    headers,
    body: form,
  });
  if (!res.ok) throw new Error('Ошибка загрузки версии');
  return res.json();
}

export async function downloadVersion(docId: number, versionId: number, filename: string): Promise<void> {
  const res = await fetch(`${API_BASE}/documents/${docId}/versions/${versionId}/download`, {
    headers: getHeaders(),
  });
  if (!res.ok) throw new Error('Ошибка скачивания');
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export async function approveDocument(docId: number, comment?: string): Promise<DocumentOut> {
  const form = new FormData();
  if (comment) form.append('comment', comment);

  const headers: Record<string, string> = {};
  const token = getToken();
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}/documents/${docId}/approve`, {
    method: 'POST',
    headers,
    body: form,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Ошибка согласования');
  }
  return res.json();
}

export async function rejectDocument(docId: number, comment?: string): Promise<DocumentOut> {
  const form = new FormData();
  if (comment) form.append('comment', comment);

  const headers: Record<string, string> = {};
  const token = getToken();
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}/documents/${docId}/reject`, {
    method: 'POST',
    headers,
    body: form,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Ошибка отклонения');
  }
  return res.json();
}

export interface TaskItem {
  document_id: number;
  title: string;
  step_id: number;
  step_order: number;
  state: string;
  deadline?: string | null;
  meta?: Record<string, unknown>;
}

export interface AuditLogItem {
  id: number;
  created_at: string;
  actor_username?: string | null;
  action: string;
  document_id: number | null;
  meta?: Record<string, unknown> | null;
}

export async function getAuditLog(documentId?: number): Promise<AuditLogItem[]> {
  const params = documentId ? `?document_id=${documentId}` : '';
  const res = await fetch(`${API_BASE}/audit${params}`, { headers: getHeaders() });
  if (!res.ok) throw new Error('Ошибка загрузки аудита');
  return res.json();
}

export async function delegateStep(docId: number, stepId: number, toUsername: string): Promise<DocumentOut> {
  const res = await fetch(`${API_BASE}/documents/${docId}/delegate`, {
    method: 'POST',
    headers: { ...getHeaders(), 'Content-Type': 'application/json' },
    body: JSON.stringify({ step_id: stepId, to_username: toUsername }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Ошибка делегирования');
  }
  return res.json();
}

export async function createAssignment(data: {
  document_id: number;
  assignee_username: string;
  title: string;
  deadline?: string;
}): Promise<unknown> {
  const res = await fetch(`${API_BASE}/assignments`, {
    method: 'POST',
    headers: { ...getHeaders(), 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error('Ошибка создания поручения');
  return res.json();
}

export async function getMyAssignments(): Promise<unknown[]> {
  const res = await fetch(`${API_BASE}/assignments/my`, { headers: getHeaders() });
  if (!res.ok) throw new Error('Ошибка загрузки поручений');
  return res.json();
}

export async function getUsers(): Promise<User[]> {
  const res = await fetch(`${API_BASE}/auth/users`, { headers: getHeaders() });
  if (!res.ok) return [];
  return res.json();
}

export async function getMyTasks(): Promise<TaskItem[]> {
  const res = await fetch(`${API_BASE}/tasks/my`, { headers: getHeaders() });
  if (!res.ok) throw new Error('Ошибка загрузки задач');
  return res.json();
}

export async function signDocument(
  docId: number,
  opts?: { certSubject?: string; certThumbprint?: string; signatureFile?: File }
): Promise<DocumentOut> {
  const form = new FormData();
  if (opts?.certSubject) form.append('cert_subject', opts.certSubject);
  if (opts?.certThumbprint) form.append('cert_thumbprint', opts.certThumbprint);
  if (opts?.signatureFile) form.append('signature_file', opts.signatureFile);

  const headers: Record<string, string> = {};
  const token = getToken();
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}/documents/${docId}/sign`, {
    method: 'POST',
    headers,
    body: form,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Ошибка подписания');
  }
  return res.json();
}

export async function downloadSignature(docId: number, sigId: number): Promise<void> {
  const res = await fetch(`${API_BASE}/documents/${docId}/signatures/${sigId}/download`, {
    headers: getHeaders(),
  });
  if (!res.ok) throw new Error('Ошибка скачивания');
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `signature_${sigId}.p7s`;
  a.click();
  URL.revokeObjectURL(url);
}
