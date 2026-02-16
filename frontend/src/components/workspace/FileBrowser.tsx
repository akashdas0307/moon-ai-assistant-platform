import React, { useEffect, useState } from 'react';
import {
  Folder,
  File,
  ChevronRight,
  ChevronDown,
  FileText,
  FileCode,
  FileImage,
  RefreshCw,
  Loader2
} from 'lucide-react';
import { useWorkspaceStore } from '../../stores/workspaceStore';
import { FileItem } from '../../services/fileService';

// Helper to check if file is a direct child
const isDirectChild = (parentPath: string, filePath: string) => {
  const parent = parentPath === '/' ? '' : parentPath;
  if (!filePath.startsWith(parent + '/')) return false;
  const relative = filePath.slice(parent.length + 1);
  return !relative.includes('/');
};

// Icon helper
const getFileIcon = (name: string) => {
  const ext = name.split('.').pop()?.toLowerCase();
  switch (ext) {
    case 'ts':
    case 'tsx':
    case 'js':
    case 'jsx':
    case 'json':
    case 'css':
    case 'html':
      return <FileCode size={16} className="text-blue-400" />;
    case 'png':
    case 'jpg':
    case 'jpeg':
    case 'svg':
      return <FileImage size={16} className="text-purple-400" />;
    case 'md':
    case 'txt':
      return <FileText size={16} className="text-gray-400" />;
    default:
      return <File size={16} className="text-gray-500" />;
  }
};

interface FileTreeItemProps {
  item: FileItem;
  level: number;
}

const FileTreeItem: React.FC<FileTreeItemProps> = ({ item, level }) => {
  const { files, selectedFile, selectFile, loadFiles, openFile } = useWorkspaceStore();
  const [isExpanded, setIsExpanded] = useState(false);
  const [loading, setLoading] = useState(false);

  // Derive children from the flat list
  const children = files.filter(f => isDirectChild(item.path, f.path));
  const isSelected = selectedFile === item.path;

  const handleToggle = async (e: React.MouseEvent) => {
    e.stopPropagation();

    // Select the file/folder visually
    selectFile(item.path);

    if (item.type === 'file') {
      // Open the file in the viewer
      openFile(item.path);
      return;
    }

    // Toggle folder expansion
    if (!isExpanded) {
      setLoading(true);
      await loadFiles(item.path);
      setLoading(false);
    }
    setIsExpanded(!isExpanded);
  };

  return (
    <div>
      <div
        className={`
          flex items-center py-1 px-2 cursor-pointer select-none
          hover:bg-gray-800 transition-colors
          ${isSelected ? 'bg-blue-900/30 text-blue-200' : 'text-gray-300'}
        `}
        style={{ paddingLeft: `${level * 12 + 8}px` }}
        onClick={handleToggle}
      >
        <span className="mr-1 opacity-70">
          {item.type === 'directory' && (
            loading ? (
              <Loader2 size={16} className="animate-spin" />
            ) : (
              isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />
            )
          )}
          {item.type === 'file' && <span className="w-4" />}
        </span>

        <span className="mr-2">
          {item.type === 'directory' ? (
            <Folder size={16} className={isExpanded ? 'text-yellow-400' : 'text-yellow-500'} />
          ) : (
            getFileIcon(item.name)
          )}
        </span>

        <span className="truncate text-sm">{item.name}</span>
      </div>

      {isExpanded && item.type === 'directory' && (
        <div>
          {children.length === 0 && !loading ? (
             <div
               className="text-gray-500 text-xs py-1 italic"
               style={{ paddingLeft: `${(level + 1) * 12 + 28}px` }}
             >
               Empty
             </div>
          ) : (
            children.map(child => (
              <FileTreeItem key={child.path} item={child} level={level + 1} />
            ))
          )}
        </div>
      )}
    </div>
  );
};

export const FileBrowser: React.FC = () => {
  const { files, loadFiles, isLoading, refreshFiles } = useWorkspaceStore();
  const [initialized, setInitialized] = useState(false);

  useEffect(() => {
    loadFiles('/').then(() => setInitialized(true));
  }, [loadFiles]);

  // Root files
  const rootFiles = files.filter(f => isDirectChild('/', f.path));

  // If loading initially and no files, show skeleton
  if (!initialized && isLoading && files.length === 0) {
    return (
      <div className="flex flex-col h-full bg-[#1a1a1a] border-r border-[#404040] w-64 p-4">
         <div className="flex items-center justify-between mb-4">
           <div className="h-6 w-24 bg-gray-800 rounded animate-pulse"></div>
         </div>
         <div className="space-y-2">
           {[1, 2, 3, 4, 5].map(i => (
             <div key={i} className="h-6 bg-gray-800 rounded animate-pulse w-full"></div>
           ))}
         </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-[#1a1a1a] border-r border-[#404040] w-64 flex-none">
      <div className="flex items-center justify-between p-3 border-b border-[#404040]">
        <h2 className="text-sm font-semibold text-gray-200 uppercase tracking-wider">Workspace</h2>
        <button
          onClick={() => refreshFiles()}
          className="p-1 hover:bg-gray-800 rounded text-gray-400 hover:text-white transition-colors"
          title="Refresh"
        >
          <RefreshCw size={14} />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto overflow-x-hidden py-2 custom-scrollbar">
        {files.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-40 text-gray-500">
            <Folder size={32} className="mb-2 opacity-50" />
            <span className="text-xs">Workspace is empty</span>
          </div>
        ) : (
          <div className="flex flex-col">
            {rootFiles.map(file => (
              <FileTreeItem key={file.path} item={file} level={0} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
