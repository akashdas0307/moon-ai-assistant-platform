import { create } from 'zustand';
import { Message } from '../types/chat';
import { apiClient, MessageResponse } from '../services/apiClient';

interface MessageState {
  messages: Message[];
  isLoading: boolean;
  error: string | null;
  loadMessages: () => Promise<void>;
  addMessage: (message: Message) => void;
  setMessages: (messages: Message[]) => void;
}

export const useMessageStore = create<MessageState>((set) => ({
  messages: [],
  isLoading: false,
  error: null,

  loadMessages: async () => {
    set({ isLoading: true, error: null });
    try {
      const data: MessageResponse[] = await apiClient.getMessages(100);

      const messages: Message[] = data.map((msg) => ({
        id: msg.id.toString(),
        sender: msg.sender === 'assistant' ? 'ai' : 'user',
        content: msg.content,
        timestamp: new Date(msg.timestamp),
      }));

      set({ messages, isLoading: false });
    } catch (error: unknown) {
      console.error('Error loading messages:', error);
      set({
        error: (error as Error).message || 'Failed to load messages',
        isLoading: false
      });
    }
  },

  addMessage: (message) => set((state) => ({
    messages: [...state.messages, message]
  })),

  setMessages: (messages) => set({ messages }),
}));
