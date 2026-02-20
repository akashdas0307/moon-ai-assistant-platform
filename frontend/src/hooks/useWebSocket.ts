import { useEffect, useRef, useState, useCallback } from 'react';
import { Message } from '../types/chat';

export interface WebSocketConfig {
  url: string;
  onMessage?: (message: Message) => void;
  onStreamStart?: (messageId: string, userComId?: string) => void;
  onStreamToken?: (messageId: string, token: string) => void;
  onStreamEnd?: (messageId: string, fullContent: string, aiComId?: string) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Event) => void;
  autoReconnect?: boolean;
  reconnectInterval?: number;
}

export interface WebSocketState {
  isConnected: boolean;
  connectionError: string | null;
  sendMessage: (content: string, lastComId?: string | null) => void;
  disconnect: () => void;
}

export function useWebSocket(config: WebSocketConfig): WebSocketState {
  const {
    url,
    autoReconnect = true,
    reconnectInterval = 3000
  } = config;

  const [isConnected, setIsConnected] = useState(false);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const shouldReconnectRef = useRef(true);

  // Store all callbacks in refs so `connect` never needs them as deps
  const onMessageRef = useRef(config.onMessage);
  const onStreamStartRef = useRef(config.onStreamStart);
  const onStreamTokenRef = useRef(config.onStreamToken);
  const onStreamEndRef = useRef(config.onStreamEnd);
  const onConnectRef = useRef(config.onConnect);
  const onDisconnectRef = useRef(config.onDisconnect);
  const onErrorRef = useRef(config.onError);
  const autoReconnectRef = useRef(autoReconnect);
  const reconnectIntervalRef = useRef(reconnectInterval);

  // Keep refs in sync with latest prop values (no re-renders triggered)
  useEffect(() => { onMessageRef.current = config.onMessage; });
  useEffect(() => { onStreamStartRef.current = config.onStreamStart; });
  useEffect(() => { onStreamTokenRef.current = config.onStreamToken; });
  useEffect(() => { onStreamEndRef.current = config.onStreamEnd; });
  useEffect(() => { onConnectRef.current = config.onConnect; });
  useEffect(() => { onDisconnectRef.current = config.onDisconnect; });
  useEffect(() => { onErrorRef.current = config.onError; });
  useEffect(() => { autoReconnectRef.current = autoReconnect; });
  useEffect(() => { reconnectIntervalRef.current = reconnectInterval; });

  // connect only depends on `url` — stable reference, no infinite loop
  const connect = useCallback(() => {
    // Cancel any pending reconnect
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    // Close existing connection cleanly
    if (wsRef.current) {
      wsRef.current.onclose = null; // prevent reconnect trigger on manual close
      wsRef.current.close();
      wsRef.current = null;
    }

    try {
      const ws = new WebSocket(url);

      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        setConnectionError(null);
        onConnectRef.current?.();
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          if (data.type === 'connection') {
            console.log('Connection confirmed:', data.message);
          } else if (data.type === 'stream_start') {
            onStreamStartRef.current?.(data.message_id, data.user_com_id);
          } else if (data.type === 'stream_token') {
            onStreamTokenRef.current?.(data.message_id, data.token);
          } else if (data.type === 'stream_end') {
            onStreamEndRef.current?.(data.message_id, data.content, data.ai_com_id);
          } else if (data.type === 'echo' || data.type === 'message') {
            const sender = data.sender === 'assistant' ? 'ai' : (data.sender || 'ai');
            const message: Message = {
              id: data.timestamp || Date.now().toString(),
              sender: sender as 'user' | 'ai',
              content: data.content || data.server_message || data.original_message?.content || '',
              timestamp: new Date(data.timestamp || Date.now())
            };
            onMessageRef.current?.(message);
          } else if (data.type === 'error') {
            console.error('Server error:', data.message);
            setConnectionError(data.message);
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setConnectionError('WebSocket connection error');
        onErrorRef.current?.(error);
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
        onDisconnectRef.current?.();

        if (autoReconnectRef.current && shouldReconnectRef.current) {
          console.log(`Reconnecting in ${reconnectIntervalRef.current}ms...`);
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, reconnectIntervalRef.current);
        }
      };

      wsRef.current = ws;
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
      setConnectionError('Failed to connect to server');
    }
  }, [url]); // ← ONLY url as dependency — this is the critical fix

  const sendMessage = useCallback((content: string, lastComId?: string | null) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      const message = {
        type: 'message',
        content,
        timestamp: new Date().toISOString(),
        last_com_id: lastComId ?? null
      };
      wsRef.current.send(JSON.stringify(message));
      console.log('Message sent:', message);
    } else {
      console.error('WebSocket is not connected');
      setConnectionError('Cannot send message: not connected');
    }
  }, []);

  const disconnect = useCallback(() => {
    shouldReconnectRef.current = false;
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    if (wsRef.current) {
      wsRef.current.onclose = null; // prevent auto-reconnect on manual disconnect
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsConnected(false);
  }, []);

  // Only runs once on mount (connect only changes if url changes)
  useEffect(() => {
    shouldReconnectRef.current = true;
    connect();

    return () => {
      shouldReconnectRef.current = false;
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        // Do NOT null out onclose here — onDisconnect should fire on unmount.
        // shouldReconnectRef.current is false so no auto-reconnect will occur.
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [connect]); // connect is now stable (only changes if url changes)

  return {
    isConnected,
    connectionError,
    sendMessage,
    disconnect
  };
}
