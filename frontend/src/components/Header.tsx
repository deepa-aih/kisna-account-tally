import React, { useState } from 'react';
import { ActiveTab } from '../types';
import {
  Sun,
  Moon,
  ArrowLeft,
  Menu,
  ChevronDown,
  ShieldCheck,
  Settings,
  LogOut,
} from 'lucide-react';
import type { AuthUser } from '../lib/api';
import { AdminUsersModal } from './AdminUsersModal';

interface HeaderProps {
  activeTab: ActiveTab;
  setActiveTab: (tab: ActiveTab) => void;
  isDark: boolean;
  setIsDark: (dark: boolean) => void;
  setIsOpenMobile: (open: boolean) => void;
  onDownloadConsolidated?: () => void;
  selectedFileName?: string;
  user: AuthUser;
  onSignOut: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  activeTab,
  setActiveTab,
  isDark,
  setIsDark,
  setIsOpenMobile,
  onDownloadConsolidated,
  selectedFileName = 'Q2_Global_OpEx_Consolidated.xlsx',
  user,
  onSignOut,
}) => {
  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const [isUserManagerOpen, setIsUserManagerOpen] = useState(false);
  const initials = user.name.split(/\s+/).map((part) => part[0]).slice(0, 2).join('').toUpperCase();

  return (
    <>
    <header className="sticky top-0 z-30 bg-white/95 dark:bg-slate-900/95 backdrop-blur-xs border-b border-slate-200/80 dark:border-slate-800 px-4 sm:px-8 py-3.5 flex items-center justify-between transition-colors">
      {/* Left zone: Title / Breadcrumbs */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => setIsOpenMobile(true)}
          className="lg:hidden p-2 text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg"
          aria-label="Open navigation menu"
        >
          <Menu className="w-5 h-5" />
        </button>

        {activeTab === 'cost-analysis' && (
          <div>
            <div className="text-xs font-normal text-slate-500 dark:text-slate-400 leading-tight">
              Analytics & Benchmarks
            </div>
            <h1 className="text-2xl font-bold text-slate-900 dark:text-white tracking-tight">
              Cost & ROI Analysis
            </h1>
          </div>
        )}
      </div>

      {/* Right zone: Actions & Profile */}
      <div className="flex items-center gap-3 sm:gap-4">
        {/* Dark/Light mode toggle */}
        <button
          onClick={() => setIsDark(!isDark)}
          className="p-2 text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-100 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          title={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
          aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
          aria-pressed={isDark}
        >
          {isDark ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4" />}
        </button>

        <span className="hidden sm:block w-px h-8 bg-slate-200 dark:bg-slate-700" aria-hidden="true" />

        {/* User Profile Pill */}
        <div className="relative">
          <button
            onClick={() => setIsProfileOpen(!isProfileOpen)}
            className="flex items-center gap-2.5 p-1 sm:pr-2.5 rounded-full sm:rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors text-left"
          >
            <div className="relative flex w-8 h-8 items-center justify-center rounded-full ring-1 ring-slate-200 dark:ring-slate-700 bg-indigo-700 text-xs font-semibold text-white shrink-0">
              {initials || 'U'}
            </div>
            <div className="hidden sm:block text-left">
              <div className="text-xs font-semibold text-slate-900 dark:text-white leading-tight">
                {user.name}
              </div>
              <div className="text-[10px] font-medium text-slate-400 dark:text-slate-400 tracking-wider">
                {user.role === 'admin' ? 'ADMINISTRATOR' : user.email}
              </div>
            </div>
            <ChevronDown className="w-3.5 h-3.5 text-slate-400 hidden sm:block" />
          </button>

          {/* Profile Dropdown */}
          {isProfileOpen && (
            <div className="absolute right-0 mt-2 w-56 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl shadow-lg py-1.5 z-50 text-xs">
              <div className="px-3.5 py-2 border-b border-slate-100 dark:border-slate-700">
                <div className="font-semibold text-slate-900 dark:text-white">{user.name}</div>
                <div className="text-slate-500 dark:text-slate-400 text-[11px]">{user.email}</div>
                <div className="mt-1 inline-flex items-center gap-1 text-[10px] text-emerald-600 dark:text-emerald-400 font-medium">
                  <ShieldCheck className="w-3 h-3" />
                  <span>{user.clientName} workspace · {user.role}</span>
                </div>
              </div>
              {user.role === 'admin' && (
                <button
                  onClick={() => {
                    setIsProfileOpen(false);
                    setIsUserManagerOpen(true);
                  }}
                  className="w-full text-left px-3.5 py-2 hover:bg-slate-50 dark:hover:bg-slate-700/60 flex items-center gap-2 text-slate-700 dark:text-slate-200"
                >
                  <Settings className="w-3.5 h-3.5 text-slate-400" />
                  <span>Manage users</span>
                </button>
              )}
              <div className="border-t border-slate-100 dark:border-slate-700 my-1" />
              <button
                onClick={() => {
                  setIsProfileOpen(false);
                  onSignOut();
                }}
                className="w-full text-left px-3.5 py-2 hover:bg-red-50 dark:hover:bg-red-950/30 flex items-center gap-2 text-red-600 dark:text-red-400"
              >
                <LogOut className="w-3.5 h-3.5" />
                <span>Sign out</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
    {isUserManagerOpen && <AdminUsersModal onClose={() => setIsUserManagerOpen(false)} />}
    {activeTab === 'viewer' && (
      <div className="bg-white/95 dark:bg-slate-900/95 border-b border-slate-200/80 dark:border-slate-800 px-4 sm:px-8 py-5 flex items-center justify-between gap-4 transition-colors">
        <div className="flex flex-col items-start gap-3 min-w-0">
          <button
            onClick={() => setActiveTab('new-merge')}
            className="inline-flex items-center gap-1 text-[18px] leading-5 font-normal text-[#626779] dark:text-slate-300 hover:text-[#111B4A] dark:hover:text-white transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back</span>
          </button>
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="w-[38px] h-[36px] bg-[#111B4A] text-[#20E4D0] rounded-[2px] flex items-center justify-center shrink-0">
              <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" className="w-[19px] h-[19px]" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                <path d="M5 4.5h14v15H5z" />
                <path d="M5 9h14M10 9v10M15 9v10M5 14h14" />
              </svg>
            </div>
            <span className="font-bold text-[#17234F] dark:text-white text-xl sm:text-2xl tracking-tight truncate">
              {selectedFileName}
            </span>
          </div>
        </div>
        <button
          onClick={onDownloadConsolidated}
          className="inline-flex items-center gap-1.5 px-3.5 h-11 bg-[#111B4A] text-white hover:bg-[#1B285D] text-[17px] font-semibold rounded-[2px] transition-colors shrink-0"
        >
          <svg aria-hidden="true" viewBox="0 0 20 20" fill="none" className="w-[18px] h-[18px]" stroke="#20E4D0" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
            <path d="M10 2.5v9m0 0 3.5-3.5M10 11.5 6.5 8M4 13v4h12v-4" />
          </svg>
          <span>Download .xlsx</span>
        </button>
      </div>
    )}
    </>
  );
};
