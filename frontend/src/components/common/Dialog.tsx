import React, { useEffect, useRef, useState } from 'react';
import { X } from 'lucide-react';

interface DialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (value?: string) => void;
  title: string;
  message?: string;
  inputValue?: string;
  inputPlaceholder?: string;
  confirmText?: string;
  cancelText?: string;
  type?: 'confirm' | 'prompt' | 'alert';
}

export const Dialog: React.FC<DialogProps> = ({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  inputValue = '',
  inputPlaceholder = '',
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  type = 'confirm',
}) => {
  const [value, setValue] = useState(inputValue);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isOpen) {
      setValue(inputValue);
      if (type === 'prompt') {
        // Small delay to ensure render
        setTimeout(() => {
            inputRef.current?.focus();
            inputRef.current?.select();
        }, 100);
      }
    }
  }, [isOpen, inputValue, type]);

  if (!isOpen) return null;

  const handleConfirm = () => {
    onConfirm(type === 'prompt' ? value : undefined);
    onClose();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') handleConfirm();
    if (e.key === 'Escape') onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm" onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
    }}>
      <div className="bg-[#1e1e1e] border border-[#404040] rounded-lg shadow-xl w-full max-w-md overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        <div className="flex items-center justify-between p-4 border-b border-[#404040]">
          <h3 className="text-lg font-semibold text-gray-100">{title}</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-white transition-colors">
            <X size={20} />
          </button>
        </div>

        <div className="p-6">
          {message && <p className="text-gray-300 mb-4">{message}</p>}

          {type === 'prompt' && (
            <input
              ref={inputRef}
              type="text"
              value={value}
              onChange={(e) => setValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={inputPlaceholder}
              className="w-full bg-[#252525] border border-[#404040] rounded px-3 py-2 text-white focus:outline-none focus:border-blue-500 transition-colors"
            />
          )}
        </div>

        <div className="flex justify-end gap-3 p-4 bg-[#252525] border-t border-[#404040]">
          {type !== 'alert' && (
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm text-gray-300 hover:text-white hover:bg-[#333] rounded transition-colors"
            >
              {cancelText}
            </button>
          )}
          <button
            onClick={handleConfirm}
            className="px-4 py-2 text-sm bg-blue-600 hover:bg-blue-500 text-white rounded transition-colors font-medium"
          >
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
};
