import React, { useState, useEffect } from 'react';
import { Panel, Group as PanelGroup, Separator as PanelResizeHandle } from 'react-resizable-panels';

interface MainLayoutProps {
  chatPanel: React.ReactNode;
  workspacePanel: React.ReactNode;
  chatVisible: boolean;
  workspaceVisible: boolean;
}

export const MainLayout: React.FC<MainLayoutProps> = ({
  chatPanel,
  workspacePanel,
  chatVisible,
  workspaceVisible,
}) => {
  const [direction, setDirection] = useState<'horizontal' | 'vertical'>('horizontal');

  useEffect(() => {
    const handleResize = () => {
      setDirection(window.innerWidth < 768 ? 'vertical' : 'horizontal');
    };
    handleResize(); // Initial check
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const showBoth = chatVisible && workspaceVisible;

  return (
    <div className="flex-1 overflow-hidden h-full relative bg-[#1a1a1a]">
      <PanelGroup direction={direction} className="h-full w-full">
        {chatVisible && (
          <Panel defaultSize={40} minSize={30} order={1} id="chat-panel">
            <div className="h-full w-full overflow-hidden">
               {chatPanel}
            </div>
          </Panel>
        )}

        {showBoth && (
          <PanelResizeHandle
            className={`flex-none bg-[#404040] transition-all hover:bg-[#4a90e2] z-50
              ${direction === 'horizontal'
                ? 'w-[1px] hover:w-[2px] cursor-col-resize h-full'
                : 'h-[1px] hover:h-[2px] cursor-row-resize w-full'
              }
            `}
          />
        )}

        {workspaceVisible && (
          <Panel defaultSize={60} minSize={30} order={2} id="workspace-panel">
            <div className="h-full w-full overflow-hidden">
               {workspacePanel}
            </div>
          </Panel>
        )}
      </PanelGroup>
    </div>
  );
};
