import React, { useState } from 'react';
import { RecentFile, ActiveTab, HistoryJob, DashboardKpis, JobMetrics } from '../types';
import {
  Layers,
  FileSpreadsheet,
  Clock,
  ShieldCheck,
  Search,
  Download,
  Loader2,
  ChevronRight,
  Plus,
  Filter,
  ArrowUp,
  ArrowDown,
  Zap,
  TrendingUp,
} from 'lucide-react';
import { downloadJobWorkbook } from '../lib/api';

interface DashboardSummary {
  totalJobs: number;
  successfulJobs: number;
  flaggedJobs: number;
  recordsProcessed: number;
  recentFiles: Array<Record<string, unknown>>;
  kpis?: DashboardKpis | null;
}

interface DashboardViewProps {
  recentFiles: RecentFile[];
  jobs: HistoryJob[];
  dashboardSummary: DashboardSummary;
  setActiveTab: (tab: ActiveTab) => void;
  onSelectFileToView: (fileName: string) => void;
  onShowToast: (message: string) => void;
}

const MANUAL_RUN_SECONDS = 18 * 60;
const BENCHMARK_RUN_SECONDS = 42;
const LABOR_RATE_PER_HOUR = 37;

const parseCount = (value: unknown) => Number(String(value ?? '0').replace(/[^\d]/g, '')) || 0;

const percentChange = (current: number, previous: number) => {
  if (previous <= 0) return 0;
  return ((current - previous) / previous) * 100;
};

const jobInstant = (job: HistoryJob) => {
  const parsed = new Date(`${job.date || ''}T${job.timeUTC || '00:00:00'}Z`);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
};

const fileCounts = (names: string[], metrics?: JobMetrics) => {
  if (metrics && (metrics.xlsxCount || metrics.xlsCount || metrics.fileCount)) {
    return {
      files: metrics.fileCount || (metrics.xlsxCount || 0) + (metrics.xlsCount || 0),
      xlsx: metrics.xlsxCount || 0,
      xls: metrics.xlsCount || 0,
    };
  }
  const xlsx = names.filter((name) => name.toLowerCase().endsWith('.xlsx')).length;
  const xls = names.filter((name) => name.toLowerCase().endsWith('.xls') && !name.toLowerCase().endsWith('.xlsx')).length;
  return { files: names.length || xlsx + xls, xlsx, xls };
};

