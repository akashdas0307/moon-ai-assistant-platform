import React, { useRef, useEffect } from 'react';
import { X, FileCode, FileImage, FileText, File } from 'lucide-react';
import { useWorkspaceStore } from '../../stores/workspaceStore';
import { FileType } from '../../utils/fileTypes';

const getFileIcon = (type: FileType) => {
  switch (type) {
    case 'code':
      return <FileCode size={14} className="text-blue-400" />;
    case 'image':
      return <FileImage size={14} className="text-purple-400" />;
    case 'markdown':
    case 'text':
      return <FileText size={14} className="text-gray-400" />;
    default:
      return <File size={14} className="text-gray-500" />;
  }
};

export const FileViewerTabs: React.FC = () => {
  const { openFiles, activeFilePath, setActiveFile, closeFile } = useWorkspaceStore();
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  // Scroll active tab into view
  useEffect(() => {
    if (activeFilePath && scrollContainerRef.current) {
      // Logic to scroll to active tab can be added here if needed
      // For now, basic scroll is usually sufficient
    }
  }, [activeFilePath]);

  if (openFiles.length === 0) return null;

  return (
    <div
      ref={scrollContainerRef}
      className="flex bg-[#252525] border-b border-[#404040] overflow-x-auto custom-scrollbar h-9 flex-shrink-0"
    >
      {openFiles.map((file) => {
        const isActive = file.path === activeFilePath;

        return (
          <div
            key={file.path}
            className={`
              flex items-center gap-2 px-3 min-w-[120px] max-w-[200px] border-r border-[#404040] cursor-pointer select-none
              hover:bg-[#2a2a2a] transition-colors group
              ${isActive ? 'bg-[#1e1e1e] text-white border-t-2 border-t-blue-500' : 'text-gray-400 bg-[#252525]'}
            `}
            onClick={() => setActiveFile(file.path)}
            title={file.path}
          >
            <span className="flex-shrink-0">
              {getFileIcon(file.type)}
            </span>
            <span className="truncate text-xs flex-1">
              {file.name}
            </span>
            <button
              className={`
                p-0.5 rounded-sm hover:bg-gray-700 opacity-0 group-hover:opacity-100 transition-opacity
                ${isActive ? 'opacity-100' : ''}
              `}
              onClick={(e) => {
                e.stopPropagation();
                closeFile(file.path);
              }}
            >
              <X size={12} />
            </button>
          </div>
        );
      })}
    </div>
  );
};
