import { StatusIndicator } from './components/StatusIndicator';
import { ChatPanel } from './components/chat/ChatPanel';
import { FileBrowser } from './components/workspace/FileBrowser';

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
        {/* Sidebar */}
        <aside className="w-64 flex-none border-r border-gray-800 bg-[#1a1a1a]">
          <FileBrowser />
        </aside>

        {/* Chat Area */}
        <main className="flex-1 flex flex-col min-w-0 bg-[#0f0f0f]">
          <div className="flex-1 p-4 overflow-hidden flex flex-col">
            <ChatPanel />
          </div>
        </main>
      </div>
    </div>
  );
}

export default App;