const buildKpis = (jobs: HistoryJob[], summary: DashboardSummary): DashboardKpis => {
  const now = Date.now();
  const weekMs = 7 * 24 * 60 * 60 * 1000;
  const inWindow = (job: HistoryJob, start: number, end: number) => {
    const instant = jobInstant(job);
    if (!instant) return false;
    const time = instant.getTime();
    return time >= start && time < end;
  };
  const thisWeekJobs = jobs.filter((job) => inWindow(job, now - weekMs, now + 1000));
  const lastWeekJobs = jobs.filter((job) => inWindow(job, now - weekMs * 2, now - weekMs));

  const totalsFor = (list: HistoryJob[]) => {
    return list.reduce(
      (acc, job) => {
        const counts = fileCounts(job.sourceFiles || [], job.metrics);
        acc.files += counts.files;
        acc.xlsx += counts.xlsx;
        acc.xls += counts.xls;
        acc.sheets += job.metrics?.sheetCount || 0;
        acc.records += job.metrics?.recordCount || parseCount(job.recordsCount);
        acc.duplicates += job.metrics?.duplicateRows || 0;
        acc.patched += job.metrics?.patchedRows || 0;
        acc.knownDuration += job.metrics?.durationSeconds ? 1 : 0;
        acc.durationSum += job.metrics?.durationSeconds || 0;
        (job.metrics?.regions || []).forEach((region) => acc.regions.add(region));
        if (!job.metrics?.regions?.length && job.metrics?.regionCount) {
          acc.regionFallback += job.metrics.regionCount;
        }
        return acc;
      },
      {
        files: 0,
        xlsx: 0,
        xls: 0,
        sheets: 0,
        records: 0,
        duplicates: 0,
        patched: 0,
        knownDuration: 0,
        durationSum: 0,
        regions: new Set<string>(),
        regionFallback: 0,
      }
    );
  };

  const all = totalsFor(jobs);
  const current = totalsFor(thisWeekJobs);
  const previous = totalsFor(lastWeekJobs);
  const totalMerges = summary.totalJobs || jobs.length;
  const avgRunSeconds = all.knownDuration > 0 ? all.durationSum / all.knownDuration : BENCHMARK_RUN_SECONDS;
  const savedSeconds = Math.max(0, totalMerges * (MANUAL_RUN_SECONDS - avgRunSeconds));
  const previousSaved = Math.max(0, lastWeekJobs.length * (MANUAL_RUN_SECONDS - avgRunSeconds));
  const currentSaved = Math.max(0, thisWeekJobs.length * (MANUAL_RUN_SECONDS - avgRunSeconds));
  const successRate = totalMerges > 0 ? (summary.successfulJobs / totalMerges) * 100 : 0;
  const dupePct = all.records > 0 ? (all.duplicates / all.records) * 100 : 0;
  const patchedPct = all.records > 0 ? (all.patched / all.records) * 100 : 0;
  const rowQuality = all.records > 0 ? ((all.records - all.duplicates) / all.records) * 100 : successRate;
  const qualityScore = all.records > 0 ? rowQuality * 0.7 + successRate * 0.3 : successRate;
  const previousSuccess = lastWeekJobs.length
    ? (lastWeekJobs.filter((job) => job.status === 'OK').length / lastWeekJobs.length) * 100
    : 0;
  const currentSuccess = thisWeekJobs.length
    ? (thisWeekJobs.filter((job) => job.status === 'OK').length / thisWeekJobs.length) * 100
    : 0;
  const sparkline = Array.from({ length: 7 }, (_, index) => {
    const dayStart = new Date();
    dayStart.setHours(0, 0, 0, 0);
    dayStart.setDate(dayStart.getDate() - (6 - index));
    const dayEnd = new Date(dayStart);
    dayEnd.setDate(dayEnd.getDate() + 1);
    return jobs.filter((job) => inWindow(job, dayStart.getTime(), dayEnd.getTime())).length;
  });

  return {
    totalMerges,
    mergeTrendPct: percentChange(thisWeekJobs.length, lastWeekJobs.length),
    jobsThisWeek: thisWeekJobs.length,
    sparkline,
    filesProcessed: all.files,
    filesTrendPct: percentChange(current.files, previous.files),
    avgSheetsPerFile: all.sheets > 0 && all.files > 0 ? all.sheets / all.files : null,
    xlsxCount: all.xlsx,
    xlsCount: all.xls,
    regionCount: all.regions.size || all.regionFallback,
    hoursSaved: savedSeconds / 3600,
    timeTrendPct: percentChange(currentSaved, previousSaved),
    laborSaved: Math.round((savedSeconds / 3600) * LABOR_RATE_PER_HOUR),
    avgRunSeconds,
    qualityScore,
    qualityTrendPct: percentChange(currentSuccess, previousSuccess),
    dupePct,
    patchedPct,
    deterministicValid: totalMerges > 0 && summary.flaggedJobs === 0 && dupePct < 1,
  };
};

const TrendBadge = ({ value, icon }: { value: number; icon?: 'arrow' | 'zap' | 'trend' }) => {
  const positive = value >= 0;
  const color = positive ? 'text-emerald-600' : 'text-rose-600';
  const Icon = !positive ? ArrowDown : icon === 'zap' ? Zap : icon === 'trend' ? TrendingUp : ArrowUp;
  return (
    <span className={`inline-flex items-center gap-0.5 text-xs font-semibold ${color}`}>
      <Icon className="w-3 h-3" />
      {positive ? '+' : ''}
      {value.toFixed(1)}%
    </span>
  );
};

