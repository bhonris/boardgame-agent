import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { GameView } from '../GameView'
import { useGameStore } from '../../stores/gameStore'
import { vi } from 'vitest'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

// Mock child components to isolate GameView behavior
vi.mock('../TutorialEngine', () => ({
  TutorialEngine: () => <div data-testid="tutorial-engine">Tutorial</div>,
}))
vi.mock('../ChatInterface', () => ({
  ChatInterface: () => <div data-testid="chat-interface">Chat</div>,
}))
vi.mock('../CameraCapture', () => ({
  CameraCapture: () => <div data-testid="camera-capture">Camera</div>,
}))
vi.mock('../QuickReference', () => ({
  QuickReference: () => <div data-testid="quick-reference">Reference</div>,
}))
vi.mock('../SetupChecklist', () => ({
  SetupChecklist: () => <div data-testid="setup-checklist">Setup</div>,
}))
vi.mock('../RealtimeMode', () => ({
  RealtimeMode: () => <div data-testid="realtime-mode">Realtime</div>,
}))
vi.mock('../VoiceInterface', () => ({
  VoiceInterface: ({ onTranscript }: { onTranscript: (t: string) => void }) => (
    <button data-testid="voice-interface" title="Hold to talk" onClick={() => onTranscript('test')}>
      Voice
    </button>
  ),
}))

function renderWithQuery(ui: React.ReactElement) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>)
}

describe('GameView', () => {
  beforeEach(() => {
    useGameStore.setState({
      selectedGame: {
        id: 'catan',
        title: 'Catan',
        coverImageUrl: null,
        minPlayers: 3,
        maxPlayers: 4,
        complexityWeight: 2.3,
        playTimeMinutes: 90,
        description: 'Test',
      },
      sessionId: null,
      messages: [],
      activeTab: 'tutorial',
    })
  })

  it('hides VoiceInterface when Realtime tab is active (regression: mic conflict)', async () => {
    renderWithQuery(<GameView />)

    // VoiceInterface should be visible on default tab (tutorial)
    expect(screen.getByTestId('voice-interface')).toBeInTheDocument()

    // Switch to Realtime tab
    await userEvent.click(screen.getByRole('button', { name: 'Realtime' }))

    // VoiceInterface should be hidden to prevent mic conflict
    expect(screen.queryByTestId('voice-interface')).not.toBeInTheDocument()
    // Realtime component should be rendered
    expect(screen.getByTestId('realtime-mode')).toBeInTheDocument()
  })

  it('shows VoiceInterface on non-realtime tabs', async () => {
    renderWithQuery(<GameView />)

    const tabs = ['Tutorial', 'Q&A', 'Camera', 'Reference']
    for (const tab of tabs) {
      await userEvent.click(screen.getByRole('button', { name: tab }))
      expect(screen.getByTestId('voice-interface')).toBeInTheDocument()
    }
  })
})
