import React from 'react';

interface TextViewerProps {
  content: string;
  path: string;
}

export const TextViewer: React.FC<TextViewerProps> = ({ content }) => {
  return (
    <div className="p-4 h-full overflow-auto bg-[#1a1a1a] text-white font-mono text-sm">
      <pre className="whitespace-pre-wrap">{content}</pre>
    </div>
  );
};
