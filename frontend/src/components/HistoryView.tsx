import React, { useState } from 'react';
import { HistoryJob } from '../types';
import {
  LayoutGrid,
  FileSpreadsheet,
  ShieldCheck,
  AlertTriangle,
  Search,
  Download,
  Shield,
  ChevronLeft,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
  Filter,
  ArrowUpRight,
} from 'lucide-react';
import { downloadDatasetAsCsv } from '../utils/exportUtils';

interface HistoryViewProps {
  jobs: HistoryJob[];
  summary: {
    totalJobs: number;
    successfulJobs: number;
    flaggedJobs: number;
    recordsProcessed: number;
    recentFiles: Array<Record<string, unknown>>;
  };
  onSelectSourceFileForAudit: (job: HistoryJob, sourceFile: string) => void;
  onShowToast: (message: string) => void;
}

export const HistoryView: React.FC<HistoryViewProps> = ({
  jobs,
  summary,
  onSelectSourceFileForAudit,
  onShowToast,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [modeFilter, setModeFilter] = useState('ALL');
  const [operatorFilter, setOperatorFilter] = useState('ALL');
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [currentPage, setCurrentPage] = useState(1);

  const parseRecordCount = (job: HistoryJob) =>
    job.metrics?.recordCount ?? (Number(String(job.recordsCount || '0').replace(/[^\d]/g, '')) || 0);
  const totalJobs = jobs.length || summary.totalJobs;
  const successfulJobs = jobs.length
    ? jobs.filter((job) => job.status === 'OK').length
    : summary.successfulJobs;
  const flaggedJobs = jobs.length
    ? jobs.filter((job) => job.status !== 'OK').length
    : summary.flaggedJobs;
  const recordsProcessed = jobs.length
    ? jobs.reduce((total, job) => total + parseRecordCount(job), 0)
    : summary.recordsProcessed;
  const duplicateRows = jobs.reduce((total, job) => total + (job.metrics?.duplicateRows || 0), 0);
  const now = new Date();
  const thisMonthJobs = jobs.filter((job) => {
    const date = new Date(`${job.date}T00:00:00`);
    return !Number.isNaN(date.getTime()) &&
      date.getFullYear() === now.getFullYear() &&
      date.getMonth() === now.getMonth();
  }).length;
  const previousMonth = new Date(now.getFullYear(), now.getMonth() - 1, 1);
  const previousMonthJobs = jobs.filter((job) => {
    const date = new Date(`${job.date}T00:00:00`);
    return !Number.isNaN(date.getTime()) &&
      date.getFullYear() === previousMonth.getFullYear() &&
      date.getMonth() === previousMonth.getMonth();
  }).length;
  const monthOverMonthChange = previousMonthJobs
    ? ((thisMonthJobs - previousMonthJobs) / previousMonthJobs) * 100
    : null;

  const filteredJobs = jobs.filter((job) => {
    const term = searchTerm.toLowerCase();
    const matchesSearch =
      job.fileName.toLowerCase().includes(term) ||
      job.jobCode.toLowerCase().includes(term) ||
      job.operator.toLowerCase().includes(term) ||
      job.sourceFiles.some((sourceFile) => sourceFile.toLowerCase().includes(term));

    const matchesOperator =
      operatorFilter === 'ALL' || job.operator.toLowerCase().includes(operatorFilter.toLowerCase());

    const matchesMode =
      modeFilter === 'ALL' ||
      (modeFilter === 'STRICT' && job.status === 'OK') ||
      (modeFilter === 'FUZZY' && job.status !== 'OK');

    return matchesSearch && matchesOperator && matchesMode;
  });

  const totalPages = Math.max(1, Math.ceil(filteredJobs.length / rowsPerPage));
  const safeCurrentPage = Math.min(currentPage, totalPages);
  const startIndex = (safeCurrentPage - 1) * rowsPerPage;
  const paginatedJobs = filteredJobs.slice(startIndex, startIndex + rowsPerPage);

  const formatCompactNumber = (value: number) => {
    if (value >= 1000000) return `${(value / 1000000).toFixed(2)}M`;
    if (value >= 1000) return `${(value / 1000).toFixed(1)}K`;
    return value.toString();
  };

  const handleDownload = (job: HistoryJob, e: React.MouseEvent) => {
    e.stopPropagation();
    downloadDatasetAsCsv(
      job.fileName,
      ['Source_File', 'Job_ID', 'Operator', 'Timestamp_UTC', 'SHA256_Cryptographic_Seal'],
      [
        [job.sourceFiles[0] || 'Source.xlsx', job.jobCode, job.operator, `${job.date} ${job.timeUTC}`, job.sha256Seal]
      ]
    );
    onShowToast(`Downloading signed workbook ${job.fileName}`);
  };

  return (
    <div className="space-y-6">
      <div>
        <div className="mb-3 flex items-center gap-1.5 text-xs leading-tight text-slate-500 dark:text-slate-400">
          <LayoutGrid className="h-3.5 w-3.5 text-[#59658F]" />
          <span>Dashboard</span>
          <span className="text-slate-300 dark:text-slate-600">/</span>
          <span className="bg-[#E8ECFA] px-1.5 py-0.5 font-medium text-[#17234F] dark:bg-slate-800 dark:text-slate-200">
            History
          </span>
        </div>
        <h1 className="text-3xl font-bold tracking-tight text-[#17234F] dark:text-white">
          File History
        </h1>
        <p className="mt-1 max-w-4xl text-sm leading-5 text-slate-600 dark:text-slate-400">
          Search, filter, inspect provenance, and download consolidated workbooks across all historical merge executions with cryptographic audit seals.
        </p>
      </div>

      {/* 4 Summary Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 items-stretch gap-3">
        {/* Card 1: TOTAL JOBS EXECUTED */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 border-t-[4px] border-t-[#45F0DF] rounded-sm p-3 shadow-xs flex flex-col">
          <div>
            <div className="flex items-start justify-between gap-3 mb-1">
              <span className="max-w-[170px] text-xs leading-tight font-bold text-[#111D4A] dark:text-slate-200 uppercase tracking-wider">
                TOTAL JOBS EXECUTED
              </span>
              <div className="w-8 h-8 rounded-lg bg-[#EEF0FF] dark:bg-slate-800 text-[#111D4A] dark:text-slate-200 flex items-center justify-center shrink-0">
                <LayoutGrid className="w-4 h-4" />
              </div>
            </div>

            <div className="flex flex-wrap items-baseline gap-x-2 gap-y-0">
              <span className="text-3xl leading-tight font-extrabold text-[#17234F] dark:text-white tracking-tight">
                {totalJobs.toLocaleString()}
              </span>
              {monthOverMonthChange !== null && (
                <span className={`inline-flex items-center gap-0.5 text-xs font-semibold ${monthOverMonthChange >= 0 ? 'text-[#007A70] dark:text-teal-300' : 'text-rose-700 dark:text-rose-300'}`}>
                  <ArrowUpRight className={`w-3.5 h-3.5 ${monthOverMonthChange < 0 ? 'rotate-90' : ''}`} />
                  {monthOverMonthChange >= 0 ? '+' : ''}{monthOverMonthChange.toFixed(1)}% MoM
                </span>
              )}
            </div>
          </div>

        </div>

        {/* Card 2: RECORDS CONSOLIDATED */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 border-t-[4px] border-t-[#535D94] rounded-sm p-3 shadow-xs flex flex-col">
          <div>
            <div className="flex items-start justify-between gap-3 mb-1">
              <span className="max-w-[175px] text-[17px] leading-6 font-semibold text-[#4B4B55] dark:text-slate-200 uppercase tracking-[0.02em]">
                RECORDS CONSOLIDATED
              </span>
              <div className="w-8 h-8 rounded-sm bg-[#EEF0FF] dark:bg-slate-800 text-[#111D4A] dark:text-slate-200 flex items-center justify-center shrink-0">
                <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" className="w-5 h-5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="3.5" y="4.5" width="17" height="15" rx="1" />
                  <path d="M4 9h16M4 14h16M8 5v14" />
                </svg>
              </div>
            </div>

            <div className="flex items-baseline gap-1.5 mt-1">
              <span className="text-3xl leading-tight font-bold text-[#17234F] dark:text-white tracking-tight">
                {recordsProcessed >= 1000000
                  ? `${(recordsProcessed / 1000000).toFixed(2)}M`
                  : formatCompactNumber(recordsProcessed)}
              </span>
              <span className="text-sm font-normal text-[#4B4B55] dark:text-slate-300">Rows</span>
            </div>
          </div>

        </div>

        {/* Card 3: SUCCESSFUL MERGES */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 border-t-[4px] border-t-[#00796B] rounded-sm p-3 shadow-xs flex flex-col">
          <div>
            <div className="flex items-start justify-between gap-3 mb-1">
              <span className="max-w-[175px] text-[17px] leading-6 font-semibold text-[#4B4B55] dark:text-slate-200 uppercase tracking-[0.02em]">
                SUCCESSFUL MERGES
              </span>
              <div className="w-8 h-8 rounded-sm bg-[#EEF0FF] dark:bg-slate-800 text-[#111D4A] dark:text-slate-200 flex items-center justify-center shrink-0">
                <ShieldCheck className="w-5 h-5" />
              </div>
            </div>

            <div className="flex items-baseline gap-2 mt-1">
              <span className="text-3xl leading-tight font-bold text-[#17234F] dark:text-white tracking-tight">
                {successfulJobs}
              </span>
              <span className="text-base leading-6 font-bold text-[#00796B] bg-[#A6F5EC] dark:bg-teal-900/70 dark:text-teal-200 px-2 rounded-sm">
                OK
              </span>
            </div>
          </div>

        </div>

        {/* Card 4: FAILED / FLAGGED JOBS */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 border-t-[4px] border-t-[#C91C24] rounded-sm p-3 shadow-xs flex flex-col">
          <div>
            <div className="flex items-start justify-between gap-3 mb-1">
              <span className="max-w-[180px] text-[17px] leading-6 font-semibold text-[#C91C24] dark:text-red-300 uppercase tracking-[0.02em]">
                FAILED / FLAGGED JOBS
              </span>
              <div className="w-8 h-8 rounded-sm bg-[#FDE9E8] dark:bg-red-950/60 text-[#C91C24] dark:text-red-300 flex items-center justify-center shrink-0">
                <AlertTriangle className="w-5 h-5" />
              </div>
            </div>

            <div className="flex flex-wrap items-baseline gap-2 mt-1">
              <span className="text-3xl leading-tight font-bold text-[#C91C24] dark:text-red-300 tracking-tight">
                {flaggedJobs}
              </span>
              <span className="text-base leading-6 font-semibold text-[#C91C24] bg-[#FAD9D7] dark:bg-red-950/70 dark:text-red-200 px-2 rounded-sm">
                Action Needed
              </span>
            </div>
          </div>

        </div>
      </div>

      {/* Main Table Container */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 rounded-xl shadow-xs overflow-hidden">
        {/* Search & Filter Toolbar */}
        <div className="p-4 sm:px-6 sm:py-5 border-b border-slate-100 dark:border-slate-800 flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4">
          <div className="relative flex-1 min-w-0 md:max-w-sm">
            <Search className="w-[18px] h-[18px] absolute left-4 top-1/2 -translate-y-1/2 text-[#111D4A]/55 dark:text-slate-400" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search Job ID, merge name, operator, or file..."
              className="w-full h-11 pl-11 pr-16 text-xs bg-[#F8F9FC] dark:bg-slate-800 border border-[#D9DFEC] dark:border-slate-700 rounded-lg text-[#111D4A] dark:text-white placeholder:text-slate-400 focus:outline-hidden focus:ring-2 focus:ring-[#111D4A]/20 focus:border-[#111D4A]"
            />
            <div className="absolute right-3 top-1/2 -translate-y-1/2 px-1.5 py-0.5 rounded bg-[#E9ECF4] dark:bg-slate-700 text-[10px] font-mono text-slate-500 dark:text-slate-400">
              ⌘ F
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2 text-xs">
            {/* Mode Filter */}
            <div className="flex items-center gap-1.5">
              <span className="text-slate-400 font-semibold text-[11px]">MODE:</span>
              <select
                value={modeFilter}
                onChange={(e) => setModeFilter(e.target.value)}
                className="px-2.5 py-1.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg font-medium text-slate-700 dark:text-slate-300 focus:outline-hidden"
              >
                <option value="ALL">All Merge Modes</option>
                <option value="STRICT">Strict Chart-of-Accounts</option>
                <option value="FUZZY">Fuzzy Key Matching</option>
                <option value="AUTO_FX">Auto FX Conversion</option>
              </select>
            </div>

            {/* Operator Filter */}
            <div className="flex items-center gap-1.5">
              <span className="text-slate-400 font-semibold text-[11px]">OPERATOR:</span>
              <select
                value={operatorFilter}
                onChange={(e) => setOperatorFilter(e.target.value)}
                className="px-2.5 py-1.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg font-medium text-slate-700 dark:text-slate-300 focus:outline-hidden"
              >
                <option value="ALL">All Operators</option>
                <option value="Priya Sharma">Priya Sharma</option>
                <option value="David Miller">David Miller</option>
                <option value="Sarah Jenkins">Sarah Jenkins</option>
              </select>
            </div>
          </div>
        </div>

        {/* Data Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#111D4A] text-[11px] font-semibold text-white uppercase tracking-wider border-b border-[#111D4A]">
              <tr>
                <th className="py-3 px-6">FILE NAME</th>
                <th className="py-3 px-6">SOURCE FILES</th>
                <th className="py-3 px-6">DATE</th>
                <th className="py-3 px-6">FILE SIZE</th>
                <th className="py-3 px-6">FILE TYPE</th>
                <th className="py-3 px-6 text-right">DOWNLOAD</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {paginatedJobs.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-slate-400 dark:text-slate-500">
                    No matching historical consolidation jobs found.
                  </td>
                </tr>
              ) : (
                paginatedJobs.map((job) => (
                  <tr
                    key={job.id}
                    className="bg-[#F0F3FF] dark:bg-slate-800/70 hover:bg-[#E7ECFF] dark:hover:bg-slate-800 transition-colors group"
                  >
                    {/* FILE NAME & Job ID */}
                    <td className="py-3.5 px-6">
                      <div className="flex items-start gap-3">
                        <div className="p-1 rounded bg-emerald-50 dark:bg-emerald-950/50 text-emerald-700 dark:text-emerald-400 mt-0.5">
                          <FileSpreadsheet className="w-4 h-4" />
                        </div>
                        <div>
                          <div className="font-bold text-[#111D4A] dark:text-white group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors">
                            {job.fileName}
                          </div>
                        </div>
                      </div>
                    </td>

                    {/* SOURCE FILES */}
                    <td className="py-3.5 px-4 min-w-56 max-w-72">
                      <div className="flex flex-wrap items-center gap-1.5">
                        {job.sourceFiles.slice(0, 2).map((sourceFile) => (
                          <button
                            key={sourceFile}
                            type="button"
                            title={`View source details for ${sourceFile}`}
                            onClick={(event) => {
                              event.stopPropagation();
                              onSelectSourceFileForAudit(job, sourceFile);
                            }}
                            className="max-w-40 truncate rounded-md border border-slate-200 bg-white px-2 py-1 text-left text-[11px] font-medium text-slate-600 hover:border-emerald-300 hover:bg-emerald-50 hover:text-emerald-800 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300 dark:hover:border-emerald-700 dark:hover:bg-emerald-950/40 dark:hover:text-emerald-300"
                          >
                            {sourceFile}
                          </button>
                        ))}
                        {job.sourceFiles.length > 2 && (
                          <button
                            type="button"
                            title="View all source files"
                            onClick={(event) => {
                              event.stopPropagation();
                              onSelectSourceFileForAudit(job, job.sourceFiles[2]);
                            }}
                            className="rounded-md px-1.5 py-1 text-[11px] font-semibold text-[#00796B] hover:bg-emerald-50 dark:text-teal-300 dark:hover:bg-emerald-950/40"
                          >
                            +{job.sourceFiles.length - 2} more
                          </button>
                        )}
                        {job.sourceFiles.length === 0 && <span className="text-slate-400">No source files</span>}
                      </div>
                    </td>

                    {/* DATE */}
                    <td className="py-3.5 px-6 font-mono text-slate-600 dark:text-slate-300">
                      <div>{job.date}</div>
                      <div className="text-[11px] text-slate-400">{job.timeUTC}</div>
                    </td>

                    {/* FILE SIZE */}
                    <td className="py-3.5 px-6 font-mono text-slate-700 dark:text-slate-300 font-medium">
                      {job.fileSize}
                    </td>

                    {/* FILE TYPE */}
                    <td className="py-3.5 px-6">
                      <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-medium bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-mono">
                        {job.fileType}
                      </span>
                    </td>

                    {/* DOWNLOAD */}
                    <td className="py-3.5 px-6 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={(e) => handleDownload(job, e)}
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-slate-700 dark:text-slate-200 hover:text-indigo-600 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 rounded-md transition-colors"
                        >
                          <Download className="w-3.5 h-3.5" />
                          <span>Download</span>
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Bar (Matching Page 4 exact format) */}
        <div className="p-4 border-t border-slate-100 dark:border-slate-800 flex flex-col md:flex-row items-center justify-between gap-4 text-xs text-slate-500 dark:text-slate-400">
          <div className="flex items-center gap-2">
            <span>
              Showing <span className="font-semibold text-slate-700 dark:text-slate-300">{filteredJobs.length === 0 ? 0 : startIndex + 1}-{Math.min(startIndex + rowsPerPage, filteredJobs.length)}</span> of{' '}
              <span className="font-semibold text-slate-700 dark:text-slate-300">{filteredJobs.length}</span> consolidated runs
            </span>
            <span className="text-slate-300 dark:text-slate-600">•</span>
            <div className="flex items-center gap-1">
              <span>Rows per page:</span>
              <select
                value={rowsPerPage}
                onChange={(e) => setRowsPerPage(Number(e.target.value))}
                className="px-2 py-0.5 rounded border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 font-mono font-medium text-slate-800 dark:text-slate-200 focus:outline-hidden"
              >
                <option value={10}>10</option>
                <option value={25}>25</option>
                <option value={50}>50</option>
              </select>
            </div>
          </div>

          <div className="flex items-center gap-1">
            <span className="font-mono mr-2">Page {safeCurrentPage} of {totalPages}</span>
            <button
              onClick={() => setCurrentPage(1)}
              className="p-1 rounded text-slate-400 hover:text-slate-700 dark:hover:text-slate-200"
              disabled={safeCurrentPage === 1}
            >
              <ChevronsLeft className="w-4 h-4" />
            </button>
            <button
              onClick={() => setCurrentPage((page) => Math.max(1, page - 1))}
              className="p-1 rounded text-slate-400 hover:text-slate-700 dark:hover:text-slate-200"
              disabled={safeCurrentPage === 1}
            >
              <ChevronLeft className="w-4 h-4" />
            </button>

            {Array.from({ length: Math.min(3, totalPages) }, (_, index) => {
              const pageNumber = index + 1;
              return (
                <button
                  key={pageNumber}
                  onClick={() => setCurrentPage(pageNumber)}
                  className={`w-6 h-6 rounded font-mono font-bold text-xs ${safeCurrentPage === pageNumber ? 'bg-[#0B1528] text-white' : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'}`}
                >
                  {pageNumber}
                </button>
              );
            })}

            {totalPages > 3 && <span className="px-1 text-slate-400">...</span>}
            {totalPages > 3 && (
              <button
                onClick={() => setCurrentPage(totalPages)}
                className="px-1.5 h-6 rounded text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 font-mono text-xs"
              >
                {totalPages}
              </button>
            )}

            <button
              onClick={() => setCurrentPage((page) => Math.min(totalPages, page + 1))}
              className="p-1 rounded text-slate-400 hover:text-slate-700 dark:hover:text-slate-200"
              disabled={safeCurrentPage === totalPages}
            >
              <ChevronRight className="w-4 h-4" />
            </button>
            <button
              onClick={() => setCurrentPage(totalPages)}
              className="p-1 rounded text-slate-400 hover:text-slate-700 dark:hover:text-slate-200"
              disabled={safeCurrentPage === totalPages}
            >
              <ChevronsRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
