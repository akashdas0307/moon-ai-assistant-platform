import React, { useState, useEffect } from 'react';
import { FileBrowser } from './FileBrowser';
import { FileViewer } from './FileViewer';
import { Dialog } from '../common/Dialog';
import { useWorkspaceStore } from '../../stores/workspaceStore';
import { useToastStore } from '../../stores/toastStore';

interface WorkspacePanelProps {
  visible?: boolean;
}

type DialogType = 'createFile' | 'createFolder' | 'rename' | 'delete' | null;

export const WorkspacePanel: React.FC<WorkspacePanelProps> = ({ visible = true }) => {
  const { createNode, deleteNode, renameNode, selectedFile, files } = useWorkspaceStore();
  const { addToast } = useToastStore();

  const [dialogState, setDialogState] = useState<{
    isOpen: boolean;
    type: DialogType;
    path: string;
    inputValue?: string;
  }>({ isOpen: false, type: null, path: '' });

  const handleCreateFile = (path: string) => {
    setDialogState({ isOpen: true, type: 'createFile', path });
  };

  const handleCreateFolder = (path: string) => {
    setDialogState({ isOpen: true, type: 'createFolder', path });
  };

  const handleRename = (path: string) => {
    const name = path.split('/').pop() || '';
    setDialogState({ isOpen: true, type: 'rename', path, inputValue: name });
  };

  const handleDelete = (path: string) => {
    setDialogState({ isOpen: true, type: 'delete', path });
  };

  const handleDialogConfirm = async (value?: string) => {
    const { type, path } = dialogState;
    try {
        if (type === 'createFile' && value) {
            const newPath = path === '/' ? value : `${path}/${value}`;
            const cleanPath = newPath.replace('//', '/');
            await createNode(cleanPath, 'file', '');
            addToast(`File created: ${value}`, 'success');
        } else if (type === 'createFolder' && value) {
            const newPath = path === '/' ? value : `${path}/${value}`;
            const cleanPath = newPath.replace('//', '/');
            await createNode(cleanPath, 'directory');
            addToast(`Folder created: ${value}`, 'success');
        } else if (type === 'rename' && value) {
            if (value === path.split('/').pop()) return;

            const newPath = path.substring(0, path.lastIndexOf('/') + 1) + value;

            await renameNode(path, newPath);
            addToast(`Renamed to ${value}`, 'success');
        } else if (type === 'delete') {
            await deleteNode(path);
            addToast('Item deleted', 'success');
        }
    } catch (error) {
        addToast(`Operation failed: ${(error as Error).message}`, 'error');
    }
  };

  // Keyboard Shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
        // Ctrl+N (New File)
        if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
            e.preventDefault();
            let path = '/';
            if (selectedFile) {
               // Try to find context from files list
               const item = files.find(f => f.path === selectedFile.path);
               if (item?.type === 'directory') {
                   path = item.path;
               } else {
                   const parts = selectedFile.path.split('/');
                   if (parts.length > 1) path = parts.slice(0, -1).join('/');
               }
            }
            handleCreateFile(path);
        }

        // F2 (Rename)
        if (e.key === 'F2') {
            e.preventDefault();
            if (selectedFile) {
                handleRename(selectedFile.path);
            }
        }

        // Delete
        if (e.key === 'Delete') {
             if (document.activeElement?.tagName === 'INPUT' || document.activeElement?.tagName === 'TEXTAREA') return;

             e.preventDefault();
             if (selectedFile) {
                 handleDelete(selectedFile.path);
             }
        }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [selectedFile, files]);

  if (!visible) return null;

  let dialogProps = {
      title: '',
      message: '',
      confirmText: 'Confirm',
      type: 'confirm' as 'confirm' | 'prompt' | 'alert',
      inputPlaceholder: ''
  };

  switch (dialogState.type) {
      case 'createFile':
          dialogProps = {
              title: 'New File',
              message: `Create new file in ${dialogState.path}`,
              confirmText: 'Create',
              type: 'prompt',
              inputPlaceholder: 'filename.txt'
          };
          break;
      case 'createFolder':
          dialogProps = {
              title: 'New Folder',
              message: `Create new folder in ${dialogState.path}`,
              confirmText: 'Create',
              type: 'prompt',
              inputPlaceholder: 'folder_name'
          };
          break;
      case 'rename':
          dialogProps = {
              title: 'Rename',
              message: `Rename ${dialogState.path}`,
              confirmText: 'Rename',
              type: 'prompt',
              inputPlaceholder: 'new_name'
          };
          break;
      case 'delete':
          dialogProps = {
              title: 'Delete',
              message: `Are you sure you want to delete ${dialogState.path}? This cannot be undone.`,
              confirmText: 'Delete',
              type: 'confirm',
              inputPlaceholder: ''
          };
          break;
  }

  return (
    <div className="flex h-full w-full bg-[#1a1a1a] overflow-hidden relative">
      <div className="w-[260px] flex-none h-full border-r border-[#404040]">
        <FileBrowser
            onCreateFile={handleCreateFile}
            onCreateFolder={handleCreateFolder}
            onRename={handleRename}
            onDelete={handleDelete}
        />
      </div>

      <div className="flex-1 min-w-0 h-full">
        <FileViewer />
      </div>

      <Dialog
        isOpen={dialogState.isOpen}
        onClose={() => setDialogState({ ...dialogState, isOpen: false })}
        onConfirm={handleDialogConfirm}
        inputValue={dialogState.type === 'rename' ? dialogState.inputValue : ''}
        {...dialogProps}
      />
    </div>
  );
};
