import React, { useState } from 'react';
import {
  TrendingUp,
  Clock,
  DollarSign,
  ShieldCheck,
  Calculator,
  Layers,
  ArrowRight,
  Download,
} from 'lucide-react';
import { downloadDatasetAsCsv } from '../utils/exportUtils';

interface CostAnalysisViewProps {
  onShowToast: (message: string) => void;
}

export const CostAnalysisView: React.FC<CostAnalysisViewProps> = ({ onShowToast }) => {
  const [analystsCount, setAnalystsCount] = useState(6);
  const [hourlyRate, setHourlyRate] = useState(48);
  const [workbooksPerMonth, setWorkbooksPerMonth] = useState(320);

  // Math models
  // Manual consolidation: ~18.2 minutes per workbook batch
  // Accounts Telly automated: ~0.7 minutes (42 seconds)
  // Time saved per workbook = 17.5 mins = 0.2917 hrs
  const hoursSavedPerMonth = (workbooksPerMonth * 17.5) / 60;
  const monthlyLaborSaved = hoursSavedPerMonth * hourlyRate;
  const annualLaborSaved = monthlyLaborSaved * 12;
  const annualHoursSaved = hoursSavedPerMonth * 12;

  const handleExportRoi = () => {
    downloadDatasetAsCsv(
      'Accounts_Telly_ROI_Cost_Model.csv',
      ['Metric', 'Benchmark_Value', 'Unit'],
      [
        ['MIS Analysts Count', analystsCount, 'analysts'],
        ['Blended Hourly Rate', hourlyRate, 'USD/hr'],
        ['Workbooks Consolidated/Mo', workbooksPerMonth, 'batches'],
        ['Hours Saved Per Month', hoursSavedPerMonth.toFixed(1), 'hrs'],
        ['Monthly Labor Saved', `$${monthlyLaborSaved.toLocaleString('en-US', { minimumFractionDigits: 2 })}`, 'USD'],
        ['Annual Labor Saved', `$${annualLaborSaved.toLocaleString('en-US', { minimumFractionDigits: 2 })}`, 'USD'],
      ]
    );
    onShowToast('Exported Cost Analysis ROI projection');
  };

  return (
    <div className="space-y-6">
      {/* 4 Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Labor Saved */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 rounded-xl p-5 shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider">
                CURRENT MONTH LABOR SAVINGS
              </span>
              <div className="w-8 h-8 rounded-lg bg-emerald-50 dark:bg-emerald-950/60 text-emerald-600 flex items-center justify-center">
                <DollarSign className="w-4 h-4" />
              </div>
            </div>
            <div className="flex items-baseline gap-2 mb-2">
              <span className="text-3xl font-extrabold text-slate-900 dark:text-white font-mono">
                ${monthlyLaborSaved.toLocaleString('en-US', { maximumFractionDigits: 0 })}
              </span>
              <span className="text-xs font-semibold text-emerald-600 dark:text-emerald-400">
                +32.0%
              </span>
            </div>
          </div>
          <div className="pt-3 border-t border-slate-100 dark:border-slate-800 text-xs text-slate-400">
            Based on {workbooksPerMonth} batches processed
          </div>
        </div>

        {/* Hours Reclaimed */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 rounded-xl p-5 shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider">
                HOURS RECLAIMED / MONTH
              </span>
              <div className="w-8 h-8 rounded-lg bg-indigo-50 dark:bg-indigo-950/60 text-indigo-600 flex items-center justify-center">
                <Clock className="w-4 h-4" />
              </div>
            </div>
            <div className="flex items-baseline gap-2 mb-2">
              <span className="text-3xl font-extrabold text-slate-900 dark:text-white font-mono">
                {hoursSavedPerMonth.toFixed(1)}
              </span>
              <span className="text-sm font-semibold text-slate-500">hrs</span>
            </div>
          </div>
          <div className="pt-3 border-t border-slate-100 dark:border-slate-800 text-xs text-slate-400">
            18.2m manual vs 42s automated per file
          </div>
        </div>

        {/* Projected Annual Savings */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 rounded-xl p-5 shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider">
                PROJECTED ANNUAL RUN-RATE
              </span>
              <div className="w-8 h-8 rounded-lg bg-sky-50 dark:bg-sky-950/60 text-sky-600 flex items-center justify-center">
                <TrendingUp className="w-4 h-4" />
              </div>
            </div>
            <div className="flex items-baseline gap-2 mb-2">
              <span className="text-3xl font-extrabold text-slate-900 dark:text-white font-mono">
                ${annualLaborSaved.toLocaleString('en-US', { maximumFractionDigits: 0 })}
              </span>
            </div>
          </div>
          <div className="pt-3 border-t border-slate-100 dark:border-slate-800 text-xs text-slate-400">
            {annualHoursSaved.toFixed(0)} engineering/analyst hours
          </div>
        </div>

        {/* Error Liability Averted */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 rounded-xl p-5 shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider">
                FORMULA INTEGRITY RATE
              </span>
              <div className="w-8 h-8 rounded-lg bg-teal-50 dark:bg-teal-950/60 text-teal-600 flex items-center justify-center">
                <ShieldCheck className="w-4 h-4" />
              </div>
            </div>
            <div className="flex items-baseline gap-2 mb-2">
              <span className="text-3xl font-extrabold text-slate-900 dark:text-white font-mono">
                99.98%
              </span>
            </div>
          </div>
          <div className="pt-3 border-t border-slate-100 dark:border-slate-800 text-xs text-slate-400">
            0 #REF! / broken linkage in master rollups
          </div>
        </div>
      </div>

      {/* Main Grid: Interactive Calculator + Benchmark Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Interactive ROI Calculator */}
        <div className="lg:col-span-6 bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 rounded-xl p-6 shadow-xs space-y-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="p-2 bg-indigo-50 dark:bg-indigo-950/50 text-indigo-600 dark:text-indigo-400 rounded-lg">
                <Calculator className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-bold text-slate-900 dark:text-white">
                  Interactive ROI Scenario Model
                </h3>
                <p className="text-xs text-slate-500">
                  Tune team inputs to project consolidation economics
                </p>
              </div>
            </div>

            <button
              onClick={handleExportRoi}
              className="p-1.5 text-slate-500 hover:text-slate-900 dark:hover:text-white rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800"
              title="Export Model to CSV"
            >
              <Download className="w-4 h-4" />
            </button>
          </div>

          <div className="space-y-5 text-xs">
            {/* Slider 1: Analyst headcount */}
            <div>
              <div className="flex justify-between font-semibold text-slate-700 dark:text-slate-300 mb-2">
                <span>MIS Analysts in Department:</span>
                <span className="font-mono text-indigo-600 dark:text-indigo-400 font-bold">{analystsCount} Analysts</span>
              </div>
              <input
                type="range"
                min="1"
                max="25"
                value={analystsCount}
                onChange={(e) => setAnalystsCount(Number(e.target.value))}
                className="w-full accent-indigo-600"
              />
            </div>

            {/* Slider 2: Blended Hourly Rate */}
            <div>
              <div className="flex justify-between font-semibold text-slate-700 dark:text-slate-300 mb-2">
                <span>Blended Analyst Cost Rate:</span>
                <span className="font-mono text-indigo-600 dark:text-indigo-400 font-bold">${hourlyRate} / hr</span>
              </div>
              <input
                type="range"
                min="25"
                max="120"
                step="5"
                value={hourlyRate}
                onChange={(e) => setHourlyRate(Number(e.target.value))}
                className="w-full accent-indigo-600"
              />
            </div>

            {/* Slider 3: Workbooks per month */}
            <div>
              <div className="flex justify-between font-semibold text-slate-700 dark:text-slate-300 mb-2">
                <span>Monthly Consolidation Workbooks:</span>
                <span className="font-mono text-indigo-600 dark:text-indigo-400 font-bold">{workbooksPerMonth} workbooks</span>
              </div>
              <input
                type="range"
                min="50"
                max="1200"
                step="10"
                value={workbooksPerMonth}
                onChange={(e) => setWorkbooksPerMonth(Number(e.target.value))}
                className="w-full accent-indigo-600"
              />
            </div>

            {/* Result callout */}
            <div className="p-4 bg-slate-50 dark:bg-slate-800/60 rounded-xl border border-slate-200/80 dark:border-slate-700/80 space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-500">Monthly Hours Saved</span>
                <span className="font-mono font-bold text-slate-900 dark:text-white">
                  {hoursSavedPerMonth.toFixed(1)} hrs
                </span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-500">Monthly Net Capital Saved</span>
                <span className="font-mono font-bold text-emerald-600 dark:text-emerald-400">
                  ${monthlyLaborSaved.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                </span>
              </div>
              <div className="flex items-center justify-between text-xs pt-2 border-t border-slate-200/80 dark:border-slate-700">
                <span className="font-semibold text-slate-900 dark:text-white">5-Year Cumulative Value</span>
                <span className="font-mono font-extrabold text-indigo-600 dark:text-indigo-400 text-sm">
                  ${(annualLaborSaved * 5).toLocaleString('en-US', { maximumFractionDigits: 0 })}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Benchmark Comparisons */}
        <div className="lg:col-span-6 bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 rounded-xl p-6 shadow-xs space-y-5">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-emerald-50 dark:bg-emerald-950/50 text-emerald-600 dark:text-emerald-400 rounded-lg">
              <Layers className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900 dark:text-white">
                Process Velocity Comparison
              </h3>
              <p className="text-xs text-slate-500">
                Accounts Telly pipeline vs traditional Excel copy-paste & VLOOKUP
              </p>
            </div>
          </div>

          <div className="space-y-4 text-xs">
            {/* Step 1 */}
            <div className="p-3.5 bg-slate-50 dark:bg-slate-800/40 rounded-xl border border-slate-200/80 dark:border-slate-700/80">
              <div className="flex justify-between font-semibold text-slate-900 dark:text-white mb-1">
                <span>Multi-Workbook Header Alignment</span>
                <span className="text-emerald-600 font-mono">98% faster</span>
              </div>
              <div className="w-full bg-slate-200 dark:bg-slate-700 h-2 rounded-full overflow-hidden flex">
                <div className="bg-emerald-500 h-full w-[4%]" title="Accounts Telly (2 sec)" />
                <div className="bg-amber-500 h-full w-[96%]" title="Manual VLOOKUP (4.2 min)" />
              </div>
              <div className="flex justify-between text-[11px] text-slate-400 mt-1 font-mono">
                <span>Accounts Telly: 2.1s</span>
                <span>Manual Excel: 252s</span>
              </div>
            </div>

            {/* Step 2 */}
            <div className="p-3.5 bg-slate-50 dark:bg-slate-800/40 rounded-xl border border-slate-200/80 dark:border-slate-700/80">
              <div className="flex justify-between font-semibold text-slate-900 dark:text-white mb-1">
                <span>Multi-Currency Spot Valuation</span>
                <span className="text-emerald-600 font-mono">Automated Fixing</span>
              </div>
              <div className="w-full bg-slate-200 dark:bg-slate-700 h-2 rounded-full overflow-hidden flex">
                <div className="bg-emerald-500 h-full w-[2%]" />
                <div className="bg-amber-500 h-full w-[98%]" />
              </div>
              <div className="flex justify-between text-[11px] text-slate-400 mt-1 font-mono">
                <span>Accounts Telly: Real-Time</span>
                <span>Manual: Lookup tables & copy</span>
              </div>
            </div>

            {/* Step 3 */}
            <div className="p-3.5 bg-slate-50 dark:bg-slate-800/40 rounded-xl border border-slate-200/80 dark:border-slate-700/80">
              <div className="flex justify-between font-semibold text-slate-900 dark:text-white mb-1">
                <span>Chart-of-Accounts Range Audit</span>
                <span className="text-emerald-600 font-mono">0.0% Error Rate</span>
              </div>
              <div className="w-full bg-slate-200 dark:bg-slate-700 h-2 rounded-full overflow-hidden flex">
                <div className="bg-emerald-500 h-full w-[5%]" />
                <div className="bg-amber-500 h-full w-[95%]" />
              </div>
              <div className="flex justify-between text-[11px] text-slate-400 mt-1 font-mono">
                <span>Deterministic Invariant Audit</span>
                <span>Visual eye-balling / manual spot checks</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
