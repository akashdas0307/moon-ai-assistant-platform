import { useState, useCallback, useEffect } from 'react';
import { Message } from '../../types/chat';
import { MessageList } from './MessageList';
import { MessageInput } from './MessageInput';
import { TypingIndicator } from './TypingIndicator';
import { useWebSocket } from '../../hooks/useWebSocket';
import { WEBSOCKET_URL } from '../../config/constants';
import { useMessageStore } from '../../stores/messageStore';

export function ChatPanel() {
  const { messages, addMessage, loadMessages, isLoading, error } = useMessageStore();
  const [isTyping, setIsTyping] = useState(false);

  // Load messages on mount
  useEffect(() => {
    loadMessages();
  }, [loadMessages]);

  // Handle incoming WebSocket messages
  const handleWebSocketMessage = useCallback((message: Message) => {
    addMessage(message);
    setIsTyping(false);
  }, [addMessage]);

  // Handle WebSocket connection
  const handleConnect = useCallback(() => {
    console.log('Connected to WebSocket server');
  }, []);

  const handleDisconnect = useCallback(() => {
    console.log('Disconnected from WebSocket server');
  }, []);

  const handleError = useCallback((error: Event) => {
    console.error('WebSocket error:', error);
  }, []);

  // Initialize WebSocket connection
  const { isConnected, connectionError, sendMessage: sendWebSocketMessage } = useWebSocket({
    url: WEBSOCKET_URL,
    onMessage: handleWebSocketMessage,
    onConnect: handleConnect,
    onDisconnect: handleDisconnect,
    onError: handleError,
    autoReconnect: true,
    reconnectInterval: 3000
  });

  const handleSendMessage = (content: string) => {
    // Add user message to UI immediately
    const userMessage: Message = {
      id: Date.now().toString(),
      sender: 'user',
      content,
      timestamp: new Date()
    };
    addMessage(userMessage);

    // Show typing indicator
    setIsTyping(true);

    // Send message via WebSocket
    sendWebSocketMessage(content);
  };

  return (
    <div className="flex flex-col h-[600px] w-full max-w-4xl mx-auto bg-gray-800 rounded-xl overflow-hidden shadow-2xl border border-gray-700">
      <div className="bg-gray-900 p-4 border-b border-gray-700 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-white flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : (connectionError ? 'bg-red-500' : 'bg-yellow-500')}`}></span>
          Moon AI Chat
        </h2>
        <div className="flex flex-col items-end">
          {connectionError && (
            <span className="text-xs text-red-400">{connectionError}</span>
          )}
          {!isConnected && !connectionError && (
            <span className="text-xs text-yellow-400">Connecting...</span>
          )}
          {isLoading && (
            <span className="text-xs text-blue-400">Loading history...</span>
          )}
        </div>
      </div>

      {error && (
         <div className="p-2 bg-red-900/50 text-red-200 text-sm text-center">
            Failed to load chat history: {error}
         </div>
      )}

      <MessageList messages={messages} />

      <div className="px-4 pb-2 bg-gray-900">
        <TypingIndicator isTyping={isTyping} />
      </div>

      <MessageInput onSendMessage={handleSendMessage} disabled={!isConnected || isTyping} />
    </div>
  );
}
