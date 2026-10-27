/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState, useEffect } from 'react';
import { ActiveTab, RecentFile, ConsolidationSlot, HistoryJob, DashboardKpis, JobMetrics } from './types';
import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import { DashboardView } from './components/DashboardView';
import { NewMergeView } from './components/NewMergeView';
import { SpreadsheetView } from './components/SpreadsheetView';
import { HistoryView } from './components/HistoryView';
import { CostAnalysisView } from './components/CostAnalysisView';
import { AuditSealModal } from './components/AuditSealModal';
import { Toast } from './components/Toast';
import { AuthScreen } from './components/AuthScreen';
import { downloadDatasetAsCsv } from './utils/exportUtils';
import { getCurrentUser, getDashboardSummary, getJobs, getJobPreview, getJobSheets, signOut, uploadWorkbookBatch } from './lib/api';
import type { AuthUser } from './lib/api';

const SLOT_STORAGE_KEY = 'account-tally-consolidation-slots-v1';
const ACTIVE_TAB_STORAGE_KEY = 'account-tally-active-tab-v1';
const THEME_STORAGE_KEY = 'account-tally-theme-v1';
const SELECTED_FILE_STORAGE_KEY = 'account-tally-selected-file-v1';
const SELECTED_JOB_STORAGE_KEY = 'account-tally-selected-job-v1';
const RECENT_JOBS_STORAGE_KEY = 'account-tally-recent-jobs-v1';
const DASHBOARD_SUMMARY_STORAGE_KEY = 'account-tally-dashboard-summary-v1';
const VIEWER_ROWS_STORAGE_KEY = 'account-tally-viewer-rows-v1';
const SLOT_FILES_DB_NAME = 'account-tally-slot-files';
const SLOT_FILES_STORE_NAME = 'slot-files';

const metricsFromJob = (job: any): JobMetrics | undefined => {
  const stored = job?.metrics && typeof job.metrics === 'object' ? job.metrics : {};
  const rows = Array.isArray(job?.previewRows) ? job.previewRows : [];
  const regions = new Set<string>();
  const keyCounts = new Map<string, number>();
  let patched = 0;

  rows.forEach((row: Record<string, unknown>) => {
    const region = String(row?.region || '').trim();
    if (region && region.toLowerCase() !== 'nan') regions.add(region);
    const voucher = row?.['vch no.'];
    const key = `${voucher ?? ''}|${row?.date ?? ''}|${row?.['emr id'] ?? ''}`;
    if (voucher) keyCounts.set(key, (keyCounts.get(key) || 0) + 1);
    if (String(row?.source || '').toLowerCase() === 'rm' && row?.['jso order no']) patched += 1;
  });

  let duplicateRows = 0;
  keyCounts.forEach((count) => {
    if (count > 1) duplicateRows += count;
  });

  if (!rows.length && !Object.keys(stored).length) return undefined;

  return {
    ...stored,
    duplicateRows: stored.duplicateRows ?? duplicateRows,
    patchedRows: stored.patchedRows ?? patched,
    regionCount: stored.regionCount ?? regions.size,
    regions: stored.regions ?? Array.from(regions),
  };
};

const createEmptySlots = (): ConsolidationSlot[] =>
  Array.from({ length: 5 }, (_, index) => ({
    id: index + 1,
    slotLabel: index === 4 ? 'SLOT OPTIONAL' : `SLOT ${['PRIMARY', 'SECONDARY', 'AUXILIARY', 'AUXILIARY'][index] || 'PRIMARY'}`,
    status: 'EMPTY',
  }));

const normalizeSlotsForStorage = (slots: ConsolidationSlot[]) =>
  slots.map(({ id, slotLabel, status, fileName, fileSize, sheetCount, rowCount, colCount, uploadedTimeAgo, uploadedAt, contentFingerprint }) => ({
    id,
    slotLabel,
    status,
    fileName,
    fileSize,
    sheetCount,
    rowCount,
    colCount,
    uploadedTimeAgo,
    uploadedAt,
    contentFingerprint,
  }));

