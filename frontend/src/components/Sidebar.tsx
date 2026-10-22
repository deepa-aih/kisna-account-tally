import React from 'react';
import { ActiveTab } from '../types';
import { LayoutGrid, Sparkles, History, Table2, X } from 'lucide-react';

interface SidebarProps {
  activeTab: ActiveTab;
  setActiveTab: (tab: ActiveTab) => void;
  isOpenMobile: boolean;
  setIsOpenMobile: (open: boolean) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  setActiveTab,
  isOpenMobile,
  setIsOpenMobile,
}) => {
  const menuItems = [
    {
      id: 'dashboard' as ActiveTab,
      label: 'Dashboard',
      icon: LayoutGrid,
    },
    {
      id: 'new-merge' as ActiveTab,
      label: 'New Merge',
      icon: Sparkles,
    },
    {
      id: 'history' as ActiveTab,
      label: 'History',
      icon: History,
    },
    // {
    //   id: 'viewer' as ActiveTab,
    //   label: 'File Viewer',
    //   icon: Table2,
    // },
    // {
    //   id: 'cost-analysis' as ActiveTab,
    //   label: 'Cost Analysis',
    //   icon: TrendingUp,
    // },
  ];

  const handleSelect = (tab: ActiveTab) => {
    setActiveTab(tab);
    setIsOpenMobile(false);
  };

  return (
    <>
      {/* Mobile Backdrop */}
      {isOpenMobile && (
        <div
          className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs z-40 lg:hidden"
          onClick={() => setIsOpenMobile(false)}
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={`fixed top-0 bottom-0 left-0 z-50 w-64 bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 flex flex-col transition-transform duration-200 ease-in-out lg:translate-x-0 ${
          isOpenMobile ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Brand Header */}
        <div className="h-16 flex items-center justify-between px-6 border-b border-slate-100 dark:border-slate-800">
          <div className="flex items-center gap-2.5">
            <div className="relative flex h-9 w-9 items-center justify-center overflow-hidden rounded-xl bg-gradient-to-br from-[#202B63] to-[#111936] text-white shadow-sm ring-1 ring-[#151E49]/15 dark:ring-white/10">
              <span aria-hidden="true" className="absolute -right-1 -top-1 h-4 w-4 rounded-full bg-[#20E4D0]/20 blur-[2px]" />
              <span className="relative font-sans text-[13px] font-extrabold tracking-[-0.08em]">
                <span className="text-[#20E4D0]">A</span>T
              </span>
            </div>
            <div className="flex items-baseline gap-1.5">
              <span className="text-[17px] font-bold tracking-[-0.04em] text-[#151E49] dark:text-white">
                Accounts
              </span>
              <span className="text-[17px] font-semibold tracking-[-0.04em] text-[#128F87] dark:text-[#20E4D0]">
                Tally
              </span>
            </div>
          </div>

          <button
            onClick={() => setIsOpenMobile(false)}
            className="lg:hidden p-1.5 text-slate-400 hover:text-slate-600 rounded-md hover:bg-slate-100 dark:hover:bg-slate-800"
            aria-label="Close navigation"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Section Navigation */}
        <div className="flex-1 py-6 px-3 space-y-6 overflow-y-auto">
          <div>
            <div className="px-3 mb-3 text-[11px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider">
              CONSOLIDATION WORKFLOWS
            </div>
            <nav className="space-y-1">
              {menuItems.map((item) => {
                const Icon = item.icon;
                const isActive = activeTab === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => handleSelect(item.id)}
                    className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition-all text-left ${
                      isActive
                        ? 'bg-[#151E49] text-white shadow-xs'
                        : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100/80 dark:hover:bg-slate-800/60'
                    }`}
                  >
                    <Icon className="w-5 h-5 shrink-0 text-[#20E4D0]" />
                    <span>{item.label}</span>
                  </button>
                );
              })}
            </nav>
          </div>
        </div>

      </aside>
    </>
  );
};
