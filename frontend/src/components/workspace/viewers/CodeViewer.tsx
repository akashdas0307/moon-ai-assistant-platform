import React from 'react';
import Editor from '@monaco-editor/react';

interface CodeViewerProps {
  content: string;
  language: string;
  path: string;
}

export const CodeViewer: React.FC<CodeViewerProps> = ({ content, language }) => {
  return (
    <Editor
      height="100%"
      language={language}
      value={content}
      theme="vs-dark"
      options={{
        readOnly: true,
        minimap: { enabled: false },
        fontSize: 14,
        lineNumbers: 'on',
        scrollBeyondLastLine: false,
        automaticLayout: true
      }}
    />
  );
};
