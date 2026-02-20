export interface Message {
  id: string;
  sender: 'user' | 'ai';
  content: string;
  timestamp: Date;
  isStreaming?: boolean;
  com_id?: string;
}

export interface MessageInputProps {
  onSendMessage: (content: string) => void;
  disabled?: boolean;
}
