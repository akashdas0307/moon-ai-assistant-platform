import React from 'react';
import { MessageSquare, Folder } from 'lucide-react';
import { StatusIndicator } from '../StatusIndicator';

interface HeaderProps {
  onToggleChatPanel: () => void;
  onToggleWorkspacePanel: () => void;
  chatPanelVisible: boolean;
  workspacePanelVisible: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  onToggleChatPanel,
  onToggleWorkspacePanel,
  chatPanelVisible,
  workspacePanelVisible,
}) => {
  return (
    <header className="h-[60px] bg-[#1a1a1a] border-b border-[#404040] flex items-center justify-between px-4 flex-none">
      {/* Left: Title */}
      <div className="flex items-center gap-4">
        <h1 className="text-xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent select-none">
          Moon AI
        </h1>
        <div className="hidden md:block">
           <StatusIndicator />
        </div>
      </div>

      {/* Right: Toggles */}
      <div className="flex items-center gap-2">
        <button
          onClick={onToggleChatPanel}
          className={`p-2 rounded-md transition-colors ${
            chatPanelVisible ? 'bg-blue-600/20 text-blue-400' : 'text-gray-400 hover:bg-gray-800 hover:text-gray-200'
          }`}
          title={chatPanelVisible ? "Hide Chat" : "Show Chat"}
        >
          <MessageSquare size={20} />
        </button>
        <button
          onClick={onToggleWorkspacePanel}
          className={`p-2 rounded-md transition-colors ${
            workspacePanelVisible ? 'bg-blue-600/20 text-blue-400' : 'text-gray-400 hover:bg-gray-800 hover:text-gray-200'
          }`}
          title={workspacePanelVisible ? "Hide Workspace" : "Show Workspace"}
        >
          <Folder size={20} />
        </button>
      </div>
    </header>
  );
};
