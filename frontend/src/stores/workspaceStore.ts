import { create } from 'zustand';
import { fileService, FileItem } from '../services/fileService';
import { getFileType, FileType } from '../utils/fileTypes';

export interface OpenFile {
  path: string;
  name: string;
  content: string;
  type: FileType;
  isDirty: boolean;
  loading: boolean;
  error?: string;
}

interface WorkspaceState {
  // File Browser State
  files: FileItem[];
  currentPath: string;
  selectedFile: string | null;
  isLoading: boolean;
  error: string | null;

  // File Viewer State
  openFiles: OpenFile[];
  activeFilePath: string | null;

  // Actions
  loadFiles: (path?: string) => Promise<void>;
  selectFile: (path: string | null) => void;
  refreshFiles: () => Promise<void>;

  // Viewer Actions
  openFile: (path: string) => Promise<void>;
  closeFile: (path: string) => void;
  setActiveFile: (path: string) => void;
  closeAllFiles: () => void;
}

export const useWorkspaceStore = create<WorkspaceState>((set, get) => ({
  // Initial State
  files: [],
  currentPath: '/',
  selectedFile: null,
  isLoading: false,
  error: null,
  openFiles: [],
  activeFilePath: null,

  loadFiles: async (path: string = '/') => {
    set({ isLoading: true, error: null });

    try {
      const newFiles = await fileService.listFiles(path);

      set((state) => {
        const parentPath = path === '/' ? '' : path;
        const otherFiles = state.files.filter(f => !f.path.startsWith(parentPath + '/'));

        newFiles.sort((a, b) => {
          if (a.type === b.type) return a.name.localeCompare(b.name);
          return a.type === 'directory' ? -1 : 1;
        });

        return {
          files: [...otherFiles, ...newFiles],
          isLoading: false
        };
      });
    } catch (error) {
       console.error('Failed to load files:', error);
       set({ error: (error as Error).message, isLoading: false });
    }
  },

  selectFile: (path: string | null) => {
    set({ selectedFile: path });
  },

  refreshFiles: async () => {
    const { loadFiles } = get();
    await loadFiles('/');
  },

  openFile: async (path: string) => {
    const { openFiles, setActiveFile } = get();

    // Check if already open
    const existingFile = openFiles.find(f => f.path === path);
    if (existingFile) {
      setActiveFile(path);
      return;
    }

    const name = path.split('/').pop() || path;
    const type = getFileType(name);

    // Create new file entry
    const newFile: OpenFile = {
      path,
      name,
      content: '',
      type,
      isDirty: false,
      loading: true
    };

    // Add to open files immediately (with loading state)
    set(state => ({
      openFiles: [...state.openFiles, newFile],
      activeFilePath: path
    }));

    try {
      // If it's an image, we don't need to fetch content (viewer handles it via URL)
      if (type === 'image') {
        set(state => ({
          openFiles: state.openFiles.map(f =>
            f.path === path ? { ...f, loading: false } : f
          )
        }));
        return;
      }

      // Fetch content for text/code files
      const fileContent = await fileService.readFile(path);

      set(state => ({
        openFiles: state.openFiles.map(f =>
          f.path === path ? {
            ...f,
            content: fileContent.content,
            loading: false
          } : f
        )
      }));
    } catch (error) {
      console.error('Failed to open file:', error);
      set(state => ({
        openFiles: state.openFiles.map(f =>
          f.path === path ? {
            ...f,
            loading: false,
            error: (error as Error).message
          } : f
        )
      }));
    }
  },

  closeFile: (path: string) => {
    set(state => {
      const newOpenFiles = state.openFiles.filter(f => f.path !== path);
      let newActivePath = state.activeFilePath;

      // If closing active file, switch to another one
      if (state.activeFilePath === path) {
        if (newOpenFiles.length > 0) {
          // Try to go to the one to the right, or the last one
          // Here we just pick the last one or the one at the same index?
          // Simple logic: pick the last one in the new list
          newActivePath = newOpenFiles[newOpenFiles.length - 1].path;
        } else {
          newActivePath = null;
        }
      }

      return {
        openFiles: newOpenFiles,
        activeFilePath: newActivePath
      };
    });
  },

  setActiveFile: (path: string) => {
    set({ activeFilePath: path });
  },

  closeAllFiles: () => {
    set({ openFiles: [], activeFilePath: null });
  }
}));
