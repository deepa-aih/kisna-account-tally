export type ActiveTab = 'dashboard' | 'new-merge' | 'viewer' | 'history' | 'cost-analysis';

export interface RecentFile {
  id: string;
  name: string;
  totalRows: number;
  processingDate: string;
  durationSeconds: number;
  status: 'COMPLETED' | 'PROCESSING' | 'FLAGGED';
  fileSize: string;
  fileType: 'xlsx' | 'xls' | 'csv';
}

export interface ConsolidationSlot {
  id: number;
  slotLabel: string; // e.g. "SLOT PRIMARY", "SLOT SECONDARY", "SLOT AUXILIARY", "SLOT OPTIONAL"
  status: 'READY' | 'EMPTY';
  file?: File;
  fileName?: string;
  fileSize?: string;
  sheetCount?: number;
  rowCount?: number;
  colCount?: number;
  uploadedTimeAgo?: string;
  uploadedAt?: number;
  contentFingerprint?: string;
}

export interface MasterRow {
  rowNum: number;
  Priority: string;
  particulars: string;
  'vch type': string;
  'vch no.': string;
  date: string;
  debit: number;
  credit: number;
  'emr id': string;
  'jso order no': string;
  source: string;
  region: string;
  zone: number | string;
  part: string;
  state: string;
  'ba code': string;
  territory: string;
  city: string;
  type: string;
  status: string;
  'kisna/siva': string;
  'party name': string;
  nsm: string;
  'zone head': string;
  receivable_credit: number;
  outstanding: number;
  advance_payment: number;
}

export interface JobMetrics {
  fileCount?: number;
  sheetCount?: number;
  xlsxCount?: number;
  xlsCount?: number;
  recordCount?: number;
  duplicateRows?: number;
  patchedRows?: number;
  regionCount?: number;
  regions?: string[];
  durationSeconds?: number;
}

export interface DashboardKpis {
  totalMerges: number;
  mergeTrendPct: number;
  jobsThisWeek: number;
  sparkline: number[];
  filesProcessed: number;
  filesTrendPct: number;
  avgSheetsPerFile: number | null;
  xlsxCount: number;
  xlsCount: number;
  regionCount: number;
  hoursSaved: number;
  timeTrendPct: number;
  laborSaved: number;
  avgRunSeconds: number;
  qualityScore: number;
  qualityTrendPct: number;
  dupePct: number;
  patchedPct: number;
  deterministicValid: boolean;
}

export interface HistoryJob {
  id: string;
  jobCode: string; // e.g. "#SP-2024-8841"
  fileName: string;
  date: string;
  timeUTC: string;
  fileSize: string;
  fileType: string;
  status: 'OK' | 'ACTION_NEEDED';
  operator: string;
  recordsCount: string;
  sha256Seal: string;
  sourceFiles: string[];
  metrics?: JobMetrics;
}
