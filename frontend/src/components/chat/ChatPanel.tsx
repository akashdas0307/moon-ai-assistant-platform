import { useState, useCallback, useEffect } from 'react';
import { Message } from '../../types/chat';
import { MessageList } from './MessageList';
import { MessageInput } from './MessageInput';
import { TypingIndicator } from './TypingIndicator';
import { useWebSocket } from '../../hooks/useWebSocket';
import { WEBSOCKET_URL } from '../../config/constants';
import { useMessageStore } from '../../stores/messageStore';

export function ChatPanel() {
  const { messages, addMessage, loadMessages, error } = useMessageStore();
  const [isTyping, setIsTyping] = useState(false);
  const [streamingMessages, setStreamingMessages] = useState<Map<string, Message>>(new Map());

  // Load messages on mount
  useEffect(() => {
    loadMessages();
  }, [loadMessages]);

  // Handle incoming WebSocket messages
  const handleWebSocketMessage = useCallback((message: Message) => {
    // Regular messages might still come through fallback or other events
    // Check if it's already in streaming messages (shouldn't happen if protocol is clean)
    // If we receive a full message that was streaming, remove from streaming
    setStreamingMessages(prev => {
      const map = new Map(prev);
      if (map.has(message.id)) {
        map.delete(message.id);
      }
      return map;
    });
    addMessage(message);
    setIsTyping(false);
  }, [addMessage]);

  const handleStreamStart = useCallback((messageId: string) => {
    setIsTyping(false); // Stop generic typing indicator
    const newMessage: Message = {
      id: messageId,
      sender: 'ai',
      content: '',
      timestamp: new Date(),
      isStreaming: true
    };
    setStreamingMessages(prev => new Map(prev).set(messageId, newMessage));
  }, []);

  const handleStreamToken = useCallback((messageId: string, token: string) => {
    setStreamingMessages(prev => {
      const map = new Map(prev);
      const msg = map.get(messageId);
      if (msg) {
        map.set(messageId, { ...msg, content: msg.content + token });
      }
      return map;
    });
  }, []);

  const handleStreamEnd = useCallback((messageId: string, fullContent: string) => {
    setStreamingMessages(prev => {
      const map = new Map(prev);
      const msg = map.get(messageId);
      if (msg) {
        // Add finalized message to store
        // Ensure we use the full content provided in stream_end to guarantee integrity
        // although msg.content should be same.
        addMessage({
          ...msg,
          content: fullContent || msg.content,
          isStreaming: false
        });
        map.delete(messageId);
      }
      return map;
    });
  }, [addMessage]);

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
    onStreamStart: handleStreamStart,
    onStreamToken: handleStreamToken,
    onStreamEnd: handleStreamEnd,
    onConnect: handleConnect,
    onDisconnect: handleDisconnect,
    onError: handleError,
    autoReconnect: true,
    reconnectInterval: 3000
  });

  const handleSendMessage = (content: string) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      sender: 'user',
      content,
      timestamp: new Date()
    };
    addMessage(userMessage);
    setIsTyping(true);
    sendWebSocketMessage(content);
  };

  // Combine store messages with currently streaming messages
  // Filter out any streaming messages that have already been added to the store to prevent duplicate keys
  const displayMessages = [
    ...messages,
    ...Array.from(streamingMessages.values()).filter(
      streamMsg => !messages.some(msg => msg.id === streamMsg.id)
    )
  ];

  return (
    <div className="flex flex-col h-full w-full bg-[#111827] text-white overflow-hidden shadow-2xl border border-gray-800 rounded-xl">
      {/* Header */}
      <div className="flex-none bg-[#111827]/95 backdrop-blur border-b border-gray-800 p-4 flex items-center justify-between z-20">
        <div className="flex items-center gap-3">
          <div className="relative w-10 h-10 rounded-xl bg-gradient-to-br from-blue-600 to-purple-600 flex items-center justify-center shadow-lg shadow-blue-500/20 ring-1 ring-white/10">
            <svg xmlns="http://www.w3.org/2000/svg" className="w-6 h-6 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
            </svg>
            <div className={`absolute -bottom-1 -right-1 w-3.5 h-3.5 border-2 border-[#111827] rounded-full transition-colors duration-300 ${isConnected ? 'bg-green-500' : (connectionError ? 'bg-red-500' : 'bg-yellow-500 animate-pulse')}`}></div>
          </div>
          <div>
            <h2 className="text-lg font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">
              Moon AI
            </h2>
            <div className="flex items-center gap-1.5">
              <span className={`w-1.5 h-1.5 rounded-full transition-colors duration-300 ${isConnected ? 'bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.5)]' : (connectionError ? 'bg-red-500' : 'bg-yellow-500')}`}></span>
              <span className="text-xs text-gray-400 font-medium transition-opacity duration-300">
                {isConnected ? 'Online' : (connectionError ? 'Disconnected' : 'Connecting...')}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Error Banner */}
      {(error || connectionError) && (
         <div className="flex-none bg-red-500/10 border-b border-red-500/20 px-4 py-2 text-red-400 text-sm flex items-center gap-2 animate-fade-in">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 flex-shrink-0" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
            <span>{error || connectionError}</span>
         </div>
      )}

      {/* Message List Area */}
      <div className="flex-1 min-h-0 relative bg-gradient-to-b from-gray-900 to-[#111827]">
        <MessageList messages={displayMessages} />

        {/* Typing Indicator Overlay */}
        <div className={`absolute bottom-4 left-6 transition-all duration-300 transform ${isTyping && streamingMessages.size === 0 ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4 pointer-events-none'}`}>
           <TypingIndicator isTyping={isTyping && streamingMessages.size === 0} />
        </div>
      </div>

      {/* Input Area */}
      <div className="flex-none z-20 bg-[#111827]">
        <MessageInput onSendMessage={handleSendMessage} disabled={!isConnected || isTyping || streamingMessages.size > 0} />
      </div>
    </div>
  );
}
