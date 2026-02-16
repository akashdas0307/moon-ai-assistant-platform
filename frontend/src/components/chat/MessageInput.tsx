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

      // Reset height and refocus input
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
        // Refocus after a brief delay to ensure state updates
        setTimeout(() => {
          textareaRef.current?.focus();
        }, 10);
      }
    }
  };

  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  // Global shortcut Ctrl/Cmd+K to focus
  useEffect(() => {
    const handleGlobalKeyDown = (e: globalThis.KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        textareaRef.current?.focus();
      }
    };

    window.addEventListener('keydown', handleGlobalKeyDown);
    return () => window.removeEventListener('keydown', handleGlobalKeyDown);
  }, []);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  }, [content]);

  return (
    <form onSubmit={handleSubmit} className="p-4 bg-gray-900 border-t border-gray-800">
      <div
        className="relative flex items-end gap-2 bg-[#374151] rounded-xl p-3 border border-gray-600 focus-within:border-blue-500 focus-within:ring-2 focus-within:ring-blue-500/20 transition-all duration-200 shadow-inner"
      >
        <textarea
          ref={textareaRef}
          value={content}
          onChange={(e) => setContent(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          placeholder="Type a message..."
          className="w-full bg-transparent text-gray-100 placeholder-gray-400 resize-none outline-none max-h-[120px] min-h-[24px] py-1 px-2 font-sans"
          rows={1}
        />
        <div className="flex items-center pb-1">
          <button
            type="submit"
            disabled={!content.trim() || disabled}
            className={`
              p-2 rounded-lg transition-all duration-200
              ${!content.trim() || disabled
                ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                : 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg shadow-blue-500/30 hover:shadow-blue-500/50 hover:scale-105 active:scale-95'
              }
            `}
            title="Send message (Enter)"
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
      </div>
      <div className="text-center mt-2 flex justify-between items-center px-2">
         <span className="text-xs text-gray-500 hidden md:inline-block">
            <kbd className="font-mono bg-gray-800 px-1 rounded border border-gray-700 text-gray-400">⌘K</kbd> to focus
         </span>
         <span className="text-xs text-gray-500">
            <kbd className="font-mono bg-gray-800 px-1 rounded border border-gray-700 text-gray-400">Enter</kbd> to send, <kbd className="font-mono bg-gray-800 px-1 rounded border border-gray-700 text-gray-400">Shift + Enter</kbd> for new line
         </span>
      </div>
    </form>
  );
}
