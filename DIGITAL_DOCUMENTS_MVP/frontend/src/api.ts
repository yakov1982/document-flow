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

export interface DocumentListItem {
  id: number;
  title: string;
  doc_type: string;
  reg_number: string | null;
  status: string;
  created_at: string;
}

export async function listDocuments(q?: string, status_filter?: string): Promise<DocumentListItem[]> {
  const params = new URLSearchParams();
  if (q) params.append('q', q);
  if (status_filter) params.append('status_filter', status_filter);
  const res = await fetch(`${API_BASE}/documents?${params}`, { headers: getHeaders() });
  if (!res.ok) throw new Error('Ошибка загрузки документов');
  return res.json();
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
  state: string;
  comment: string | null;
  acted_at: string | null;
}

export interface DocumentOut {
  id: number;
  title: string;
  doc_type: string;
  reg_number: string | null;
  status: string;
  created_at: string;
  created_by_user_id: number;
  versions: DocumentVersionOut[];
  steps: ApprovalStepOut[];
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
  approvers?: string;
  file?: File;
}): Promise<DocumentOut> {
  const form = new FormData();
  form.append('title', data.title);
  form.append('doc_type', data.doc_type || 'generic');
  if (data.reg_number) form.append('reg_number', data.reg_number);
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
  meta?: Record<string, unknown>;
}

export async function getMyTasks(): Promise<TaskItem[]> {
  const res = await fetch(`${API_BASE}/tasks/my`, { headers: getHeaders() });
  if (!res.ok) throw new Error('Ошибка загрузки задач');
  return res.json();
}
