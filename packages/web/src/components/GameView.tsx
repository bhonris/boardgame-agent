import { useCallback } from 'react'
import { useGameStore } from '../stores/gameStore'
import { TutorialEngine } from './TutorialEngine'
import { ChatInterface } from './ChatInterface'
import { CameraCapture } from './CameraCapture'
import { QuickReference } from './QuickReference'
import { SetupChecklist } from './SetupChecklist'
import { VoiceInterface } from './VoiceInterface'
import { RealtimeMode } from './RealtimeMode'

const TABS = [
  { key: 'tutorial' as const, label: 'Tutorial' },
  { key: 'chat' as const, label: 'Q&A' },
  { key: 'camera' as const, label: 'Camera' },
  { key: 'reference' as const, label: 'Reference' },
  { key: 'realtime' as const, label: 'Realtime' },
] as const

export function GameView() {
  const game = useGameStore((s) => s.selectedGame)
  const setSelectedGame = useGameStore((s) => s.setSelectedGame)
  const activeTab = useGameStore((s) => s.activeTab)
  const setActiveTab = useGameStore((s) => s.setActiveTab)
  const messages = useGameStore((s) => s.messages)
  const addMessage = useGameStore((s) => s.addMessage)

  const lastAssistantMsg = [...messages].reverse().find((m) => m.role === 'assistant')?.content

  const handleVoiceTranscript = useCallback((text: string) => {
    setActiveTab('chat')
    // Add user message from voice and trigger the chat
    addMessage({
      id: crypto.randomUUID(),
      role: 'user',
      content: text,
    })
  }, [setActiveTab, addMessage])

  if (!game) return null

  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSelectedGame(null)}
              className="text-gray-400 hover:text-gray-600 transition-colors p-2 min-w-[48px] min-h-[48px] flex items-center justify-center"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="m15 18-6-6 6-6" />
              </svg>
            </button>
            <h1 className="text-lg font-semibold text-gray-900">{game.title}</h1>
          </div>
          {activeTab !== 'realtime' && (
            <VoiceInterface
              onTranscript={handleVoiceTranscript}
              lastAssistantMessage={lastAssistantMsg}
            />
          )}
        </div>

        <nav className="max-w-6xl mx-auto px-4 flex gap-1">
          {TABS.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`px-4 py-2.5 text-sm font-medium transition-colors border-b-2 min-h-[48px] ${
                activeTab === tab.key
                  ? 'border-indigo-500 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </header>

      <main className="flex-1 px-4 py-6">
        {activeTab === 'tutorial' && (
          <div className="space-y-6">
            <TutorialEngine />
            <div className="max-w-3xl mx-auto">
              <SetupChecklist gameId={game.id} />
            </div>
          </div>
        )}
        {activeTab === 'chat' && (
          <div className="h-[calc(100vh-200px)]">
            <ChatInterface />
          </div>
        )}
        {activeTab === 'camera' && <CameraCapture />}
        {activeTab === 'reference' && <QuickReference />}
        {activeTab === 'realtime' && <RealtimeMode />}
      </main>
    </div>
  )
}
