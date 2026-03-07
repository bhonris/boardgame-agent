import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { GameSelection } from '../GameSelection'
import { useGameStore } from '../../stores/gameStore'
import { vi } from 'vitest'
import type { Game } from '../../types/game'

const mockGames: Game[] = [
  {
    id: 'catan',
    title: 'Catan',
    coverImageUrl: '/images/catan.jpg',
    minPlayers: 3,
    maxPlayers: 4,
    complexityWeight: 2.3,
    playTimeMinutes: 90,
    description: 'Trade and build on Catan.',
  },
  {
    id: 'ticket-to-ride',
    title: 'Ticket to Ride',
    coverImageUrl: null,
    minPlayers: 2,
    maxPlayers: 5,
    complexityWeight: 1.9,
    playTimeMinutes: 60,
    description: 'Build train routes.',
  },
]

vi.mock('../../api/client', () => ({
  fetchGames: vi.fn(),
}))

import { fetchGames } from '../../api/client'

function renderWithProviders(ui: React.ReactNode) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>
  )
}

describe('GameSelection', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    useGameStore.setState({ selectedGame: null })
  })

  it('shows loading state', () => {
    vi.mocked(fetchGames).mockReturnValue(new Promise(() => {}))
    renderWithProviders(<GameSelection />)
    expect(screen.getByText('Loading games...')).toBeInTheDocument()
  })

  it('renders games after loading', async () => {
    vi.mocked(fetchGames).mockResolvedValue(mockGames)
    renderWithProviders(<GameSelection />)

    await waitFor(() => {
      expect(screen.getByText('Catan')).toBeInTheDocument()
    })
    expect(screen.getByText('Ticket to Ride')).toBeInTheDocument()
    expect(screen.getByText('3-4 players')).toBeInTheDocument()
  })

  it('shows error state', async () => {
    vi.mocked(fetchGames).mockRejectedValue(new Error('Network error'))
    renderWithProviders(<GameSelection />)

    await waitFor(() => {
      expect(screen.getByText('Unable to load games')).toBeInTheDocument()
    })
  })

  it('selects a game on click', async () => {
    vi.mocked(fetchGames).mockResolvedValue(mockGames)
    renderWithProviders(<GameSelection />)

    await waitFor(() => {
      expect(screen.getByText('Catan')).toBeInTheDocument()
    })

    await userEvent.click(screen.getByText('Catan'))
    expect(useGameStore.getState().selectedGame?.id).toBe('catan')
  })

  it('shows empty state when no games', async () => {
    vi.mocked(fetchGames).mockResolvedValue([])
    renderWithProviders(<GameSelection />)

    await waitFor(() => {
      expect(screen.getByText('No games available yet.')).toBeInTheDocument()
    })
  })
})
