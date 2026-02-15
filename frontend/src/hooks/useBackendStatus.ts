import { useState, useEffect } from 'react';
import { apiClient, HealthResponse, ApiError } from '../services/apiClient';

interface BackendStatus {
  connected: boolean;
  loading: boolean;
  error: string | null;
  health: HealthResponse | null;
}

export function useBackendStatus() {
  const [status, setStatus] = useState<BackendStatus>({
    connected: false,
    loading: true,
    error: null,
    health: null,
  });

  useEffect(() => {
    let mounted = true;

    const checkBackend = async () => {
      if (!mounted) return;

      try {
        const health = await apiClient.checkHealth();

        if (mounted) {
          setStatus({
            connected: true,
            loading: false,
            error: null,
            health,
          });
        }
      } catch (error) {
        if (mounted) {
          const apiError = error as ApiError;
          setStatus({
            connected: false,
            loading: false,
            error: apiError.message || 'Unknown error',
            health: null,
          });
        }
      }
    };

    // Initial check
    checkBackend();

    // Poll every 5 seconds
    const intervalId = window.setInterval(checkBackend, 5000);

    return () => {
      mounted = false;
      clearInterval(intervalId);
    };
  }, []);

  return status;
}
