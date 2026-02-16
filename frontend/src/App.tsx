import { StatusIndicator } from './components/StatusIndicator';
import { ChatPanel } from './components/chat/ChatPanel';
import { FileBrowser } from './components/workspace/FileBrowser';
import { FileViewer } from './components/workspace/FileViewer';

function App() {
  return (
    <div className="h-screen bg-gray-900 text-white flex flex-col overflow-hidden">
      {/* Header */}
      <header className="border-b border-gray-800 px-6 py-3 flex-none bg-[#1a1a1a]">
        <div className="flex items-center justify-between">
          <h1 className="text-xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
            Moon AI
          </h1>
          <StatusIndicator />
        </div>
      </header>

      {/* Main Content Area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar: File Browser */}
        <FileBrowser />

        {/* Workspace Area: File Viewer */}
        <main className="flex-1 flex flex-col min-w-0 bg-[#0f0f0f] border-r border-[#404040]">
           <FileViewer />
        </main>

        {/* Right Sidebar: Chat Area */}
        <aside className="w-96 flex-none bg-[#0f0f0f] border-l border-[#404040]">
           <div className="h-full flex flex-col">
              <ChatPanel />
           </div>
        </aside>
      </div>
    </div>
  );
}

export default App;
