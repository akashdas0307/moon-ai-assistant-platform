import React, { useEffect, useRef } from 'react';
import {
  FilePlus,
  FolderPlus,
  Edit2,
  Trash2,
  Copy,
  Download
} from 'lucide-react';

interface FileContextMenuProps {
  x: number;
  y: number;
  targetType: 'file' | 'directory';
  targetPath: string; // Kept for interface consistency, even if unused directly in rendering
  onClose: () => void;
  onNewFile: () => void;
  onNewFolder: () => void;
  onRename: () => void;
  onDelete: () => void;
  onCopyPath: () => void;
  onDownload: () => void;
}

export const FileContextMenu: React.FC<FileContextMenuProps> = ({
  x,
  y,
  targetType,
  // targetPath, // REMOVED from destructuring to avoid unused variable warning
  onClose,
  onNewFile,
  onNewFolder,
  onRename,
  onDelete,
  onCopyPath,
  onDownload
}) => {
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        onClose();
      }
    };

    // Also close on Escape
    const handleKeyDown = (event: KeyboardEvent) => {
        if (event.key === 'Escape') onClose();
    }

    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleKeyDown);
    return () => {
        document.removeEventListener('mousedown', handleClickOutside);
        document.removeEventListener('keydown', handleKeyDown);
    };
  }, [onClose]);

  // Adjust position to keep in viewport
  const style = {
      top: Math.min(y, window.innerHeight - 250), // prevent going off bottom
      left: Math.min(x, window.innerWidth - 200), // prevent going off right
  };

  return (
    <div
      ref={menuRef}
      className="fixed z-50 bg-[#252525] border border-[#404040] shadow-xl rounded py-1 min-w-[160px] text-sm animate-in fade-in duration-100"
      style={style}
    >
      {targetType === 'directory' && (
        <>
          <div
            className="flex items-center gap-2 px-3 py-2 hover:bg-blue-600 hover:text-white cursor-pointer text-gray-300"
            onClick={() => { onNewFile(); onClose(); }}
          >
            <FilePlus size={14} />
            <span>New File</span>
          </div>
          <div
            className="flex items-center gap-2 px-3 py-2 hover:bg-blue-600 hover:text-white cursor-pointer text-gray-300"
            onClick={() => { onNewFolder(); onClose(); }}
          >
            <FolderPlus size={14} />
            <span>New Folder</span>
          </div>
          <div className="h-px bg-[#404040] my-1" />
        </>
      )}

      <div
        className="flex items-center gap-2 px-3 py-2 hover:bg-blue-600 hover:text-white cursor-pointer text-gray-300"
        onClick={() => { onRename(); onClose(); }}
      >
        <Edit2 size={14} />
        <span>Rename</span>
      </div>

      <div
        className="flex items-center gap-2 px-3 py-2 hover:bg-blue-600 hover:text-white cursor-pointer text-gray-300"
        onClick={() => { onCopyPath(); onClose(); }}
      >
        <Copy size={14} />
        <span>Copy Path</span>
      </div>

      {targetType === 'file' && (
        <div
          className="flex items-center gap-2 px-3 py-2 hover:bg-blue-600 hover:text-white cursor-pointer text-gray-300"
          onClick={() => { onDownload(); onClose(); }}
        >
          <Download size={14} />
          <span>Download</span>
        </div>
      )}

      <div className="h-px bg-[#404040] my-1" />

      <div
        className="flex items-center gap-2 px-3 py-2 hover:bg-red-600 hover:text-white cursor-pointer text-red-400"
        onClick={() => { onDelete(); onClose(); }}
      >
        <Trash2 size={14} />
        <span>Delete</span>
      </div>
    </div>
  );
};
