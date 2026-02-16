import React from 'react';
import { useToastStore } from '../../stores/toastStore';
import { X, CheckCircle, AlertCircle, Info } from 'lucide-react';

const icons = {
  success: <CheckCircle className="text-green-500" size={20} />,
  error: <AlertCircle className="text-red-500" size={20} />,
  info: <Info className="text-blue-500" size={20} />,
};

const backgrounds = {
  success: 'bg-gray-800 border-green-500/50',
  error: 'bg-gray-800 border-red-500/50',
  info: 'bg-gray-800 border-blue-500/50',
};

export const Toast: React.FC = () => {
  const { toasts, removeToast } = useToastStore();

  if (toasts.length === 0) return null;

  return (
    <div className="fixed top-4 right-4 z-50 flex flex-col gap-2">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className={`
            flex items-center gap-3 p-4 rounded shadow-lg border-l-4 min-w-[300px] animate-in slide-in-from-right fade-in duration-300
            ${backgrounds[toast.type]}
          `}
        >
          {icons[toast.type]}
          <p className="flex-1 text-sm text-white">{toast.message}</p>
          <button
            onClick={() => removeToast(toast.id)}
            className="text-gray-400 hover:text-white transition-colors"
          >
            <X size={16} />
          </button>
        </div>
      ))}
    </div>
  );
};
