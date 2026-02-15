import { useBackendStatus } from '../hooks/useBackendStatus';

export function StatusIndicator() {
  const { connected, loading, error, health } = useBackendStatus();

  return (
    <div className="flex items-center gap-2 px-3 py-1.5 bg-gray-800 rounded-lg border border-gray-700">
      {/* Status Dot */}
      <div className="relative">
        <div
          className={`w-2 h-2 rounded-full ${
            loading
              ? 'bg-yellow-500'
              : connected
              ? 'bg-green-500'
              : 'bg-red-500'
          }`}
        />
        {connected && (
          <div className="absolute inset-0 w-2 h-2 rounded-full bg-green-500 animate-ping opacity-75" />
        )}
      </div>

      {/* Status Text */}
      <div className="flex flex-col">
        <span className="text-xs font-medium text-gray-200">
          {loading
            ? 'Connecting...'
            : connected
            ? 'Backend Connected'
            : 'Backend Offline'}
        </span>
        {error && (
          <span className="text-xs text-red-400">{error}</span>
        )}
        {health && (
          <span className="text-xs text-gray-400">
            v{health.version}
          </span>
        )}
      </div>
    </div>
  );
}
