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
    onMessage,
    onStreamStart,
    onStreamToken,
    onStreamEnd,
    onConnect,
    onDisconnect,
    onError,
    autoReconnect = true,
    reconnectInterval = 3000
  } = config;

  const [isConnected, setIsConnected] = useState(false);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const shouldReconnectRef = useRef(true);

  const connect = useCallback(() => {
    try {
      // Cleanup previous connection if it exists
      if (wsRef.current) {
        wsRef.current.close();
      }

      const ws = new WebSocket(url);

      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        setConnectionError(null);
        onConnect?.();
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          // console.log('WebSocket message received:', data); // Too noisy for streaming tokens

          // Handle different message types
          if (data.type === 'connection') {
            // Connection confirmation message
            console.log('Connection confirmed:', data.message);
          } else if (data.type === 'stream_start') {
            onStreamStart?.(data.message_id, data.user_com_id);
          } else if (data.type === 'stream_token') {
            onStreamToken?.(data.message_id, data.token);
          } else if (data.type === 'stream_end') {
            onStreamEnd?.(data.message_id, data.content, data.ai_com_id);
          } else if (data.type === 'echo' || data.type === 'message') {
            // Convert to Message format and pass to callback
            // Map 'assistant' sender from backend to 'ai' for frontend
            const sender = data.sender === 'assistant' ? 'ai' : (data.sender || 'ai');

            const message: Message = {
              id: data.timestamp || Date.now().toString(),
              sender: sender as 'user' | 'ai',
              content: data.content || data.server_message || data.original_message?.content || '',
              timestamp: new Date(data.timestamp || Date.now())
            };
            onMessage?.(message);
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
        onError?.(error);
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
        onDisconnect?.();

        // Auto-reconnect if enabled
        if (autoReconnect && shouldReconnectRef.current) {
          console.log('Reconnecting in ' + reconnectInterval + 'ms...');
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, reconnectInterval);
        }
      };

      wsRef.current = ws;
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
      setConnectionError('Failed to connect to server');
    }
  }, [url, onMessage, onStreamStart, onStreamToken, onStreamEnd, onConnect, onDisconnect, onError, autoReconnect, reconnectInterval]);

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
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  useEffect(() => {
    shouldReconnectRef.current = true;
    connect();

    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    isConnected,
    connectionError,
    sendMessage,
    disconnect
  };
}