const sparklineGeometry = (values: number[]) => {
  const max = Math.max(...values, 1);
  const points = values.map((value, index) => {
    const x = values.length === 1 ? 100 : (index / (values.length - 1)) * 100;
    const y = 22 - (value / max) * 14;
    return { x, y };
  });
  const path = points.map((point, index) => `${index === 0 ? 'M' : 'L'} ${point.x.toFixed(1)} ${point.y.toFixed(1)}`).join(' ');
  return { path, end: points[points.length - 1] || { x: 100, y: 18 } };
};

export const DashboardView: React.FC<DashboardViewProps> = ({
  recentFiles,
  jobs,
  dashboardSummary,
  setActiveTab,
  onSelectFileToView,
  onShowToast,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<'ALL' | 'COMPLETED' | 'PROCESSING'>('ALL');
  const [filterOpen, setFilterOpen] = useState(false);
  const [page, setPage] = useState(1);
  const [downloadingFileId, setDownloadingFileId] = useState<string | null>(null);

  const kpis = dashboardSummary.kpis ?? buildKpis(jobs, dashboardSummary);
  const spark = sparklineGeometry(kpis.sparkline.length ? kpis.sparkline : [0, 0, 0, 0, 0, 0, 0]);
  const hoursSavedLabel = kpis.hoursSaved.toFixed(1);

  const filteredFiles = recentFiles.filter((file) => {
    const matchesSearch = file.name.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'ALL' || file.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const handleDownload = async (file: RecentFile, e: React.MouseEvent) => {
    e.stopPropagation();
    const job = jobs.find((item) => item.id === file.id);
    if (!job) {
      onShowToast(`Unable to find the generated workbook for ${file.name}. Refresh the dashboard and try again.`);
      return;
    }

    setDownloadingFileId(file.id);
    try {
      const workbook = await downloadJobWorkbook(job.id);
      const url = URL.createObjectURL(workbook);
      const link = document.createElement('a');
      link.href = url;
      link.download = job.fileName.toLowerCase().endsWith('.xlsx')
        ? job.fileName
        : `${job.fileName}.xlsx`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      // The browser may still be reading the blob after click() returns. Revoking
      // the URL synchronously can leave the downloaded workbook empty.
      window.setTimeout(() => URL.revokeObjectURL(url), 1000);
      onShowToast(`Downloaded ${job.fileName}`);
    } catch (error) {
      const message = error instanceof Error ? error.message : `Unable to download ${file.name}.`;
      onShowToast(message);
    } finally {
      setDownloadingFileId(null);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="text-sm font-normal text-slate-500 dark:text-slate-400 leading-tight">
            Welcome back, Priya
          </div>
          <h1 className="text-3xl font-bold text-slate-900 dark:text-white tracking-tight">
            Dashboard
          </h1>
        </div>

        <button
          onClick={() => setActiveTab('new-merge')}
          className="inline-flex items-center justify-center gap-2 self-start sm:self-auto px-5 py-3 bg-[#151E49] text-white hover:bg-[#10183a] dark:bg-slate-100 dark:text-slate-900 dark:hover:bg-white text-sm font-semibold rounded-xl shadow-xs transition-all hover:shadow"
        >
          <Plus className="w-4 h-4 text-[#20E4D0]" strokeWidth={2.5} />
          <span>New Merge</span>
        </button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 rounded-xl p-4 shadow-xs min-h-[180px]">
          <div>
            <div className="flex items-start justify-between gap-2">
              <span className="text-[11px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider leading-4">
                Total merges<br />completed
              </span>
              <div className="w-8 h-8 rounded-lg bg-slate-50 dark:bg-slate-800 text-slate-400 flex items-center justify-center shrink-0">
                <Layers className="w-4 h-4" />
              </div>
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-4xl font-extrabold text-slate-900 dark:text-white tracking-tight">
                {kpis.totalMerges.toLocaleString()}
              </span>
              <TrendBadge value={kpis.mergeTrendPct} />
            </div>
            <div className="relative mt-4 h-10">
              <svg className="absolute inset-0 w-full h-full" viewBox="0 0 100 28" fill="none" preserveAspectRatio="none">
                <path d={spark.path} stroke="#CBD5E1" strokeWidth="1.6" strokeLinecap="round" vectorEffect="non-scaling-stroke" />
                <circle cx={spark.end.x} cy={spark.end.y} r="2.2" fill="#111D4A" />
              </svg>
              <div className="absolute left-0 top-1/2 -translate-y-1/2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm rounded-md px-2 py-1 text-[11px] text-slate-500">
                <span className="font-semibold text-slate-800 dark:text-slate-100">{kpis.jobsThisWeek.toLocaleString()}</span>{' '}
                {kpis.jobsThisWeek === 1 ? 'job' : 'jobs'} this week
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 rounded-xl p-4 shadow-xs min-h-[180px]">
          <div>
            <div className="flex items-start justify-between gap-2">
              <span className="text-[11px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider leading-4">
                Files processed &amp;<br />ingested
              </span>
              <div className="w-8 h-8 rounded-lg bg-slate-50 dark:bg-slate-800 text-slate-400 flex items-center justify-center shrink-0">
                <FileSpreadsheet className="w-4 h-4" />
              </div>
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-4xl font-extrabold text-slate-900 dark:text-white tracking-tight">
                {kpis.filesProcessed.toLocaleString()}
              </span>
              <TrendBadge value={kpis.filesTrendPct} />
            </div>
            <div className="mt-4 flex items-end justify-between gap-3">
              <div>
                <div className="text-sm font-semibold text-slate-800 dark:text-slate-100">
                  Avg {kpis.avgSheetsPerFile == null ? '—' : kpis.avgSheetsPerFile.toFixed(1)}
                </div>
                <div className="text-[11px] text-slate-400">sheets/file</div>
              </div>
              <div className="text-right text-[11px] text-slate-500 leading-5">
                <div><span className="font-semibold text-slate-700 dark:text-slate-200">{kpis.xlsxCount.toLocaleString()}</span> .xlsx</div>
                <div><span className="font-semibold text-slate-700 dark:text-slate-200">{kpis.xlsCount.toLocaleString()}</span> .xls</div>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 rounded-xl p-4 shadow-xs min-h-[180px]">
          <div>
            <div className="flex items-start justify-between gap-2">
              <span className="text-[11px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider leading-4">
                Operational time<br />saved
              </span>
              <div className="w-8 h-8 rounded-lg bg-slate-50 dark:bg-slate-800 text-slate-400 flex items-center justify-center shrink-0">
                <Clock className="w-4 h-4" />
              </div>
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-4xl font-extrabold text-slate-900 dark:text-white tracking-tight">
                {hoursSavedLabel}
              </span>
              <TrendBadge value={kpis.timeTrendPct} icon="zap" />
            </div>
            <div className="text-sm text-slate-500 dark:text-slate-400">hrs</div>
            <div className="mt-3 flex items-center justify-between gap-2">
              <span className="inline-flex items-center bg-emerald-50 dark:bg-emerald-950/50 text-emerald-700 dark:text-emerald-300 text-[11px] font-semibold px-2 py-1 rounded-md">
                ${kpis.laborSaved.toLocaleString()} labor saved
              </span>
              <span className="text-[11px] text-slate-500">{Math.round(kpis.avgRunSeconds)}s avg/run</span>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 rounded-xl p-4 shadow-xs min-h-[180px]">
          <div>
            <div className="flex items-start justify-between gap-2">
              <span className="text-[11px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider leading-4">
                Aggregate quality<br />score
              </span>
              <div className="w-8 h-8 rounded-lg bg-slate-50 dark:bg-slate-800 text-slate-400 flex items-center justify-center shrink-0">
                <ShieldCheck className="w-4 h-4" />
              </div>
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-4xl font-extrabold text-slate-900 dark:text-white tracking-tight">
                {kpis.qualityScore.toFixed(1)}%
              </span>
              <TrendBadge value={kpis.qualityTrendPct} icon="trend" />
            </div>
            <div className="mt-4 flex items-center justify-between gap-2 text-[11px]">
              <span className="inline-flex items-center gap-1.5 min-w-0">
                <span className={`w-2 h-2 rounded-full shrink-0 ${kpis.deterministicValid ? 'bg-emerald-400' : 'bg-amber-400'}`} />
                <span className="text-slate-500">Deterministic</span>
                <span className="font-semibold text-slate-800 dark:text-slate-100">{kpis.deterministicValid ? 'Valid' : 'Review'}</span>
              </span>
              <span className="text-slate-400 text-right">
                {kpis.dupePct.toFixed(1)}% dupes · {kpis.patchedPct.toFixed(1)}% patched
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content: Recent Files Table Container */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 rounded-xl shadow-xs overflow-hidden">
        {/* Table Top Header Bar */}
        <div className="p-4 sm:p-5 border-b border-slate-100 dark:border-slate-800 flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-lg bg-[#111D4A] flex items-center justify-center shrink-0">
              <svg viewBox="0 0 24 24" className="w-5 h-5" fill="none" aria-hidden="true">
                <rect x="3.5" y="4" width="17" height="16" rx="2" stroke="#45F0DF" strokeWidth="1.7" />
                <path d="M3.5 9.2h17" stroke="#45F0DF" strokeWidth="1.7" />
                <path d="M9.2 9.2V20.8M14.8 9.2V20.8" stroke="#45F0DF" strokeWidth="1.7" />
              </svg>
            </div>
            <h2 className="text-base font-bold text-slate-900 dark:text-white">
              Recent Files
            </h2>
          </div>

          {/* Search & Filter Toolbar */}
          <div className="flex items-center gap-2">
            <div className="relative flex-1 sm:w-72">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search file or job name..."
                className="w-full pl-9 pr-3 py-1.5 text-xs bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white placeholder-slate-400 focus:outline-hidden focus:ring-1 focus:ring-indigo-500"
              />
              {searchTerm && (
                <button
                  onClick={() => setSearchTerm('')}
                  className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 text-xs"
                >
                  ×
                </button>
              )}
            </div>

            <div className="relative">
              <button
                type="button"
                onClick={() => setFilterOpen((open) => !open)}
                className="w-9 h-9 inline-flex items-center justify-center rounded-lg bg-[#F2F4FC] text-[#9390BF] hover:bg-[#E9ECF7] dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700 transition-colors"
                aria-label="Filter files by status"
                aria-expanded={filterOpen}
              >
                <Filter className="w-4 h-4" />
              </button>
              {filterOpen && (
                <div className="absolute right-0 mt-2 w-36 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg shadow-lg py-1 z-20 text-xs">
                  {([
                    ['ALL', 'All'],
                    ['COMPLETED', 'Completed'],
                    ['PROCESSING', 'Processing'],
                  ] as const).map(([value, label]) => (
                    <button
                      key={value}
                      type="button"
                      onClick={() => {
                        setStatusFilter(value);
                        setFilterOpen(false);
                      }}
                      className={`w-full text-left px-3 py-1.5 hover:bg-slate-50 dark:hover:bg-slate-700/60 ${
                        statusFilter === value
                          ? 'text-[#111D4A] dark:text-white font-semibold'
                          : 'text-slate-600 dark:text-slate-300'
                      }`}
                    >
                      {label}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Table Viewport */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#F1F1FC] dark:bg-slate-800/50 text-[11px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider border-b border-slate-100 dark:border-slate-800">
              <tr>
                <th className="py-3 px-6">FILE / BATCH NAME</th>
                <th className="py-3 px-6 text-right font-mono">TOTAL ROWS</th>
                <th className="py-3 px-6">PROCESSING DATE</th>
                <th className="py-3 px-6">STATUS</th>
                <th className="py-3 px-6 text-right">ACTIONS</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {filteredFiles.length === 0 ? (
                <tr>
                  <td colSpan={5} className="py-8 text-center text-slate-400 dark:text-slate-500">
                    No files found matching criteria.
                  </td>
                </tr>
              ) : (
                filteredFiles.map((file) => (
                  <tr
                    key={file.id}
                    onClick={() => {
                      onSelectFileToView(file.name);
                      setActiveTab('viewer');
                    }}
                    className="hover:bg-slate-50/80 dark:hover:bg-slate-800/40 transition-colors cursor-pointer group"
                  >
                    <td className="py-3.5 px-6">
                      <div className="flex items-center gap-3">
                        <div className="p-1.5 rounded-md bg-emerald-50 dark:bg-emerald-950/50 text-emerald-700 dark:text-emerald-400">
                          <FileSpreadsheet className="w-4 h-4" />
                        </div>
                        <div>
                          <div className="font-semibold text-slate-900 dark:text-white group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors">
                            {file.name}
                          </div>
                          <div className="text-[11px] text-slate-400 dark:text-slate-500">
                            {file.fileSize} • Batch SHA-verified
                          </div>
                        </div>
                      </div>
                    </td>

                    <td className="py-3.5 px-6 text-right font-mono text-slate-700 dark:text-slate-300 font-semibold tabular-nums">
                      {file.totalRows.toLocaleString()}
                    </td>

                    <td className="py-3.5 px-6 text-slate-500 dark:text-slate-400 font-mono text-[11px]">
                      <span>{file.processingDate}</span>
                      <span className="mx-1.5 text-slate-300 dark:text-slate-600">•</span>
                      <span>{file.durationSeconds.toFixed(1)}s</span>
                    </td>

                    <td className="py-3.5 px-6">
                      {file.status === 'COMPLETED' ? (
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-400 border border-emerald-200/60 dark:border-emerald-800/60">
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                          COMPLETED
                        </span>
                      ) : file.status === 'FLAGGED' ? (
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-amber-50 text-amber-700 dark:bg-amber-950/60 dark:text-amber-400 border border-amber-200/60 dark:border-amber-800/60">
                          <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
                          REVIEW
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-amber-50 text-amber-700 dark:bg-amber-950/60 dark:text-amber-400 border border-amber-200/60 dark:border-amber-800/60">
                          <Loader2 className="w-3 h-3 animate-spin text-amber-500" />
                          PROCESSING
                        </span>
                      )}
                    </td>

                    <td className="py-3.5 px-6 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={(e) => handleDownload(file, e)}
                          disabled={downloadingFileId === file.id}
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-700 dark:text-slate-200 hover:text-indigo-600 dark:hover:text-indigo-400 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 rounded-md transition-colors"
                          title="Download workbook"
                        >
                          {downloadingFileId === file.id
                            ? <Loader2 className="w-3.5 h-3.5 animate-spin" />
                            : <Download className="w-3.5 h-3.5" />}
                          <span>{downloadingFileId === file.id ? 'Preparing…' : 'Download'}</span>
                        </button>

                        <button
                          onClick={() => {
                            onSelectFileToView(file.name);
                            setActiveTab('viewer');
                          }}
                          className="p-1.5 text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 rounded-md"
                          title="Inspect spreadsheet grid"
                        >
                          <ChevronRight className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Table Footer with Pagination */}
        <div className="p-4 border-t border-slate-100 dark:border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-slate-500 dark:text-slate-400">
          <div>
            Showing{' '}
            <span className="font-semibold text-slate-700 dark:text-slate-300">{filteredFiles.length}</span> of{' '}
            <span className="font-semibold text-slate-700 dark:text-slate-300">{recentFiles.length}</span> consolidated batch files
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => {
                if (page > 1) setPage(page - 1);
                onShowToast(`Navigated to page ${Math.max(1, page - 1)}`);
              }}
              className="px-3.5 py-2 bg-[#F2F4FC] hover:bg-[#E9ECF7] dark:bg-slate-800 dark:hover:bg-slate-700 text-[#9EA3B9] dark:text-slate-300 rounded-lg font-medium transition-colors"
            >
              Previous
            </button>
            <button
              onClick={() => {
                setPage(page + 1);
                onShowToast(`Navigated to page ${page + 1}`);
              }}
              className="px-3.5 py-2 bg-[#F2F4FC] hover:bg-[#E9ECF7] dark:bg-slate-800 dark:hover:bg-slate-700 text-[#9EA3B9] dark:text-slate-300 rounded-lg font-medium transition-colors"
            >
              Next
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
