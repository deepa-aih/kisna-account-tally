import React, { useState, useRef } from 'react';
import * as XLSX from 'xlsx';
import { ConsolidationSlot, ActiveTab } from '../types';
import {
  FileSpreadsheet,
  CheckCircle2,
  Trash2,
  Plus,
  RefreshCw,
  ArrowRight,
  Check,
} from 'lucide-react';

interface NewMergeViewProps {
  slots: ConsolidationSlot[];
  setSlots: React.Dispatch<React.SetStateAction<ConsolidationSlot[]>>;
  setActiveTab: (tab: ActiveTab) => void;
  onShowToast: (message: string) => void;
  onProcessFiles: (filesByRole: Record<string, File>) => Promise<void> | void;
}

const slotNames = [
  'Branded',
  'RM Job',
  'Trade Receivable',
  'Master Data',
  'Sales Invoice',
];

const uploadRoles: Array<{ slotId: number; field: string; label: string; pattern: RegExp }> = [
  { slotId: 1, field: 'branded_file', label: 'Branded', pattern: /branded/i },
  { slotId: 2, field: 'rm_file', label: 'RM Job', pattern: /(^|[^a-z0-9])rm([^a-z0-9]|$)/i },
  { slotId: 3, field: 'receivable_file', label: 'Trade Receivable', pattern: /receivable/i },
  { slotId: 4, field: 'master_file', label: 'Master Data', pattern: /master/i },
  { slotId: 5, field: 'sale_file', label: 'Sales Invoice', pattern: /sale/i },
];

const getRoleForFileName = (fileName: string) =>
  uploadRoles.find(({ pattern }) => pattern.test(fileName));

