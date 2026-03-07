import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { TutorialEngine } from '../TutorialEngine'
import { useGameStore } from '../../stores/gameStore'
import { vi } from 'vitest'
import type { TutorialData } from '../../types/game'

const mockTutorial: TutorialData = {
  gameId: 'catan',
  steps: [
    { id: 1, phase: 'theme_and_goal', title: 'What is Catan?', content: 'You are settlers...', estimatedSeconds: 30 },
    { id: 2, phase: 'components', title: 'Components', content: 'Here are the pieces...', estimatedSeconds: 60 },
    { id: 3, phase: 'setup', title: 'Setup', content: 'Set up the board...', estimatedSeconds: 90 },
  ],
  totalSteps: 3,
  estimatedMinutes: 3,
}

vi.mock('../../api/client', () => ({
  fetchTutorial: vi.fn(),
}))

import { fetchTutorial } from '../../api/client'

function renderWithProviders(ui: React.ReactNode) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>
  )
}

describe('TutorialEngine', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    useGameStore.setState({
      selectedGame: { id: 'catan', title: 'Catan', coverImageUrl: null, minPlayers: 3, maxPlayers: 4, complexityWeight: 2.3, playTimeMinutes: 90, description: 'Test' },
      currentTutorialStep: 0,
    })
  })

  it('shows loading state', () => {
    vi.mocked(fetchTutorial).mockReturnValue(new Promise(() => {}))
    renderWithProviders(<TutorialEngine />)
    expect(screen.getByText('Loading tutorial...')).toBeInTheDocument()
  })

  it('renders first step', async () => {
    vi.mocked(fetchTutorial).mockResolvedValue(mockTutorial)
    renderWithProviders(<TutorialEngine />)

    await waitFor(() => {
      expect(screen.getByText('What is Catan?')).toBeInTheDocument()
    })
    expect(screen.getByText('Step 1 of 3')).toBeInTheDocument()
  })

  it('navigates to next step', async () => {
    vi.mocked(fetchTutorial).mockResolvedValue(mockTutorial)
    renderWithProviders(<TutorialEngine />)

    await waitFor(() => {
      expect(screen.getByText('What is Catan?')).toBeInTheDocument()
    })

    await userEvent.click(screen.getByText('Next'))
    expect(screen.getByText('Components')).toBeInTheDocument()
    expect(screen.getByText('Step 2 of 3')).toBeInTheDocument()
  })

  it('disables Previous on first step', async () => {
    vi.mocked(fetchTutorial).mockResolvedValue(mockTutorial)
    renderWithProviders(<TutorialEngine />)

    await waitFor(() => {
      expect(screen.getByText('What is Catan?')).toBeInTheDocument()
    })

    expect(screen.getByText('Previous')).toBeDisabled()
  })

  it('disables Next on last step', async () => {
    useGameStore.setState({ currentTutorialStep: 2 })
    vi.mocked(fetchTutorial).mockResolvedValue(mockTutorial)
    renderWithProviders(<TutorialEngine />)

    await waitFor(() => {
      expect(screen.getByText('Setup')).toBeInTheDocument()
    })

    expect(screen.getByText('Next')).toBeDisabled()
  })
})
