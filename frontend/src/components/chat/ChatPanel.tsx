import { useState } from 'react';
import { Message } from '../../types/chat';
import { MessageList } from './MessageList';
import { MessageInput } from './MessageInput';
import { TypingIndicator } from './TypingIndicator';

const mockMessages: Message[] = [
  {
    id: '1',
    sender: 'ai',
    content: "Hello! I'm Moon-AI. How can I help you today?",
    timestamp: new Date(Date.now() - 60000)
  },
  {
    id: '2',
    sender: 'user',
    content: "Hi! Can you help me with this project?",
    timestamp: new Date(Date.now() - 30000)
  },
  {
    id: '3',
    sender: 'ai',
    content: "Of course! I'd be happy to help with your project. What would you like to know?",
    timestamp: new Date()
  }
];

export function ChatPanel() {
  const [messages, setMessages] = useState<Message[]>(mockMessages);
  const [isTyping, setIsTyping] = useState(false);

  const handleSendMessage = (content: string) => {
    // Add user message
    const newMessage: Message = {
      id: Date.now().toString(),
      sender: 'user',
      content,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, newMessage]);
    setIsTyping(true);

    // Simulate AI response
    setTimeout(() => {
      setIsTyping(false);
      const aiResponse: Message = {
        id: (Date.now() + 1).toString(),
        sender: 'ai',
        content: "I'm just a visual demo for now, but soon I'll be connected to the real backend!",
        timestamp: new Date()
      };
      setMessages(prev => [...prev, aiResponse]);
    }, 2000);
  };

  return (
    <div className="flex flex-col h-[600px] w-full max-w-4xl mx-auto bg-gray-800 rounded-xl overflow-hidden shadow-2xl border border-gray-700">
      <div className="bg-gray-900 p-4 border-b border-gray-700 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-white flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-green-500"></span>
          Moon AI Chat
        </h2>
      </div>

      <MessageList messages={messages} />

      <div className="px-4 pb-2 bg-gray-900">
        <TypingIndicator isTyping={isTyping} />
      </div>

      <MessageInput onSendMessage={handleSendMessage} disabled={isTyping} />
    </div>
  );
}
