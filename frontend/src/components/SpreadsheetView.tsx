import React, { useState } from 'react';
import { ChevronLeft, ChevronRight, FileSpreadsheet } from 'lucide-react';

interface SpreadsheetViewProps {
  rows?: Array<Record<string, unknown>>;
  sheets?: Record<string, Array<Record<string, unknown>>>;
}

const getColumnLabel = (index: number) => {
  let label = '';
  let value = index + 1;

  while (value > 0) {
    value -= 1;
    label = String.fromCharCode(65 + (value % 26)) + label;
    value = Math.floor(value / 26);
  }

  return label;
};

const formatCellValue = (value: unknown) => {
  if (value === null || value === undefined || value === '') {
    return '';
  }

  if (typeof value === 'number' && Number.isFinite(value)) {
    return value.toLocaleString('en-US', { maximumFractionDigits: 4 });
  }

  return String(value);
};

export const SpreadsheetView: React.FC<SpreadsheetViewProps> = ({
  rows = [],
  sheets = {},
}) => {
  const [activeSheet, setActiveSheet] = useState('Final Merged');
  const sheetEntries = Object.keys(sheets).length > 0
    ? sheets
    : { 'Final Merged': rows };
  const hasFullWorkbookSheets = Object.keys(sheets).length > 0;
  const sheetNames = Object.keys(sheetEntries);
  const currentSheet = sheetNames.includes(activeSheet)
    ? activeSheet
    : sheetNames[0] || 'Final Merged';
  const currentRows = sheetEntries[currentSheet] || [];
  const columns = currentRows.length > 0 ? Object.keys(currentRows[0]) : [];
  const activeSheetIndex = sheetNames.indexOf(currentSheet);

  const moveSheet = (direction: -1 | 1) => {
    const nextIndex = activeSheetIndex + direction;
    if (nextIndex >= 0 && nextIndex < sheetNames.length) {
      setActiveSheet(sheetNames[nextIndex]);
    }
  };

  return (
    <div>
      <div className="bg-white dark:bg-slate-900 border-x border-b border-slate-200/90 dark:border-slate-800 rounded-b-xl shadow-xs overflow-hidden flex flex-col">
        <div className="max-h-[384px] overflow-auto">
          {currentRows.length === 0 ? (
            <div className="flex min-h-[240px] items-center justify-center px-6 text-sm text-slate-500 dark:text-slate-400">
              This worksheet has no data rows.
            </div>
          ) : (
            <table className="min-w-full w-max text-left border-collapse text-xs select-none">
              <thead className="sticky top-0 z-10">
                <tr className="bg-[#E3E8FF] dark:bg-slate-800/95 text-[10px] font-mono text-[#17234F] dark:text-slate-300 border-b border-slate-200 dark:border-slate-700">
                  <th className="sticky left-0 z-20 min-w-12 bg-[#E3E8FF] dark:bg-slate-800 py-1 px-3 text-center border-r border-[#CBD2F0] dark:border-slate-700">
                    #
                  </th>
                  {columns.map((_, index) => (
                    <th
                      key={index}
                      className="min-w-24 py-1 px-3 text-center border-r border-[#CBD2F0] dark:border-slate-700 last:border-r-0"
                    >
                      {getColumnLabel(index)}
                    </th>
                  ))}
                </tr>
                <tr className="bg-[#111B4A] dark:bg-slate-950 text-[11px] font-bold text-white border-b border-[#111B4A] dark:border-slate-700">
                  <th className="sticky left-0 z-20 min-w-12 bg-[#111B4A] dark:bg-slate-950 py-2 px-3 text-center border-r border-white/15 dark:border-slate-700 text-slate-300">
                    #
                  </th>
                  {columns.map((column) => (
                    <th
                      key={column}
                      className="min-w-24 whitespace-nowrap py-2 px-3.5 border-r border-white/15 dark:border-slate-700 last:border-r-0"
                    >
                      {column}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800 font-mono">
                {currentRows.map((row, rowIndex) => (
                  <tr
                    key={rowIndex}
                    className="h-9 text-slate-800 dark:text-slate-200 transition-colors hover:bg-indigo-50/40 dark:hover:bg-slate-800/60"
                  >
                    <td className="sticky left-0 z-[1] min-w-12 bg-slate-50 dark:bg-slate-800 py-2 px-3 text-center border-r border-slate-200/80 dark:border-slate-700/80 text-[11px] text-slate-400">
                      {rowIndex + 1}
                    </td>
                    {columns.map((column) => {
                      const value = row[column];
                      const isNumeric = typeof value === 'number';

                      return (
                        <td
                          key={column}
                          className={`whitespace-nowrap py-2 px-3.5 border-r border-slate-200/80 dark:border-slate-700/80 last:border-r-0 ${
                            isNumeric ? 'text-right tabular-nums' : 'text-left'
                          }`}
                        >
                          {formatCellValue(value)}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        <div className="flex items-center justify-between gap-3 border-t border-slate-200 dark:border-slate-800 bg-slate-50/80 dark:bg-slate-900 px-4 py-3 text-xs">
          <div className="flex flex-col gap-1 text-slate-500 dark:text-slate-400">
            <span>
              {hasFullWorkbookSheets
                ? currentRows.length === 0
                  ? '0 rows'
                  : currentRows.length > 9
                    ? `${currentRows.length} rows · Scroll within the table to view all`
                    : `${currentRows.length} rows`
                : `Showing ${currentRows.length} preview rows only`}
            </span>
            {!hasFullWorkbookSheets && (
              <span className="text-[11px]">
                Reprocess this workbook with the updated backend to load its summary and monthly sheets.
              </span>
            )}
          </div>
          <span className="text-slate-500 dark:text-slate-400">{currentSheet}</span>
        </div>

        <div className="bg-slate-100 dark:bg-slate-800 border-t border-slate-200 dark:border-slate-700 px-3 py-1.5 flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-2 text-xs">
          <div className="flex items-center gap-1 overflow-x-auto py-1">
            <div className="flex items-center text-slate-400 mr-1 shrink-0">
              <button
                type="button"
                onClick={() => moveSheet(-1)}
                disabled={activeSheetIndex <= 0}
                className="p-1 rounded hover:text-slate-700 dark:hover:text-slate-200 disabled:opacity-40"
                aria-label="Previous worksheet"
              >
                <ChevronLeft className="w-3.5 h-3.5" />
              </button>
              <button
                type="button"
                onClick={() => moveSheet(1)}
                disabled={activeSheetIndex < 0 || activeSheetIndex >= sheetNames.length - 1}
                className="p-1 rounded hover:text-slate-700 dark:hover:text-slate-200 disabled:opacity-40"
                aria-label="Next worksheet"
              >
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>

            {sheetNames.map((sheetName, index) => (
              <button
                key={sheetName}
                type="button"
                onClick={() => setActiveSheet(sheetName)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-t-md font-mono text-xs whitespace-nowrap transition-colors ${
                  currentSheet === sheetName
                    ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-white font-bold shadow-xs border-t-2 border-emerald-500'
                    : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-200/60 dark:hover:bg-slate-700/60'
                }`}
              >
                {index === 0 && <FileSpreadsheet className="w-3.5 h-3.5 text-emerald-600" />}
                <span>{sheetName}</span>
              </button>
            ))}
          </div>

          <div className="flex items-center gap-2 text-[11px] text-slate-500 dark:text-slate-400 shrink-0 self-end sm:self-center">
            <span className="font-mono">Sheet {activeSheetIndex + 1} of {sheetNames.length}</span>
            <span className="text-slate-300 dark:text-slate-600">|</span>
            <span className="font-medium text-slate-700 dark:text-slate-300">Read-Only Preview Mode</span>
          </div>
        </div>
      </div>
    </div>
  );
};
