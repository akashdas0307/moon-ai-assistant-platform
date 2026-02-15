import { renderHook, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useWebSocket } from '../useWebSocket';

// Mock WebSocket
class MockWebSocket {
  onopen: (() => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;
  onclose: (() => void) | null = null;
  readyState: number = 0; // WebSocket.CONNECTING
  url: string;

  static readonly CONNECTING = 0;
  static readonly OPEN = 1;
  static readonly CLOSING = 2;
  static readonly CLOSED = 3;

  constructor(url: string) {
    this.url = url;
    setTimeout(() => {
      this.readyState = MockWebSocket.OPEN;
      this.onopen?.();
    }, 0);
  }

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  send(_data: string) {
    // Mock send
  }

  close() {
    this.readyState = MockWebSocket.CLOSED;
    this.onclose?.();
  }
}

global.WebSocket = MockWebSocket as unknown as typeof WebSocket;

describe('useWebSocket', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should connect to WebSocket on mount', async () => {
    const onConnect = vi.fn();
    const { result } = renderHook(() =>
      useWebSocket({
        url: 'ws://localhost:8000/ws',
        onConnect,
      })
    );

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    });

    expect(onConnect).toHaveBeenCalled();
  });

  it('should send messages when connected', async () => {
    const { result } = renderHook(() =>
      useWebSocket({
        url: 'ws://localhost:8000/ws',
      })
    );

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    });

    // Should not throw
    expect(() => {
      result.current.sendMessage('Hello');
    }).not.toThrow();
  });

  it('should disconnect on unmount', async () => {
    const onDisconnect = vi.fn();
    const { result, unmount } = renderHook(() =>
      useWebSocket({
        url: 'ws://localhost:8000/ws',
        onDisconnect,
      })
    );

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    });

    unmount();

    await waitFor(() => {
      expect(onDisconnect).toHaveBeenCalled();
    });
  });
});
