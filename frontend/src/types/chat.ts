export interface Message {
  id: string;
  sender: 'user' | 'ai';
  content: string;
  timestamp: Date;
}

export interface MessageInputProps {
  onSendMessage: (content: string) => void;
  disabled?: boolean;
}
