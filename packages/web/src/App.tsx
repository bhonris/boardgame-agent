import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useGameStore } from './stores/gameStore'
import { GameSelection } from './components/GameSelection'
import { GameView } from './components/GameView'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,
      retry: 1,
    },
  },
})

function AppContent() {
  const selectedGame = useGameStore((s) => s.selectedGame)

  if (selectedGame) {
    return <GameView />
  }

  return <GameSelection />
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppContent />
    </QueryClientProvider>
  )
}
