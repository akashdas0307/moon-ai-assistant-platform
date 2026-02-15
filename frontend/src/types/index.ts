export interface BackendHealth {
  status: string;
  timestamp: string;
  version: string;
}

export interface ConnectionStatus {
  connected: boolean;
  loading: boolean;
  error: string | null;
}
