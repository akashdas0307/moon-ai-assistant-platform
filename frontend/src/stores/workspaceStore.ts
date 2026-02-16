import { create } from 'zustand';
import { fileService, FileItem } from '../services/fileService';

interface WorkspaceState {
  files: FileItem[];
  currentPath: string;
  selectedFile: string | null;
  isLoading: boolean;
  error: string | null;

  // Actions
  loadFiles: (path?: string) => Promise<void>;
  selectFile: (path: string | null) => void;
  refreshFiles: () => Promise<void>;
}

export const useWorkspaceStore = create<WorkspaceState>((set, get) => ({
  files: [],
  currentPath: '/',
  selectedFile: null,
  isLoading: false,
  error: null,

  loadFiles: async (path: string = '/') => {
    set({ isLoading: true, error: null });

    try {
      const newFiles = await fileService.listFiles(path);

      set((state) => {
        // Remove all descendants of the path we are loading to ensure fresh state
        // This handles deletions and updates correctly
        const parentPath = path === '/' ? '' : path;

        // Filter out any file that is a descendant of the loaded path
        // We look for paths that start with "{path}/"
        const otherFiles = state.files.filter(f => !f.path.startsWith(parentPath + '/'));

        // Sort new files: Directories first, then files. Alphabetical.
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
  }
}));
