import React from 'react';
import { FileBrowser } from './FileBrowser';
import { FileViewer } from './FileViewer';

interface WorkspacePanelProps {
  visible?: boolean;
}

export const WorkspacePanel: React.FC<WorkspacePanelProps> = ({ visible = true }) => {
  if (!visible) return null;

  return (
    <div className="flex h-full w-full bg-[#1a1a1a] overflow-hidden">
      {/* File Browser Sidebar */}
      <div className="w-[260px] flex-none h-full">
        <FileBrowser />
      </div>

      {/* Main Workspace */}
      <div className="flex-1 min-w-0 h-full">
        <FileViewer />
      </div>
    </div>
  );
};
