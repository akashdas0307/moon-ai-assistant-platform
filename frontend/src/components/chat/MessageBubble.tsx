import { useState, ComponentPropsWithoutRef } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Message } from '../../types/chat';
import { colors } from '../../styles/tokens';
import { formatTimestamp } from '../../utils/formatters';

interface MessageBubbleProps {
  message: Message;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.sender === 'user';

  // Custom renderer for code blocks
  const CodeBlock = ({ inline, className, children, ...props }: ComponentPropsWithoutRef<'code'> & { inline?: boolean }) => {
    const match = /language-(\w+)/.exec(className || '');
    const codeString = String(children).replace(/\n$/, '');
    const [copied, setCopied] = useState(false);

    const handleCopy = () => {
      navigator.clipboard.writeText(codeString);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    };

    if (!inline && match) {
      return (
        <div className="relative my-4 rounded-lg overflow-hidden border border-gray-700">
          <div className="flex items-center justify-between px-4 py-2 bg-gray-900 border-b border-gray-700">
            <span className="text-xs text-gray-400 font-mono">{match[1]}</span>
            <button
              onClick={handleCopy}
              className="text-xs text-gray-400 hover:text-white transition-colors flex items-center gap-1"
            >
              {copied ? (
                <>
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 text-green-500" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                  <span className="text-green-500">Copied!</span>
                </>
              ) : (
                <>
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                  Copy
                </>
              )}
            </button>
          </div>
          <SyntaxHighlighter
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            style={vscDarkPlus as any}
            language={match[1]}
            PreTag="div"
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            customStyle={{ margin: 0, padding: '1rem', background: '#1F2937' } as any}
            {...props}
          >
            {codeString}
          </SyntaxHighlighter>
        </div>
      );
    }

    return (
      <code className={`${className} bg-gray-800 text-gray-200 rounded px-1.5 py-0.5 font-mono text-sm border border-gray-700`} {...props}>
        {children}
      </code>
    );
  };

  return (
    <div className={`flex w-full mb-6 ${isUser ? 'justify-end' : 'justify-start'} animate-message-entrance`}>
      <div className={`flex flex-col max-w-[85%] md:max-w-[75%] ${isUser ? 'items-end' : 'items-start'}`}>
        <div
          className={`
            relative px-5 py-4 rounded-2xl shadow-sm
            ${isUser
              ? 'rounded-br-sm text-white'
              : 'rounded-bl-sm text-gray-100 bg-gray-800 border border-gray-700'
            }
          `}
          style={isUser ? {
            background: `linear-gradient(135deg, ${colors.accent.blue}, ${colors.accent.purple})`,
          } : {
            backgroundColor: colors.background.card,
          }}
        >
          {isUser ? (
            <div className="whitespace-pre-wrap break-words text-[15px] leading-relaxed">
              {message.content}
            </div>
          ) : (
            <div className="markdown-content text-[15px] leading-relaxed overflow-hidden">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  code: CodeBlock,
                  p: ({ children }) => <p className="mb-3 last:mb-0">{children}</p>,
                  ul: ({ children }) => <ul className="list-disc pl-5 mb-3 space-y-1">{children}</ul>,
                  ol: ({ children }) => <ol className="list-decimal pl-5 mb-3 space-y-1">{children}</ol>,
                  li: ({ children }) => <li className="pl-1">{children}</li>,
                  blockquote: ({ children }) => (
                    <blockquote className="border-l-4 border-gray-600 pl-4 py-1 italic my-3 text-gray-400 bg-gray-800/50 rounded-r">
                      {children}
                    </blockquote>
                  ),
                  a: ({ href, children }) => (
                    <a
                      href={href}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-400 hover:text-blue-300 underline underline-offset-2 transition-colors"
                    >
                      {children}
                    </a>
                  ),
                  h1: ({ children }) => <h1 className="text-2xl font-bold mb-3 mt-4 first:mt-0 border-b border-gray-700 pb-2">{children}</h1>,
                  h2: ({ children }) => <h2 className="text-xl font-bold mb-2 mt-3 first:mt-0">{children}</h2>,
                  h3: ({ children }) => <h3 className="text-lg font-bold mb-2 mt-3 first:mt-0">{children}</h3>,
                  table: ({ children }) => (
                    <div className="overflow-x-auto my-4 border border-gray-700 rounded-lg">
                      <table className="min-w-full divide-y divide-gray-700 bg-gray-900/50">
                        {children}
                      </table>
                    </div>
                  ),
                  thead: ({ children }) => <thead className="bg-gray-800">{children}</thead>,
                  tbody: ({ children }) => <tbody className="divide-y divide-gray-700">{children}</tbody>,
                  tr: ({ children }) => <tr className="hover:bg-gray-800/50 transition-colors">{children}</tr>,
                  th: ({ children }) => <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">{children}</th>,
                  td: ({ children }) => <td className="px-4 py-3 text-sm text-gray-300 whitespace-nowrap">{children}</td>,
                  hr: () => <hr className="my-4 border-gray-700" />,
                }}
              >
                {message.content}
              </ReactMarkdown>
            </div>
          )}
        </div>

        <span className={`
          text-xs mt-1.5 px-1 font-medium
          ${isUser ? 'text-gray-400' : 'text-gray-500'}
        `}>
          {formatTimestamp(message.timestamp)}
        </span>
      </div>
    </div>
  );
}