export const NewMergeView: React.FC<NewMergeViewProps> = ({
  slots,
  setSlots,
  setActiveTab,
  onShowToast,
  onProcessFiles,
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const [isCheckingSchema, setIsCheckingSchema] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const filledSlots = slots.filter((s) => s.status === 'READY');
  const filledCount = filledSlots.length;
  const duplicateFingerprints = new Set(
    filledSlots
      .filter((slot) => slot.contentFingerprint)
      .map((slot) => slot.contentFingerprint!)
      .filter((fingerprint, index, fingerprints) => fingerprints.indexOf(fingerprint) !== index)
  );
  const handleRemoveSlot = (id: number) => {
    setSlots((prev) =>
      prev.map((slot) => {
        if (slot.id === id) {
          return {
            id: slot.id,
            slotLabel: slot.id === 5 ? 'SLOT OPTIONAL' : slot.slotLabel,
            status: 'EMPTY',
          };
        }
        return slot;
      })
    );
    onShowToast(`Removed Slot ${id}`);
  };

  const getFileFingerprint = async (file: File) => {
    if (!globalThis.crypto?.subtle) {
      throw new Error('Secure file validation is unavailable in this browser context.');
    }
    const contents = await file.arrayBuffer();
    const digest = await globalThis.crypto.subtle.digest('SHA-256', contents);
    return Array.from(new Uint8Array(digest), (byte) => byte.toString(16).padStart(2, '0')).join('');
  };

  const handleAddFile = async (file: File) => {
    const fileName = file.name;
    const extension = fileName.split('.').pop()?.toLowerCase();
    if (!['xlsx', 'xls', 'csv'].includes(extension || '')) {
      onShowToast(`${fileName} is not a supported workbook format.`);
      return;
    }
    if (file.size > 25 * 1024 * 1024) {
      onShowToast(`${fileName} exceeds the 25 MB per-workbook limit.`);
      return;
    }

    const fileSizeStr = (file.size / (1024 * 1024)).toFixed(1) + ' MB';
    let fileBuffer: ArrayBuffer;
    let contentFingerprint: string;
    try {
      fileBuffer = await file.arrayBuffer();
      contentFingerprint = await getFileFingerprint(file);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unable to validate this workbook.';
      onShowToast(message);
      return;
    }

    let sheetCount = 1;
    let rowCount = 0;
    let colCount = 0;
    try {
      const workbook = XLSX.read(fileBuffer, { type: 'array', sheetRows: 0 });
      sheetCount = workbook.SheetNames.length;
      for (const sheetName of workbook.SheetNames) {
        const sheet = workbook.Sheets[sheetName];
        const ref = sheet['!ref'];
        if (ref) {
          const range = XLSX.utils.decode_range(ref);
          // Sum rows across all sheets, take max column width
          rowCount += range.e.r; // e.r is last row index (0-based), so this = data rows
          colCount = Math.max(colCount, range.e.c + 1);
        }
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unable to read this workbook.';
      onShowToast(`${fileName} could not be read: ${message}`);
      return;
    }

    setSlots((prev) => {
      if (prev.some((slot) => slot.status === 'READY' && slot.contentFingerprint === contentFingerprint)) {
        onShowToast(`${fileName} is already uploaded. Duplicate workbooks cannot be assigned to multiple sources.`);
        return prev;
      }

      const role = getRoleForFileName(fileName);
      if (!role) {
        onShowToast(
          `${fileName} does not identify a required source. Include branded, RM, receivable, master, or sale in the filename.`
        );
        return prev;
      }

      const targetIndex = prev.findIndex((slot) => slot.id === role.slotId);
      if (targetIndex === -1) {
        onShowToast(`${role.label} source slot is unavailable.`);
        return prev;
      }
      if (prev[targetIndex].status === 'READY') {
        onShowToast(`${role.label} already has a workbook. Remove it before uploading another.`);
        return prev;
      }

      if (prev.every((slot) => slot.status === 'READY')) {
        onShowToast('All 5 consolidation slots are currently full.');
        return prev;
      }

      const updated = [...prev];
      const slot = updated[targetIndex];
      updated[targetIndex] = {
        ...slot,
        status: 'READY',
        file,
        fileName,
        fileSize: fileSizeStr,
        sheetCount,
        rowCount,
        colCount,
        uploadedTimeAgo: 'just now',
        uploadedAt: Math.max(Date.now(), ...prev.map((existingSlot) => (existingSlot.uploadedAt || 0) + 1)),
        contentFingerprint,
      };
      onShowToast(`Assigned ${fileName} to ${role.label}`);
      return updated;
    });
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const files = Array.from(e.target.files);
      void (async () => {
        for (const file of files) await handleAddFile(file);
      })();
      e.target.value = '';
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const files = Array.from(e.dataTransfer.files);
      void (async () => {
        for (const file of files) await handleAddFile(file);
      })();
    }
  };

  const handleClearAll = () => {
    setSlots((prev) =>
      prev.map((slot) => ({
        id: slot.id,
        slotLabel: slot.slotLabel,
        status: 'EMPTY',
      }))
    );
    onShowToast('Cleared all consolidation slots.');
  };

  const handleRecheckSchema = async () => {
    setIsCheckingSchema(true);
    try {
      const fingerprintEntries = await Promise.all(
        filledSlots
          .filter((slot) => slot.file)
          .map(async (slot) => [slot.id, await getFileFingerprint(slot.file!)] as const)
      );
      const fingerprints = fingerprintEntries.map(([, fingerprint]) => fingerprint);
      const fingerprintsBySlot = new Map(fingerprintEntries);
      setSlots((previousSlots) => previousSlots.map((slot) => ({
        ...slot,
        contentFingerprint: fingerprintsBySlot.get(slot.id) || slot.contentFingerprint,
      })));
      const duplicatesFound = new Set(fingerprints).size !== fingerprints.length;
      onShowToast(
        duplicatesFound
          ? 'Duplicate workbook content detected. Remove duplicate files before proceeding.'
          : `${filledSlots.filter((slot) => slot.file).length} of ${slotNames.length} required sources are available; no duplicate files found.`
      );
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unable to check uploaded workbooks.';
      onShowToast(message);
    } finally {
      setIsCheckingSchema(false);
    }
  };

  const handleProceed = async () => {
    const readySlots = slots.filter((slot) => slot.status === 'READY' && slot.file);
    if (readySlots.length === 0) {
      onShowToast('Please attach at least one workbook to consolidate.');
      return;
    }

    let fingerprints: string[];
    try {
      fingerprints = await Promise.all(readySlots.map((slot) =>
        slot.contentFingerprint || getFileFingerprint(slot.file!)
      ));
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unable to validate uploaded workbooks.';
      onShowToast(message);
      return;
    }
    if (new Set(fingerprints).size !== fingerprints.length) {
      onShowToast('Duplicate workbook content detected. Remove duplicate files before proceeding.');
      return;
    }

    const filesByRole: Record<string, File> = {};
    const duplicateRoles = new Set<string>();

    readySlots.forEach((slot) => {
      const role = slot.file ? getRoleForFileName(slot.file.name) : undefined;
      if (!role || !slot.file) {
        return;
      }
      if (filesByRole[role.field]) {
        duplicateRoles.add(role.label);
      } else {
        filesByRole[role.field] = slot.file;
      }
    });

    if (duplicateRoles.size > 0) {
      onShowToast(`Multiple files match these sources: ${Array.from(duplicateRoles).join(', ')}. Keep one per source.`);
      return;
    }

    const stillMissing = uploadRoles.filter(({ field }) => !filesByRole[field]);
    if (stillMissing.length > 0) {
      const labels = stillMissing.map((r) => r.label).join(', ');
      onShowToast(`Please upload the following required files: ${labels}`);
      return;
    }

    setIsProcessing(true);
    try {
      onShowToast('Submitting files to the FastAPI merge engine...');
      await onProcessFiles(filesByRole);
      setActiveTab('history');
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Merge failed';
      onShowToast(message);
    } finally {
      setIsProcessing(false);
    }
  };

  const iconStroke = '#45F0DF';

const FileUploadMark = ({ className }: { className?: string }) => (
  <svg viewBox="0 0 24 24" className={className} fill="none" aria-hidden="true">
    <path d="M7 3.5h6.2L18.5 8.8V19.5A1.5 1.5 0 0 1 17 21H8.5A1.5 1.5 0 0 1 7 19.5v-16Z" stroke={iconStroke} strokeWidth="1.7" strokeLinejoin="round" />
    <path d="M13 3.8V9h5.2" stroke={iconStroke} strokeWidth="1.7" strokeLinejoin="round" />
    <path d="M12.2 17.2v-5.2" stroke={iconStroke} strokeWidth="1.7" strokeLinecap="round" />
    <path d="M9.7 14.2 12.2 11.7l2.5 2.5" stroke={iconStroke} strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

const CloudUploadMark = ({ className }: { className?: string }) => (
  <svg viewBox="0 0 24 24" className={className} fill="none" aria-hidden="true">
    <path d="M7.2 17.5h8.8a3.2 3.2 0 0 0 .3-6.4 4.3 4.3 0 0 0-8.2 1.3 2.7 2.7 0 0 0-.9 5.1Z" stroke={iconStroke} strokeWidth="1.7" strokeLinejoin="round" />
    <path d="M12 16.6V11" stroke={iconStroke} strokeWidth="1.7" strokeLinecap="round" />
    <path d="M9.6 13.2 12 10.8l2.4 2.4" stroke={iconStroke} strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

const FolderMark = ({ className }: { className?: string }) => (
  <svg viewBox="0 0 24 24" className={className} fill="none" aria-hidden="true">
    <path d="M3.5 8.2A1.7 1.7 0 0 1 5.2 6.5h3.4l1.6 1.8h8.1A1.7 1.7 0 0 1 20 10v7.2a1.7 1.7 0 0 1-1.7 1.7H5.2A1.7 1.7 0 0 1 3.5 17.2V8.2Z" stroke={iconStroke} strokeWidth="1.7" strokeLinejoin="round" />
  </svg>
);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-slate-900 dark:text-white tracking-tight">New Merge</h1>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
          Configure sources and upload workbooks to start multi-entity consolidation
        </p>
      </div>
      {/* Hidden File Input */}
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileInputChange}
        multiple
        accept=".xlsx,.xls,.csv"
        className="hidden"
      />

      {/* Top Slot Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <span className="text-xs font-bold text-slate-700 dark:text-slate-300 tracking-wider uppercase">
            CONSOLIDATION SLOTS
          </span>
          <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-400 border border-emerald-200/60 dark:border-emerald-800/60 font-mono">
            {filledCount} of 5 Filled
          </span>
        </div>

        <div className="flex flex-wrap items-center justify-end gap-4 text-xs text-slate-500 dark:text-slate-400">
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block" />
            <span>Active</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-slate-300 dark:bg-slate-600 inline-block" />
            <span>Empty</span>
          </div>
          <button
            onClick={handleRecheckSchema}
            disabled={isCheckingSchema || filledCount === 0}
            className="inline-flex items-center gap-1.5 text-slate-600 dark:text-slate-300 hover:text-indigo-600 dark:hover:text-indigo-400 font-medium transition-colors disabled:opacity-40"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isCheckingSchema ? 'animate-spin' : ''}`} />
            <span>Check duplicate content</span>
          </button>
          <button
            onClick={handleClearAll}
            disabled={filledCount === 0}
            className="text-red-600 dark:text-red-400 hover:text-red-700 font-medium transition-colors disabled:opacity-40"
          >
            Clear All
          </button>
        </div>
      </div>

      {/* 5 Slots Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3.5">
        {slots.map((slot) => {
          const isFilled = slot.status === 'READY';

          if (!isFilled) {
            return (
              <div
                key={slot.id}
                onClick={() => fileInputRef.current?.click()}
                className="group border border-dashed border-slate-300 dark:border-slate-700 hover:border-[#151E49] rounded-2xl px-4 py-3.5 flex flex-col bg-white dark:bg-slate-900 transition-all cursor-pointer min-h-[196px]"
              >
                <div className="w-full flex items-center justify-between">
                  <span className="text-sm font-bold text-slate-900 dark:text-white">{slotNames[slot.id - 1]}</span>
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-slate-100 text-slate-400 uppercase tracking-wide">Empty</span>
                </div>
                <div className="my-auto flex flex-col items-center text-center pt-3">
                  <Plus className="w-4 h-4 text-slate-400 mb-2" />
                  <div className="text-xs font-semibold text-slate-800 dark:text-slate-200">Add workbook</div>
                  <div className="text-[11px] text-slate-400 mt-0.5">Waiting for upload</div>
                </div>
              </div>
            );
          }

          return (
            <div
              key={slot.id}
              className="bg-white dark:bg-slate-900 border-2 border-[#111D4A] border-t-4 border-t-[#111D4A] rounded-2xl px-4 py-3.5 flex flex-col min-h-[196px]"
            >
              <div className="flex items-center justify-between">
                <span className="text-sm font-bold text-slate-900 dark:text-white">{slotNames[slot.id - 1]}</span>
                <span
                  className={`px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500 text-white ${
                    slot.id === 3 ? '-mt-1' : ''
                  }`}
                >
                  READY
                </span>
              </div>

              <div className="mt-3 flex items-start gap-1.5">
                <FileSpreadsheet className="w-3.5 h-3.5 text-emerald-500 shrink-0 mt-0.5" />
                <div className="min-w-0">
                  <div className="text-xs font-semibold text-emerald-600 dark:text-emerald-400 truncate" title={slot.fileName}>
                    {slot.fileName}
                  </div>
                  <div className="mt-1 text-[11px] text-slate-400 leading-4">
                    <div>
                      {slot.fileSize} • {slot.sheetCount} Sheet{slot.sheetCount === 1 ? '' : 's'}
                    </div>
                    <div>{slot.rowCount?.toLocaleString()} Rows</div>
                  </div>
                </div>
              </div>

              <div className="mt-auto pt-3 flex items-center justify-between text-[11px]">
                <span className="inline-flex items-center gap-1 font-medium text-emerald-600">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  Parsed
                </span>
                <button
                  onClick={() => handleRemoveSlot(slot.id)}
                  className="text-slate-400 hover:text-red-600 text-[11px] inline-flex items-center gap-1 transition-colors"
                >
                  <Trash2 className="w-3 h-3" />
                  <span>Remove</span>
                </button>
              </div>
            </div>
          );
        })}
      </div>

      <div className="bg-white dark:bg-slate-900 border-2 border-[#111D4A] rounded-2xl overflow-hidden">
      {/* File Uploader Box */}
      <div className="p-5">
        <div className="flex items-center gap-2.5 mb-1">
          <div className="w-9 h-9 rounded-lg bg-[#111D4A] flex items-center justify-center shrink-0">
            <FileUploadMark className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-slate-900 dark:text-white">File Uploader</h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Intelligent batch ingest & automatic assignment to matching source cards
            </p>
          </div>
        </div>

        {/* Drag & Drop Zone */}
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setIsDragging(true);
          }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={handleDrop}
          className={`relative mt-4 flex min-h-[300px] flex-col items-center justify-center overflow-hidden rounded-2xl border-2 border-dashed p-8 text-center transition-all sm:p-10 ${
            isDragging
              ? 'border-[#20BFAF] bg-[#E9FBF8] dark:bg-emerald-950/30'
              : 'border-[#CDD7EC] bg-gradient-to-br from-[#F8FAFF] via-white to-[#F0F8F8] hover:border-[#9BAACB] dark:border-slate-700 dark:from-slate-900 dark:via-slate-900 dark:to-slate-800/80 dark:hover:border-slate-600'
          }`}
        >
          <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-[#111D4A] shadow-lg shadow-[#111D4A]/15 ring-4 ring-white/80 dark:ring-slate-800">
            <CloudUploadMark className="w-7 h-7" />
          </div>

          <h3 className="mb-1 text-base font-bold tracking-tight text-slate-900 dark:text-white sm:text-lg">
            Drop your workbooks here
          </h3>
          <p className="mb-6 max-w-lg text-sm leading-5 text-slate-500 dark:text-slate-400">
            Excel and CSV files are matched to the right source card by filename. Add one file or select several at once.
          </p>

          <button
            onClick={() => fileInputRef.current?.click()}
            className="inline-flex min-h-14 items-center gap-3 rounded-xl bg-[#111D4A] px-8 py-4 text-sm font-semibold text-white shadow-md shadow-[#111D4A]/15 transition-all hover:-translate-y-0.5 hover:bg-[#1B2A68] hover:shadow-lg focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-[#20E4D0]/30"
          >
            <FolderMark className="h-5 w-5" />
            <span>Browse Local Files</span>
            <ArrowRight className="h-4 w-4 opacity-75" />
          </button>

          <div className="mt-7 flex flex-wrap items-center justify-center gap-x-6 gap-y-2 border-t border-slate-200/70 pt-4 text-[11px] text-slate-500 dark:border-slate-700 dark:text-slate-400">
            <span className="inline-flex items-center gap-1"><Check className="w-3 h-3 text-emerald-500" /> Supported: .xlsx, .xls, .csv</span>
            <span className="inline-flex items-center gap-1"><Check className="w-3 h-3 text-emerald-500" /> Max file size: 25 MB per workbook</span>
            <span className="inline-flex items-center gap-1"><Check className="w-3 h-3 text-emerald-500" /> 256-bit In-Memory Encryption</span>
          </div>
        </div>
      </div>

      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-end gap-3 px-5 py-4 border-t border-[#111D4A]/15">
        <button
          onClick={handleProceed}
          disabled={isProcessing}
          className="inline-flex items-center gap-2 px-5 py-2.5 bg-[#151E49] text-white hover:bg-[#10183a] text-sm font-semibold rounded-lg shadow-xs transition-all disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isProcessing ? (
            <>
              <RefreshCw className="w-4 h-4 animate-spin" />
              <span>Processing...</span>
            </>
          ) : (
            <>
              <span>Validate Files & Run Merge</span>
              <ArrowRight className="w-4 h-4" />
            </>
          )}
        </button>
      </div>
      </div>
    </div>
  );
};
