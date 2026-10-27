import * as XLSX from 'xlsx';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';
const XLSX_MIME_TYPE = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet';

async function apiRequest<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      ...(options.headers || {}),
    },
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed with status ${response.status}`);
  }

  const contentType = response.headers.get('content-type') || '';
  if (contentType.includes('application/json')) {
    return (await response.json()) as T;
  }

  return (await response.blob()) as unknown as T;
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
  const response = await fetch(`${API_BASE_URL}/jobs/${jobId}/download`);

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Workbook download failed with status ${response.status}`);
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
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || 'Upload failed');
  }

  return response;
}
