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
  path: string;
  content: string;
  encoding: string;
  size: number;
}

export const fileService = {
  // GET /api/v1/files?path={path}
  async listFiles(path: string = '/'): Promise<FileItem[]> {
    return apiClient.request<FileItem[]>(`/api/v1/files?path=${encodeURIComponent(path)}`);
  },

  // GET /api/v1/files/content?path={path}
  async readFile(path: string): Promise<FileContent> {
    try {
      const response = await apiClient.request<FileContent>(`/api/v1/files/content?path=${encodeURIComponent(path)}`);
      return response;
    } catch (error) {
      console.error('Failed to read file:', error);
      throw new Error(`Failed to read file: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
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
