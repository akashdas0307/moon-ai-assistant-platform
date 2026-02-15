import { StatusIndicator } from './components/StatusIndicator';
import { ChatPanel } from './components/chat/ChatPanel';

function App() {
  return (
    <div className="min-h-screen bg-gray-900 text-white flex flex-col">
      {/* Header */}
      <header className="border-b border-gray-800 px-6 py-4 flex-none">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
            Moon AI
          </h1>
          <StatusIndicator />
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-6 py-8 flex-1 flex flex-col items-center justify-center">
        <ChatPanel />
      </main>
    </div>
  );
}

export default App;
