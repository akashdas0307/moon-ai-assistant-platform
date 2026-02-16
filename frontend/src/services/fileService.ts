import { apiClient } from './apiClient';

export interface FileItem {
  name: string;
  path: string;
  type: 'file' | 'directory';
  size?: number;
  modified_at?: string;
  extension?: string;
}

export interface FileContent {
  content: string;
  encoding: string;
}

export const fileService = {
  // GET /api/v1/files?path={path}
  async listFiles(path: string = '/'): Promise<FileItem[]> {
    return apiClient.request<FileItem[]>(`/api/v1/files?path=${encodeURIComponent(path)}`);
  },

  // GET /api/v1/files/content?path={path}
  async readFile(path: string): Promise<FileContent> {
    return apiClient.request<FileContent>(`/api/v1/files/content?path=${encodeURIComponent(path)}`);
  },

  // POST /api/v1/files
  async createFile(path: string, type: 'file' | 'directory', content?: string): Promise<FileItem> {
    return apiClient.request<FileItem>('/api/v1/files', {
      method: 'POST',
      body: JSON.stringify({ path, type, content }),
    });
  },

  // DELETE /api/v1/files?path={path}
  async deleteFile(path: string): Promise<void> {
    return apiClient.request<void>(`/api/v1/files?path=${encodeURIComponent(path)}`, {
      method: 'DELETE',
    });
  }
};
