import React, { useState } from 'react';
import { X, Cloud, Search, Check, FileSpreadsheet, Folder } from 'lucide-react';

interface OneDriveModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectFiles: (files: { name: string; size: string }[]) => void;
  onShowToast: (message: string) => void;
}

export const OneDriveModal: React.FC<OneDriveModalProps> = ({
  isOpen,
  onClose,
  onSelectFiles,
  onShowToast,
}) => {
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [search, setSearch] = useState('');

  if (!isOpen) return null;

  const filtered: Array<{ id: string; name: string; size: string; modified: string; path: string }> = [];

  const toggleSelect = (id: string) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]
    );
  };

  const handleImport = () => {
    if (filtered.length === 0) {
      onShowToast('No SharePoint workbook files are connected. Please upload Excel files locally instead.');
      return;
    }

    const toImport = filtered
      .filter((f) => selectedIds.includes(f.id))
      .map((f) => ({ name: f.name, size: f.size }));

    if (toImport.length === 0) {
      onShowToast('Please select at least one workbook from SharePoint');
      return;
    }

    onSelectFiles(toImport);
    onShowToast(`Imported ${toImport.length} workbooks from Microsoft SharePoint`);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl max-w-xl w-full shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="p-5 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between bg-slate-50/50 dark:bg-slate-800/40">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-blue-100 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400">
              <Cloud className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                Import from Microsoft OneDrive / SharePoint
              </h3>
              <p className="text-xs text-slate-500">
                Connected to Accounts Telly Corporate Tenant
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 rounded-lg"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-5 space-y-4 text-xs">
          {/* Search */}
          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search SharePoint drives or files..."
              className="w-full pl-9 pr-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white placeholder-slate-400 focus:outline-hidden focus:ring-1 focus:ring-indigo-500"
            />
          </div>

          {/* File List */}
          <div className="space-y-2 max-h-60 overflow-y-auto">
            {filtered.length === 0 ? (
              <div className="p-4 rounded-xl border border-dashed border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/40 text-center text-sm text-slate-500 dark:text-slate-400">
                No workbook files are connected yet. Upload your Excel files directly from the local upload panel instead.
              </div>
            ) : (
              filtered.map((file) => {
                const isSelected = selectedIds.includes(file.id);
                return (
                  <div
                    key={file.id}
                    onClick={() => toggleSelect(file.id)}
                    className={`p-3 rounded-xl border flex items-center justify-between cursor-pointer transition-colors ${
                      isSelected
                        ? 'border-indigo-500 bg-indigo-50/60 dark:bg-indigo-950/40'
                        : 'border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-800/40 hover:bg-slate-50 dark:hover:bg-slate-800'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <div
                        className={`w-5 h-5 rounded flex items-center justify-center border transition-colors ${
                          isSelected
                            ? 'bg-indigo-600 border-indigo-600 text-white'
                            : 'border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800'
                        }`}
                      >
                        {isSelected && <Check className="w-3.5 h-3.5" />}
                      </div>

                      <FileSpreadsheet className="w-4 h-4 text-emerald-600 shrink-0" />

                      <div>
                        <div className="font-semibold text-slate-900 dark:text-white">
                          {file.name}
                        </div>
                        <div className="text-[11px] text-slate-400 flex items-center gap-2 mt-0.5 font-mono">
                          <span>{file.size}</span>
                          <span>•</span>
                          <span className="flex items-center gap-1 font-sans">
                            <Folder className="w-3 h-3" />
                            {file.path}
                          </span>
                        </div>
                      </div>
                    </div>

                    <span className="text-[11px] text-slate-400 font-mono">
                      {file.modified}
                    </span>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/40 flex items-center justify-between text-xs">
          <span className="text-slate-500">
            {selectedIds.length} item{selectedIds.length !== 1 ? 's' : ''} selected
          </span>

          <div className="flex items-center gap-2">
            <button
              onClick={onClose}
              className="px-3 py-1.5 bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-200 rounded-lg font-medium hover:bg-slate-300 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleImport}
              disabled={selectedIds.length === 0}
              className="px-4 py-1.5 bg-[#0B1528] text-white hover:bg-slate-800 disabled:opacity-40 rounded-lg font-semibold transition-colors"
            >
              Import Selected Workbooks
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
