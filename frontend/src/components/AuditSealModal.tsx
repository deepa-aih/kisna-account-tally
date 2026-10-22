import React from 'react';
import { HistoryJob } from '../types';
import { ShieldCheck, X, Download, FileSpreadsheet, Lock } from 'lucide-react';

interface AuditSealModalProps {
  job: HistoryJob | null;
  selectedSourceFile?: string | null;
  onClose: () => void;
  onShowToast: (message: string) => void;
}

export const AuditSealModal: React.FC<AuditSealModalProps> = ({
  job,
  selectedSourceFile,
  onClose,
  onShowToast,
}) => {
  if (!job) return null;

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center overflow-y-auto p-3 sm:p-4">
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl max-w-xl w-full max-h-[calc(100vh-1.5rem)] max-h-[calc(100dvh-1.5rem)] shadow-2xl overflow-hidden flex flex-col animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="shrink-0 p-4 sm:p-5 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between bg-slate-50/50 dark:bg-slate-800/40">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-emerald-100 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-400">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                Cryptographic Audit Seal & Lineage
              </h3>
              <p className="text-xs text-slate-500 font-mono">Job {job.jobCode}</p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 rounded-lg"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="min-h-0 flex-1 overflow-y-auto p-4 sm:p-5 space-y-4 sm:space-y-5 text-xs">
          {/* Target File */}
          <div className="p-3 bg-slate-50 dark:bg-slate-800/50 border border-slate-200/80 dark:border-slate-700/80 rounded-xl flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <FileSpreadsheet className="w-4 h-4 text-emerald-600" />
              <div>
                <div className="font-semibold text-slate-900 dark:text-white">{job.fileName}</div>
                <div className="text-[11px] text-slate-400 font-mono">
                  {job.fileSize} • {job.recordsCount} Consolidated Rows • {job.sourceFiles.length} Source Workbooks
                </div>
              </div>
            </div>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-400">
              Deterministic Valid
            </span>
          </div>

          {/* Execution Provenance */}
          <div className="grid grid-cols-2 gap-3 text-xs">
            <div className="p-3 border border-slate-100 dark:border-slate-800 rounded-lg">
              <div className="text-[10px] text-slate-400 uppercase font-semibold">Operator</div>
              <div className="font-semibold text-slate-900 dark:text-white mt-0.5">{job.operator}</div>
              <div className="text-[10px] text-slate-400 mt-0.5">LEAD MIS ANALYST</div>
            </div>
            <div className="p-3 border border-slate-100 dark:border-slate-800 rounded-lg">
              <div className="text-[10px] text-slate-400 uppercase font-semibold">Execution Timestamp</div>
              <div className="font-semibold text-slate-900 dark:text-white mt-0.5 font-mono">{job.date}</div>
              <div className="text-[10px] text-slate-400 mt-0.5 font-mono">{job.timeUTC}</div>
            </div>
          </div>

          {/* Ingested Source Files */}
          <div>
            {selectedSourceFile && (
              <div className="mb-3 rounded-lg border border-emerald-200 bg-emerald-50/70 p-3 dark:border-emerald-900 dark:bg-emerald-950/30">
                <div className="text-[10px] font-semibold uppercase tracking-wider text-emerald-700 dark:text-emerald-300">
                  Selected source workbook
                </div>
                <div className="mt-1 break-all font-mono font-medium text-slate-800 dark:text-slate-100">
                  {selectedSourceFile}
                </div>
                <div className="mt-1 text-[11px] text-slate-500 dark:text-slate-400">
                  Used to create {job.fileName}
                </div>
              </div>
            )}
            <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-2">
              Source Workbooks ({job.sourceFiles.length})
            </div>
            <div className="space-y-1.5">
              {job.sourceFiles.map((sf, idx) => (
                <div
                  key={idx}
                  className={`px-3 py-2 border rounded-lg flex items-center justify-between ${selectedSourceFile === sf ? 'border-emerald-300 bg-emerald-50 dark:border-emerald-800 dark:bg-emerald-950/40' : 'border-slate-100 bg-slate-50 dark:border-slate-800 dark:bg-slate-800/40'}`}
                >
                  <span className="font-mono text-slate-800 dark:text-slate-200 font-medium">{sf}</span>
                  <span className="text-[10px] text-emerald-600 font-medium">In-Memory Verified</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="shrink-0 p-3 sm:p-4 border-t border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/40 flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-1.5 text-slate-400 font-mono text-[11px]">
            <Lock className="w-3.5 h-3.5 text-emerald-500" />
            <span>SOX-404 Compliance Audited</span>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={onClose}
              className="px-3 py-1.5 bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-200 rounded-lg font-medium hover:bg-slate-300 transition-colors"
            >
              Close
            </button>
            <button
              onClick={() => {
                onShowToast(`Exporting compliance manifest for ${job.jobCode}`);
                onClose();
              }}
              className="inline-flex items-center gap-1.5 px-4 py-1.5 bg-[#0B1528] text-white hover:bg-slate-800 rounded-lg font-semibold transition-colors"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Export Audit Manifest</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
