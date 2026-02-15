import { Message } from '../../types/chat';

interface MessageBubbleProps {
  message: Message;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.sender === 'user';

  return (
    <div className={`flex w-full mb-4 ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`
          max-w-[80%] rounded-lg p-3 relative
          ${isUser
            ? 'bg-blue-600 text-white rounded-br-none'
            : 'bg-gray-700 text-gray-100 rounded-bl-none'
          }
        `}
      >
        <div className="whitespace-pre-wrap break-words text-sm md:text-base">
          {message.content}
        </div>
        <div
          className={`
            text-xs mt-1
            ${isUser ? 'text-blue-200' : 'text-gray-400'}
            text-right
          `}
        >
          {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </div>
      </div>
    </div>
  );
}
