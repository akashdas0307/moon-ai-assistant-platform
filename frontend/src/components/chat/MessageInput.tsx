import { useState, useRef, useEffect, FormEvent, KeyboardEvent } from 'react';
import { MessageInputProps } from '../../types/chat';

export function MessageInput({ onSendMessage, disabled }: MessageInputProps) {
  const [content, setContent] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = (e?: FormEvent) => {
    e?.preventDefault();
    if (content.trim() && !disabled) {
      onSendMessage(content);
      setContent('');
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  }, [content]);

  return (
    <form onSubmit={handleSubmit} className="p-4 border-t border-gray-800 bg-gray-900">
      <div className="flex items-end gap-2 bg-gray-800 rounded-lg p-2 border border-gray-700 focus-within:border-blue-500 transition-colors">
        <textarea
          ref={textareaRef}
          value={content}
          onChange={(e) => setContent(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          placeholder="Type a message..."
          className="w-full bg-transparent text-gray-100 placeholder-gray-500 resize-none outline-none max-h-[120px] min-h-[24px] py-1 px-2"
          rows={1}
        />
        <button
          type="submit"
          disabled={!content.trim() || disabled}
          className="p-2 text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          title="Send message"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="currentColor"
            className="w-5 h-5 transform rotate-0"
          >
            <path d="M3.478 2.405a.75.75 0 00-.926.94l2.432 7.905H13.5a.75.75 0 010 1.5H4.984l-2.432 7.905a.75.75 0 00.926.94 60.519 60.519 0 0018.445-8.986.75.75 0 000-1.218A60.517 60.517 0 003.478 2.405z" />
          </svg>
        </button>
      </div>
    </form>
  );
}
