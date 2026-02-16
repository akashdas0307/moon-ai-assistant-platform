import React, { useEffect, useState, useRef } from 'react';
import {
  Folder,
  File,
  ChevronRight,
  ChevronDown,
  FileText,
  FileCode,
  FileImage,
  RefreshCw,
  Loader2,
  Upload
} from 'lucide-react';
import { useWorkspaceStore } from '../../stores/workspaceStore';
import { FileItem, fileService } from '../../services/fileService';
import { FileContextMenu } from './FileContextMenu';
import { useToastStore } from '../../stores/toastStore';

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
  onContextMenu: (e: React.MouseEvent, item: FileItem) => void;
}

const FileTreeItem: React.FC<FileTreeItemProps> = ({ item, level, onContextMenu }) => {
  const { files, selectedFile, selectFile, loadFiles } = useWorkspaceStore();
  const [isExpanded, setIsExpanded] = useState(false);
  const [loading, setLoading] = useState(false);

  // Derive children from the flat list
  const children = files.filter(f => isDirectChild(item.path, f.path));
  const isSelected = selectedFile?.path === item.path;

  const handleToggle = async (e: React.MouseEvent) => {
    e.stopPropagation();

    // Select the file/folder visually and fetch content
    selectFile(item.path);

    if (item.type === 'file') {
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
        onContextMenu={(e) => onContextMenu(e, item)}
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
              <FileTreeItem key={child.path} item={child} level={level + 1} onContextMenu={onContextMenu} />
            ))
          )}
        </div>
      )}
    </div>
  );
};

interface FileBrowserProps {
  onCreateFile: (path: string) => void;
  onCreateFolder: (path: string) => void;
  onRename: (path: string) => void;
  onDelete: (path: string) => void;
}

export const FileBrowser: React.FC<FileBrowserProps> = ({
  onCreateFile,
  onCreateFolder,
  onRename,
  onDelete
}) => {
  const { files, loadFiles, isLoading, refreshFiles, createNode, selectedFile } = useWorkspaceStore();
  const { addToast } = useToastStore();
  const [initialized, setInitialized] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [contextMenu, setContextMenu] = useState<{
    visible: boolean;
    x: number;
    y: number;
    item: FileItem | null;
  }>({ visible: false, x: 0, y: 0, item: null });

  useEffect(() => {
    loadFiles('/').then(() => setInitialized(true));
  }, [loadFiles]);

  // Root files
  const rootFiles = files.filter(f => isDirectChild('/', f.path));

  const handleContextMenu = (e: React.MouseEvent, item: FileItem) => {
    e.preventDefault();
    e.stopPropagation();
    setContextMenu({
      visible: true,
      x: e.clientX,
      y: e.clientY,
      item
    });
  };

  const handleCloseContextMenu = () => {
    setContextMenu({ ...contextMenu, visible: false });
  };

  const getTargetDir = () => {
      if (!contextMenu.item) return '';
      if (contextMenu.item.type === 'directory') return contextMenu.item.path;
      // If file, return parent
      return contextMenu.item.path.split('/').slice(0, -1).join('/') || '/';
  };

  const handleDownload = async () => {
      if (!contextMenu.item || contextMenu.item.type !== 'file') return;
      try {
          const data = await fileService.readFile(contextMenu.item.path);
          const blob = new Blob([data.content], { type: 'text/plain' });
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = contextMenu.item.name;
          a.click();
          URL.revokeObjectURL(url);
          addToast('File downloaded successfully', 'success');
      } catch (e) {
          addToast('Failed to download file', 'error');
      }
  };

  const handleCopyPath = () => {
      if (contextMenu.item) {
          navigator.clipboard.writeText(contextMenu.item.path);
          addToast('Path copied to clipboard', 'success');
      }
  };

  const handleUploadClick = () => {
      fileInputRef.current?.click();
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (!file) return;

      const reader = new FileReader();
      reader.onload = async (ev) => {
          const content = ev.target?.result as string;
          // Determine path
          let parentPath = '';
          if (selectedFile) {
              // Check if selectedFile path exists in files list to know type
              const selItem = files.find(f => f.path === selectedFile.path);
              if (selItem?.type === 'directory') parentPath = selItem.path;
              else parentPath = selItem?.path.split('/').slice(0, -1).join('/') || '';
          }
          // Remove leading slash if needed, but createNode handles paths
          // Ensure parentPath doesn't start with / if it's empty

          const path = parentPath ? `${parentPath}/${file.name}` : file.name;

          try {
              await createNode(path, 'file', content);
              addToast(`File uploaded: ${file.name}`, 'success');
          } catch (err) {
              addToast('Failed to upload file', 'error');
          }
      };
      reader.readAsText(file);
      e.target.value = ''; // Reset
  };

  // If loading initially and no files, show skeleton
  if (!initialized && isLoading && files.length === 0) {
    return (
      <div className="flex flex-col h-full bg-[#1a1a1a] border-r border-[#404040] w-full p-4">
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
    <div className="flex flex-col h-full bg-[#1a1a1a] border-r border-[#404040] w-full"
         onContextMenu={(e) => {
             e.preventDefault();
             // Context menu on empty space - create file/folder at root
             setContextMenu({
                 visible: true,
                 x: e.clientX,
                 y: e.clientY,
                 item: { path: '/', type: 'directory', name: 'root' } // Mock root item
             });
         }}>
      <div className="flex items-center justify-between p-3 border-b border-[#404040]">
        <h2 className="text-sm font-semibold text-gray-200 uppercase tracking-wider">Workspace</h2>
        <div className="flex items-center gap-1">
            <button
              onClick={handleUploadClick}
              className="p-1 hover:bg-gray-800 rounded text-gray-400 hover:text-white transition-colors"
              title="Upload File"
            >
              <Upload size={14} />
            </button>
            <button
              onClick={() => refreshFiles()}
              className="p-1 hover:bg-gray-800 rounded text-gray-400 hover:text-white transition-colors"
              title="Refresh"
            >
              <RefreshCw size={14} />
            </button>
        </div>
      </div>

      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        className="hidden"
      />

      <div className="flex-1 overflow-y-auto overflow-x-hidden py-2 custom-scrollbar">
        {files.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-40 text-gray-500">
            <Folder size={32} className="mb-2 opacity-50" />
            <span className="text-xs">Workspace is empty</span>
          </div>
        ) : (
          <div className="flex flex-col">
            {rootFiles.map(file => (
              <FileTreeItem
                key={file.path}
                item={file}
                level={0}
                onContextMenu={handleContextMenu}
              />
            ))}
          </div>
        )}
      </div>

      {contextMenu.visible && contextMenu.item && (
        <FileContextMenu
          x={contextMenu.x}
          y={contextMenu.y}
          targetType={contextMenu.item.type}
          targetPath={contextMenu.item.path}
          onClose={handleCloseContextMenu}
          onNewFile={() => onCreateFile(getTargetDir())}
          onNewFolder={() => onCreateFolder(getTargetDir())}
          onRename={() => onRename(contextMenu.item!.path)}
          onDelete={() => onDelete(contextMenu.item!.path)}
          onCopyPath={handleCopyPath}
          onDownload={handleDownload}
        />
      )}
    </div>
  );
};