const openSlotFilesDb = (): Promise<IDBDatabase> =>
  new Promise((resolve, reject) => {
    if (typeof window === 'undefined' || !('indexedDB' in window)) {
      reject(new Error('IndexedDB is unavailable in this browser.'));
      return;
    }

    const request = window.indexedDB.open(SLOT_FILES_DB_NAME, 1);

    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains(SLOT_FILES_STORE_NAME)) {
        db.createObjectStore(SLOT_FILES_STORE_NAME, { keyPath: 'id' });
      }
    };

    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error ?? new Error('Unable to open file storage.'));
  });

const readPersistedSlotFiles = async (): Promise<Map<number, File>> => {
  if (typeof window === 'undefined' || !('indexedDB' in window)) {
    return new Map();
  }

  try {
    const db = await openSlotFilesDb();
    const transaction = db.transaction(SLOT_FILES_STORE_NAME, 'readonly');
    const store = transaction.objectStore(SLOT_FILES_STORE_NAME);

    const allRecords = await new Promise<Array<{ id: number; file: File }>>((resolve, reject) => {
      const request = store.getAll();
      request.onsuccess = () => resolve((request.result ?? []) as Array<{ id: number; file: File }>);
      request.onerror = () => reject(request.error ?? new Error('Unable to read stored files.'));
    });

    db.close();
    return new Map(
      allRecords
        .filter((record) => record && record.file instanceof File)
        .map((record) => [record.id, record.file])
    );
  } catch (error) {
    console.warn('Unable to restore uploaded workbook files.', error);
    return new Map();
  }
};

const savePersistedSlotFiles = async (slots: ConsolidationSlot[]) => {
  if (typeof window === 'undefined' || !('indexedDB' in window)) {
    return;
  }

  try {
    const db = await openSlotFilesDb();
    const transaction = db.transaction(SLOT_FILES_STORE_NAME, 'readwrite');
    const store = transaction.objectStore(SLOT_FILES_STORE_NAME);

    const readyFiles = slots.filter((slot) => slot.status === 'READY' && slot.file instanceof File);
	do {
      const request = store.clear();
      await new Promise<void>((resolve, reject) => {
        request.onsuccess = () => resolve();
        request.onerror = () => reject(request.error ?? new Error('Unable to clear old file storage.'));
      });
    } while (false);

    for (const slot of readyFiles) {
      const request = store.put({ id: slot.id, file: slot.file as File });
      await new Promise<void>((resolve, reject) => {
        request.onsuccess = () => resolve();
        request.onerror = () => reject(request.error ?? new Error('Unable to save workbook file.'));
      });
    }

    db.close();
  } catch (error) {
    console.warn('Unable to persist uploaded workbook files.', error);
  }
};

export default function App() {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [checkingSession, setCheckingSession] = useState(true);

  useEffect(() => {
    let active = true;
    void getCurrentUser()
      .then(({ user: currentUser }) => { if (active) setUser(currentUser); })
      .catch(() => { if (active) setUser(null); })
      .finally(() => { if (active) setCheckingSession(false); });
    return () => { active = false; };
  }, []);

  const handleSignOut = async () => {
    try {
      await signOut();
    } catch (error) {
      console.warn('Unable to revoke the server session during sign out.', error);
    } finally {
      setUser(null);
    }
  };

  if (checkingSession) {
    return <main className="min-h-screen bg-slate-950 flex items-center justify-center text-sm text-slate-400">Checking your session…</main>;
  }

  if (!user) {
    const resetToken = new URLSearchParams(window.location.search).get('reset') || undefined;
    return <AuthScreen key={resetToken || 'sign-in'} resetToken={resetToken} onSignedIn={setUser} />;
  }

  return <AuthenticatedApp user={user} onSignOut={() => { void handleSignOut(); }} />;
}

