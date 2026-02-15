const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface HealthResponse {
  status: string;
  timestamp: string;
  version: string;
}

interface MessageResponse {
  id: number;
  sender: string;
  content: string;
  timestamp: string;
}

interface ApiError {
  message: string;
  code?: string;
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;

    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
      });

      if (!response.ok) {
        const error: ApiError = {
          message: `HTTP ${response.status}: ${response.statusText}`,
          code: `HTTP_${response.status}`,
        };
        throw error;
      }

      return await response.json();
    } catch (error) {
      if (error instanceof TypeError && error.message.includes('fetch')) {
        const apiError: ApiError = {
          message: 'Cannot connect to backend. Make sure the server is running.',
          code: 'CONNECTION_ERROR',
        };
        throw apiError;
      }
      throw error;
    }
  }

  async checkHealth(): Promise<HealthResponse> {
    return this.request<HealthResponse>('/api/v1/health');
  }

  async getMessages(limit: number = 100): Promise<MessageResponse[]> {
    return this.request<MessageResponse[]>(`/api/v1/messages?limit=${limit}`);
  }
}

export const apiClient = new ApiClient();
export type { HealthResponse, ApiError, MessageResponse };
