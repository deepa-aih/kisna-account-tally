import * as XLSX from 'xlsx';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';
const XLSX_MIME_TYPE = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet';

async function responseError(response: Response, fallback: string) {
  const text = await response.text();
  if (!text) return new Error(`${fallback} (${response.status})`);
  try {
    const payload = JSON.parse(text) as { detail?: string; message?: string };
    return new Error(payload.detail || payload.message || fallback);
  } catch {
    return new Error(text);
  }
}

async function apiRequest<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  if (typeof options.body === 'string' && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    credentials: 'include',
    headers,
  });

  if (!response.ok) {
    throw await responseError(response, `Request failed with status ${response.status}`);
  }

  const contentType = response.headers.get('content-type') || '';
  if (contentType.includes('application/json')) {
    return (await response.json()) as T;
  }

  return (await response.blob()) as unknown as T;
}

export interface AuthUser {
  id: string;
  email: string;
  name: string;
  clientName: string;
  role: 'admin' | 'member';
}

export interface ManagedUser extends AuthUser {
  active: boolean;
  createdAt?: string;
}

export async function getCurrentUser() {
  return apiRequest<{ user: AuthUser }>('/auth/me');
}

export async function signIn(email: string, password: string) {
  return apiRequest<{ user: AuthUser }>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
}

export async function signOut() {
  return apiRequest<{ ok: boolean }>('/auth/logout', { method: 'POST' });
}

export async function resetPassword(token: string, password: string) {
  return apiRequest<{ ok: boolean }>('/auth/reset-password', {
    method: 'POST',
    body: JSON.stringify({ token, password }),
  });
}

export async function getManagedUsers() {
  return apiRequest<ManagedUser[]>('/admin/users');
}

export async function createManagedUser(name: string, email: string) {
  return apiRequest<{ user: ManagedUser; resetLink: string; expiresInSeconds: number }>('/admin/users', {
    method: 'POST',
    body: JSON.stringify({ name, email }),
  });
}

export async function createUserResetLink(userId: string) {
  return apiRequest<{ resetLink: string; expiresInSeconds: number }>(`/admin/users/${userId}/reset-link`, {
    method: 'POST',
  });
}

export async function getDashboardSummary() {
  return apiRequest<{
    totalJobs: number;
    successfulJobs: number;
    flaggedJobs: number;
    recordsProcessed: number;
    recentFiles: unknown[];
    kpis?: Record<string, unknown> | null;
  }>('/dashboard/summary');
}

export async function getJobs() {
  return apiRequest<Array<Record<string, unknown>>>('/jobs');
}

export async function getJobPreview(jobId: string) {
  return apiRequest<{ rows: Array<Record<string, unknown>>; count: number }>(`/jobs/${jobId}/rows`);
}

export async function getJobSheets(jobId: string) {
  return apiRequest<{ sheets: Record<string, Array<Record<string, unknown>>> }>(`/jobs/${jobId}/sheets`);
}

export async function downloadJobWorkbook(jobId: string) {
  const response = await fetch(`${API_BASE_URL}/jobs/${jobId}/download`, { credentials: 'include' });

  if (!response.ok) {
    throw await responseError(response, `Workbook download failed with status ${response.status}`);
  }

  const contentType = response.headers.get('content-type') || '';
  if (contentType.includes('application/json')) {
    const payload = await response.json() as { detail?: string };
    const { sheets } = await getJobSheets(jobId);
    const sheetEntries = Object.entries(sheets);
    if (sheetEntries.length === 0) {
      throw new Error(
        payload.detail || 'The saved workbook data is unavailable. Reprocess the source files to enable downloads.'
      );
    }

    const workbook = XLSX.utils.book_new();
    sheetEntries.forEach(([sheetName, rows]) => {
      XLSX.utils.book_append_sheet(
        workbook,
        XLSX.utils.json_to_sheet(rows),
        sheetName.slice(0, 31)
      );
    });
    const workbookData = XLSX.write(workbook, { bookType: 'xlsx', type: 'array' });
    return new Blob([workbookData], { type: XLSX_MIME_TYPE });
  }

  const workbook = await response.blob();
  if (workbook.size === 0) {
    throw new Error('The generated workbook download was empty.');
  }
  return workbook;
}

export async function uploadWorkbookBatch(filesByRole: Record<string, File>) {
  const formData = new FormData();

  const fieldOrder = ['branded_file', 'rm_file', 'master_file', 'sale_file', 'receivable_file'];

  fieldOrder.forEach((field) => {
    const file = filesByRole[field];
    if (file) {
      formData.append(field, file);
    }
  });

  const response = await fetch(`${API_BASE_URL}/process`, {
    method: 'POST',
    body: formData,
    credentials: 'include',
  });

  if (!response.ok) {
    throw await responseError(response, 'Upload failed');
  }

  return response;
}