function AuthenticatedApp({ user, onSignOut }: { user: AuthUser; onSignOut: () => void }) {
  const [activeTab, setActiveTab] = useState<ActiveTab>('dashboard');
  const [isDark, setIsDark] = useState<boolean>(() => {
    return window.localStorage.getItem(THEME_STORAGE_KEY) === 'dark';
  });
  const [isOpenMobile, setIsOpenMobile] = useState<boolean>(false);
  const [recentFiles, setRecentFiles] = useState<RecentFile[]>([]);
  const [jobs, setJobs] = useState<HistoryJob[]>([]);
  const [dashboardSummary, setDashboardSummary] = useState({
    totalJobs: 0,
    successfulJobs: 0,
    flaggedJobs: 0,
    recordsProcessed: 0,
    recentFiles: [] as Array<Record<string, unknown>>,
    kpis: null as DashboardKpis | null,
  });
  const [slots, setSlots] = useState<ConsolidationSlot[]>(createEmptySlots);
  const [selectedFileName, setSelectedFileName] = useState<string>('');
  const [selectedJobId, setSelectedJobId] = useState<string>('');
  const [selectedFileRows, setSelectedFileRows] = useState<Array<Record<string, unknown>>>([]);
  const [selectedFileSheets, setSelectedFileSheets] = useState<Record<string, Array<Record<string, unknown>>>>({});
  const [auditJob, setAuditJob] = useState<HistoryJob | null>(null);
  const [auditSourceFile, setAuditSourceFile] = useState<string | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [hasRestoredSlots, setHasRestoredSlots] = useState(false);

  // Sync dark class with document element
  useEffect(() => {
    document.documentElement.classList.toggle('dark', isDark);
    document.documentElement.style.colorScheme = isDark ? 'dark' : 'light';
    window.localStorage.setItem(THEME_STORAGE_KEY, isDark ? 'dark' : 'light');
  }, [isDark]);

  useEffect(() => {
    if (typeof window === 'undefined') {
      return;
    }

    const queryTab = new URLSearchParams(window.location.search).get('tab') as ActiveTab | null;
    const savedTab = window.localStorage.getItem(ACTIVE_TAB_STORAGE_KEY) as ActiveTab | null;
    const savedSelectedFile = window.localStorage.getItem(SELECTED_FILE_STORAGE_KEY) ?? '';
    const savedSelectedJob = window.localStorage.getItem(SELECTED_JOB_STORAGE_KEY) ?? '';
    const savedViewerRows = window.localStorage.getItem(VIEWER_ROWS_STORAGE_KEY);

    const allowedTabs: ActiveTab[] = ['dashboard', 'new-merge', 'viewer', 'history', 'cost-analysis'];
    if (queryTab && allowedTabs.includes(queryTab)) {
      setActiveTab(queryTab);
    } else if (savedTab && allowedTabs.includes(savedTab)) {
      setActiveTab(savedTab);
    }

    if (savedSelectedFile) {
      setSelectedFileName(savedSelectedFile);
    }

    if (savedSelectedJob) {
      setSelectedJobId(savedSelectedJob);
    }

    if (savedViewerRows) {
      try {
        const parsedRows = JSON.parse(savedViewerRows);
        if (Array.isArray(parsedRows)) {
          setSelectedFileRows(parsedRows);
        }
      } catch (error) {
        console.warn('Unable to restore saved viewer rows.', error);
      }
    }

    try {
      const savedSlots = window.localStorage.getItem(SLOT_STORAGE_KEY);
      if (savedSlots) {
        const parsed = JSON.parse(savedSlots) as Array<Record<string, unknown>>;
        if (Array.isArray(parsed) && parsed.length > 0) {
          const savedMap = new Map<number, Record<string, unknown>>(
            parsed.map((slot) => [Number(slot.id), slot])
          );

          const slotEntries = createEmptySlots().map((slot) => {
            const savedSlot = savedMap.get(slot.id);
            if (!savedSlot) {
              return slot;
            }

            return {
              ...slot,
              ...savedSlot,
              status: savedSlot.status === 'READY' ? 'READY' : 'EMPTY',
            } as ConsolidationSlot;
          });

          void readPersistedSlotFiles().then((restoredFiles) => {
            setSlots(
              slotEntries.map((slot) => ({
                ...slot,
                file: restoredFiles.get(slot.id),
              }))
            );
            setHasRestoredSlots(true);
          });
          return;
        }
      }
    } catch (error) {
      console.warn('Unable to restore saved merge slots.', error);
    }

    setHasRestoredSlots(true);
  }, []);

  useEffect(() => {
    if (!hasRestoredSlots || typeof window === 'undefined') {
      return;
    }

    window.localStorage.setItem(ACTIVE_TAB_STORAGE_KEY, activeTab);
    window.localStorage.setItem(SELECTED_FILE_STORAGE_KEY, selectedFileName);
    window.localStorage.setItem(SELECTED_JOB_STORAGE_KEY, selectedJobId);
    window.localStorage.setItem(SLOT_STORAGE_KEY, JSON.stringify(normalizeSlotsForStorage(slots)));
    if (selectedFileRows.length > 0) {
      window.localStorage.setItem(VIEWER_ROWS_STORAGE_KEY, JSON.stringify(selectedFileRows));
    }
    void savePersistedSlotFiles(slots);
  }, [activeTab, hasRestoredSlots, selectedFileName, selectedJobId, selectedFileRows, slots]);

  const readCachedDashboardState = () => {
    if (typeof window === 'undefined') {
      return null;
    }

    try {
      const cachedJobs = window.localStorage.getItem(RECENT_JOBS_STORAGE_KEY);
      const cachedSummary = window.localStorage.getItem(DASHBOARD_SUMMARY_STORAGE_KEY);

      if (!cachedJobs && !cachedSummary) {
        return null;
      }

      const parsedJobs = cachedJobs ? JSON.parse(cachedJobs) : [];
      const parsedSummary = cachedSummary ? JSON.parse(cachedSummary) : null;

      if (!Array.isArray(parsedJobs) && !parsedSummary) {
        return null;
      }

      const resultJobs = Array.isArray(parsedJobs) ? parsedJobs : [];
      const recentFiles = resultJobs.map((job: any, index: number) => ({
        id: job.id,
        name: job.fileName,
        totalRows: Number(String(job.recordsCount || '0').replace(/[^\d]/g, '')) || 0,
        processingDate: job.date ? new Date(`${job.date}T${job.timeUTC || '00:00:00'}Z`).toLocaleDateString('en-US', {
          month: 'short',
          day: 'numeric',
          year: 'numeric',
        }) : 'Recently',
        durationSeconds: 32 + index * 4,
        status: job.status === 'OK' ? 'COMPLETED' : 'FLAGGED',
        fileSize: job.fileSize || '4.8 MB',
        fileType: (job.fileType || 'xlsx') as RecentFile['fileType'],
      }));

      return {
        jobs: resultJobs,
        recentFiles,
        summary: parsedSummary || {
          totalJobs: resultJobs.length,
          successfulJobs: resultJobs.filter((job: any) => job.status === 'OK').length,
          flaggedJobs: resultJobs.filter((job: any) => job.status !== 'OK').length,
          recordsProcessed: resultJobs.reduce((sum: number, job: any) => sum + (Number(String(job.recordsCount || '0').replace(/[^\d]/g, '')) || 0), 0),
          recentFiles: resultJobs.map((job: any) => ({ fileName: job.fileName, status: job.status })),
        },
      };
    } catch (error) {
      console.warn('Unable to read cached recent jobs.', error);
      return null;
    }
  };

  const loadRecentJobs = async () => {
    const cachedState = readCachedDashboardState();

    // Use browser cache immediately for a quick UI restore, but prefer the backend's persisted
    // state once it responds. The backend is the source of truth for recent jobs and summary.
    if (cachedState) {
      setJobs(cachedState.jobs);
      setRecentFiles(cachedState.recentFiles);
      setDashboardSummary(cachedState.summary);
      const latestFileName = Array.isArray(cachedState.summary?.recentFiles) && cachedState.summary.recentFiles[0]
        ? String(cachedState.summary.recentFiles[0].fileName || '')
        : cachedState.jobs[0]?.fileName || '';
      if (latestFileName) {
        setSelectedFileName(latestFileName);
      }
    }

    try {
      const [summary, jobsResponse] = await Promise.all([getDashboardSummary(), getJobs()]);
      const normalizedJobs = Array.isArray(jobsResponse)
        ? jobsResponse.map((job: any, index: number) => ({
            id: String(job.id || `job-${index + 1}`),
            jobCode: String(job.jobCode || `#SP-${index + 1}`),
            fileName: String(job.fileName || 'Merged Workbook.xlsx'),
            date: String(job.date || new Date().toISOString().slice(0, 10)),
            timeUTC: String(job.timeUTC || '00:00:00'),
            fileSize: String(job.fileSize || '7.2 MB'),
            fileType: String(job.fileType || 'xlsx'),
            status: job.status === 'OK' ? 'OK' : 'ACTION_NEEDED',
            operator: String(job.operator || 'Kisna Ops'),
            recordsCount: String(job.recordsCount || '0'),
            sha256Seal: String(job.sha256Seal || 'n/a'),
            sourceFiles: Array.isArray(job.sourceFiles) ? job.sourceFiles.map(String) : [],
            metrics: metricsFromJob(job),
          }))
        : [];

      const normalizedRecentFiles = normalizedJobs.map((job, index) => ({
        id: job.id,
        name: job.fileName,
        totalRows: Number(String(job.recordsCount || '0').replace(/[^\d]/g, '')) || 0,
        processingDate: job.date ? new Date(`${job.date}T${job.timeUTC || '00:00:00'}Z`).toLocaleDateString('en-US', {
          month: 'short',
          day: 'numeric',
          year: 'numeric',
        }) : 'Recently',
        durationSeconds: 32 + index * 4,
        status: job.status === 'OK' ? 'COMPLETED' : 'FLAGGED',
        fileSize: job.fileSize || '4.8 MB',
        fileType: (job.fileType || 'xlsx') as RecentFile['fileType'],
      }));

      const nextDashboardSummary = summary && typeof summary === 'object'
        ? {
            totalJobs: Number(summary.totalJobs || normalizedJobs.length || 0),
            successfulJobs: Number(summary.successfulJobs || normalizedJobs.filter((job) => job.status === 'OK').length || 0),
            flaggedJobs: Number(summary.flaggedJobs || normalizedJobs.filter((job) => job.status !== 'OK').length || 0),
            recordsProcessed: Number(summary.recordsProcessed || normalizedJobs.reduce((sum, job) => sum + Number(String(job.recordsCount || '0').replace(/[^\d]/g, '')) || 0, 0) || 0),
            recentFiles: Array.isArray(summary.recentFiles) ? summary.recentFiles : [],
            kpis: summary.kpis && typeof summary.kpis === 'object' ? (summary.kpis as DashboardKpis) : null,
          }
        : {
            totalJobs: normalizedJobs.length,
            successfulJobs: normalizedJobs.filter((job) => job.status === 'OK').length,
            flaggedJobs: normalizedJobs.filter((job) => job.status !== 'OK').length,
            recordsProcessed: normalizedJobs.reduce((sum, job) => sum + Number(String(job.recordsCount || '0').replace(/[^\d]/g, '')) || 0, 0),
            recentFiles: normalizedJobs.map((job) => ({ fileName: job.fileName, status: job.status })),
            kpis: null,
          };

      const hasBackendData = normalizedJobs.length > 0 || nextDashboardSummary.totalJobs > 0;

      if (hasBackendData) {
        // Backend job data is authoritative; replace any browser cached snapshot with the server state.
        setJobs(normalizedJobs);
        setRecentFiles(normalizedRecentFiles);
        setDashboardSummary(nextDashboardSummary);

        if (typeof window !== 'undefined') {
          window.localStorage.setItem(RECENT_JOBS_STORAGE_KEY, JSON.stringify(normalizedJobs));
          window.localStorage.setItem(DASHBOARD_SUMMARY_STORAGE_KEY, JSON.stringify(nextDashboardSummary));
        }

        const latestFileName = Array.isArray(nextDashboardSummary.recentFiles) && nextDashboardSummary.recentFiles[0]
          ? String(nextDashboardSummary.recentFiles[0].fileName || '')
          : normalizedJobs[0]?.fileName || '';
        if (latestFileName) {
          setSelectedFileName(latestFileName);
        }
      } else if (cachedState) {
        // Fall back to browser cache only when the backend has no persisted jobs yet.
        setJobs(cachedState.jobs);
        setRecentFiles(cachedState.recentFiles);
        setDashboardSummary(cachedState.summary);
      } else {
        setJobs([]);
        setRecentFiles([]);
        setDashboardSummary({ totalJobs: 0, successfulJobs: 0, flaggedJobs: 0, recordsProcessed: 0, recentFiles: [], kpis: null });
      }
    } catch (error) {
      console.warn('Unable to load jobs from the backend. Using cached dashboard state if available.', error);

      if (cachedState) {
        setJobs(cachedState.jobs);
        setRecentFiles(cachedState.recentFiles);
        setDashboardSummary(cachedState.summary);
        return;
      }

      setJobs([]);
      setRecentFiles([]);
      setDashboardSummary({ totalJobs: 0, successfulJobs: 0, flaggedJobs: 0, recordsProcessed: 0, recentFiles: [], kpis: null });
      setSelectedFileName('');
    }
  };

  useEffect(() => {
    void loadRecentJobs();
  }, []);

  const loadRowsForSelectedFile = async (jobId?: string) => {
    if (!jobId) {
      setSelectedFileRows([]);
      setSelectedFileSheets({});
      return;
    }

    const [previewResult, sheetsResult] = await Promise.allSettled([
      getJobPreview(jobId),
      getJobSheets(jobId),
    ]);

    if (previewResult.status === 'rejected') {
      console.warn('Unable to load selected file rows from backend.', previewResult.reason);
      setSelectedFileRows([]);
      setSelectedFileSheets({});
      return;
    }

    const previewRows = Array.isArray(previewResult.value?.rows) ? previewResult.value.rows : [];
    const sheets =
      sheetsResult.status === 'fulfilled' && sheetsResult.value?.sheets
        ? sheetsResult.value.sheets
        : {};
    if (sheetsResult.status === 'rejected') {
      console.warn('Unable to load workbook sheets from backend.', sheetsResult.reason);
    }

    setSelectedFileSheets(sheets);
    setSelectedFileRows(
      Array.isArray(sheets['Final Merged']) ? sheets['Final Merged'] : previewRows
    );
  };

  const handleSelectFileToView = async (fileName: string) => {
    setSelectedFileName(fileName);
    const matchedJob = jobs.find((job) => job.fileName === fileName);
    const nextJobId = matchedJob?.id || selectedJobId;
    setSelectedJobId(nextJobId);
    if (nextJobId) {
      await loadRowsForSelectedFile(nextJobId);
    } else {
      setSelectedFileRows([]);
      setSelectedFileSheets({});
    }
  };

  useEffect(() => {
    if (!selectedFileName || !jobs.length) {
      return;
    }

    const matchedJob = jobs.find((job) => job.fileName === selectedFileName);
    if (matchedJob && matchedJob.id !== selectedJobId) {
      setSelectedJobId(matchedJob.id);
    }

    if (matchedJob && matchedJob.id) {
      void loadRowsForSelectedFile(matchedJob.id);
    }
  }, [selectedFileName, jobs]);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => {
      setToastMessage((current) => (current === msg ? null : current));
    }, 3500);
  };

  const handleDownloadConsolidated = () => {
    if (!selectedFileName) {
      showToast('No consolidated workbook is available yet.');
      return;
    }

    downloadDatasetAsCsv(
      selectedFileName,
      [
        'Row',
        '_Source_Entity',
        'Transaction_ID',
        'Cost_Center',
        'GL_Account',
        'Vendor_Name',
        'Invoice_Date',
        'Currency',
        'Local_Amount',
        'Consolidated_USD',
        'Reconciliation_Status',
      ],
      []
    );
    showToast(`Downloading consolidated workbook ${selectedFileName}`);
  };

  const handleProcessFiles = async (filesByRole: Record<string, File>) => {
    try {
      const response = await uploadWorkbookBatch(filesByRole);
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'Final_Merged_Monthly_Summary.xlsx';
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
      await loadRecentJobs();
      showToast('Merge complete. Workbook downloaded successfully.');
      setActiveTab('history');
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Merge failed';
      showToast(message);
    }
  };

  return (
    <div className="app-page-background min-h-screen text-slate-900 dark:text-slate-100 flex transition-colors">
      {/* Sidebar Navigation */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        isOpenMobile={isOpenMobile}
        setIsOpenMobile={setIsOpenMobile}
      />

      {/* Main Content Area */}
      <div className="flex-1 lg:pl-64 flex flex-col min-w-0">
        {/* Top Header */}
        <Header
          user={user}
          onSignOut={onSignOut}
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          isDark={isDark}
          setIsDark={setIsDark}
          setIsOpenMobile={setIsOpenMobile}
          onDownloadConsolidated={handleDownloadConsolidated}
          selectedFileName={selectedFileName}
        />

        {/* Viewport Content */}
        <main className="flex-1 p-4 sm:p-8 max-w-7xl w-full mx-auto">
          {activeTab === 'dashboard' && (
            <DashboardView
              recentFiles={recentFiles}
              jobs={jobs}
              dashboardSummary={dashboardSummary}
              setActiveTab={setActiveTab}
              onSelectFileToView={handleSelectFileToView}
              onShowToast={showToast}
            />
          )}

          {activeTab === 'new-merge' && (
            <NewMergeView
              slots={slots}
              setSlots={setSlots}
              setActiveTab={setActiveTab}
              onShowToast={showToast}
              onProcessFiles={handleProcessFiles}
            />
          )}

          {activeTab === 'viewer' && (
            <SpreadsheetView
              rows={selectedFileRows}
              sheets={selectedFileSheets}
            />
          )}

          {activeTab === 'history' && (
            <HistoryView
              jobs={jobs}
              summary={dashboardSummary}
              onSelectSourceFileForAudit={(job, sourceFile) => {
                setAuditJob(job);
                setAuditSourceFile(sourceFile);
              }}
              onShowToast={showToast}
            />
          )}

          {activeTab === 'cost-analysis' && (
            <CostAnalysisView onShowToast={showToast} />
          )}
        </main>
      </div>

      {/* Modals & Feedback */}
      <AuditSealModal
        job={auditJob}
        selectedSourceFile={auditSourceFile}
        onClose={() => {
          setAuditJob(null);
          setAuditSourceFile(null);
        }}
        onShowToast={showToast}
      />

      <Toast message={toastMessage} onClose={() => setToastMessage(null)} />
    </div>
  );
}
