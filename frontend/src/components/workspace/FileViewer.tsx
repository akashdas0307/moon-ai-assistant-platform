import React from 'react';
import { Loader2, FileX } from 'lucide-react';
import { useWorkspaceStore } from '../../stores/workspaceStore';
import { FileViewerTabs } from './FileViewerTabs';
import { CodeViewer } from './viewers/CodeViewer';
import { MarkdownViewer } from './viewers/MarkdownViewer';
import { ImageViewer } from './viewers/ImageViewer';
import { TextViewer } from './viewers/TextViewer';
import { getLanguageFromExtension } from '../../utils/fileTypes';

export const FileViewer: React.FC = () => {
  const { activeFilePath, openFiles } = useWorkspaceStore();
  const activeFile = openFiles.find(f => f.path === activeFilePath);

  const renderContent = () => {
    if (!activeFile) {
      return (
        <div className="flex flex-col items-center justify-center h-full text-gray-500">
          <FileX size={48} className="mb-4 opacity-50" />
          <p>No file open</p>
          <p className="text-sm mt-2">Select a file from the workspace to view it</p>
        </div>
      );
    }

    if (activeFile.loading) {
      return (
        <div className="flex items-center justify-center h-full text-gray-400">
          <Loader2 size={32} className="animate-spin mb-2" />
          <span className="ml-2">Loading content...</span>
        </div>
      );
    }

    if (activeFile.error) {
      return (
        <div className="flex flex-col items-center justify-center h-full text-red-400 p-8 text-center">
          <FileX size={48} className="mb-4" />
          <h3 className="text-lg font-semibold mb-2">Failed to load file</h3>
          <p className="text-sm text-gray-400">{activeFile.error}</p>
        </div>
      );
    }

    switch (activeFile.type) {
      case 'code':
        return (
          <CodeViewer
            content={activeFile.content}
            language={getLanguageFromExtension(activeFile.name)}
            path={activeFile.path}
          />
        );
      case 'markdown':
        return <MarkdownViewer content={activeFile.content} path={activeFile.path} />;
      case 'image':
        return <ImageViewer path={activeFile.path} name={activeFile.name} />;
      case 'text':
      default:
        return <TextViewer content={activeFile.content} path={activeFile.path} />;
    }
  };

  return (
    <div className="flex flex-col h-full bg-[#1e1e1e] overflow-hidden">
      <FileViewerTabs />
      <div className="flex-1 overflow-hidden relative">
        {renderContent()}
      </div>
    </div>
  );
};
