import { useState, useEffect } from 'react';
import { MainLayout } from './components/layout/MainLayout';
import { Header } from './components/layout/Header';
import { ChatPanel } from './components/chat/ChatPanel';
import { WorkspacePanel } from './components/workspace/WorkspacePanel';
import { Toast } from './components/common/Toast';

function App() {
  const [chatVisible, setChatVisible] = useState(true);
  const [workspaceVisible, setWorkspaceVisible] = useState(true);

  // Responsive: One panel at a time on mobile/tablet
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth < 1024) {
        // Tablet/Mobile: Ensure only one is visible if both were active
        if (chatVisible && workspaceVisible) {
           setChatVisible(false); // Default to workspace being main view
        }
      }
    };

    // Run initially to set correct state
    handleResize();

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [chatVisible, workspaceVisible]);

  const handleToggleChat = () => {
    if (window.innerWidth < 1024) {
       // Mobile/Tablet: Switch to Chat exclusively
       setChatVisible(true);
       setWorkspaceVisible(false);
    } else {
       // Desktop: Toggle
       if (!chatVisible) {
         setChatVisible(true);
       } else {
         // Prevent hiding both - only hide if workspace is visible
         if (workspaceVisible) {
           setChatVisible(false);
         }
       }
    }
  };

  const handleToggleWorkspace = () => {
    if (window.innerWidth < 1024) {
       // Mobile/Tablet: Switch to Workspace exclusively
       setWorkspaceVisible(true);
       setChatVisible(false);
    } else {
       // Desktop: Toggle
       if (!workspaceVisible) {
         setWorkspaceVisible(true);
       } else {
         // Prevent hiding both - only hide if chat is visible
         if (chatVisible) {
           setWorkspaceVisible(false);
         }
       }
    }
  };

  return (
    <div className="flex flex-col h-screen bg-[#1a1a1a] overflow-hidden text-white relative">
      <Toast />
      <Header
        onToggleChatPanel={handleToggleChat}
        onToggleWorkspacePanel={handleToggleWorkspace}
        chatPanelVisible={chatVisible}
        workspacePanelVisible={workspaceVisible}
      />
      <MainLayout
        chatPanel={<ChatPanel />}
        workspacePanel={<WorkspacePanel visible={workspaceVisible} />}
        chatVisible={chatVisible}
        workspaceVisible={workspaceVisible}
      />
    </div>
  );
}

export default App;
