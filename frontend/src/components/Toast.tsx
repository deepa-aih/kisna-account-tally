import React from 'react';
import { CheckCircle2, Info, X } from 'lucide-react';

interface ToastProps {
  message: string | null;
  onClose: () => void;
}

export const Toast: React.FC<ToastProps> = ({ message, onClose }) => {
  if (!message) return null;

  return (
    <div className="fixed bottom-6 right-6 z-50 animate-in fade-in slide-in-from-bottom-5 duration-200">
      <div className="bg-[#0B1528] text-white px-4 py-3 rounded-xl shadow-xl border border-slate-700/80 flex items-center gap-3 text-xs max-w-md">
        <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
        <span className="font-medium text-slate-100">{message}</span>
        <button
          onClick={onClose}
          className="p-1 text-slate-400 hover:text-white rounded-md transition-colors ml-auto"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
};
