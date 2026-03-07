import { useQuery } from '@tanstack/react-query'
import { fetchGames } from '../api/client'
import { useGameStore } from '../stores/gameStore'
import type { Game } from '../types/game'

function GameCard({ game, onSelect }: { game: Game; onSelect: (game: Game) => void }) {
  return (
    <button
      onClick={() => onSelect(game)}
      className="bg-white rounded-xl shadow-md hover:shadow-lg transition-shadow p-4 text-left cursor-pointer border border-gray-100 hover:border-indigo-300 min-h-[200px] flex flex-col"
    >
      <div className="w-full h-40 bg-gradient-to-br from-indigo-100 to-purple-100 rounded-lg mb-3 flex items-center justify-center">
        <span className="text-4xl font-bold text-indigo-300">{game.title[0]}</span>
      </div>
      <h3 className="text-lg font-semibold text-gray-900 mb-1">{game.title}</h3>
      <p className="text-sm text-gray-500 flex-1 line-clamp-2">{game.description}</p>
      <div className="flex gap-3 mt-3 text-xs text-gray-400">
        <span>{game.minPlayers}-{game.maxPlayers} players</span>
        {game.playTimeMinutes && <span>{game.playTimeMinutes} min</span>}
        {game.complexityWeight && <span>Complexity: {game.complexityWeight}/5</span>}
      </div>
    </button>
  )
}

export function GameSelection() {
  const setSelectedGame = useGameStore((s) => s.setSelectedGame)
  const { data: games, isLoading, error } = useQuery({
    queryKey: ['games'],
    queryFn: fetchGames,
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-pulse text-gray-400 text-lg">Loading games...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-red-500 text-center">
          <p className="text-lg font-semibold">Unable to load games</p>
          <p className="text-sm mt-1">Please make sure the server is running.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <div className="text-center mb-10">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Choose a Game to Learn</h1>
        <p className="text-gray-500">Pick a game and I'll teach you how to play, step by step.</p>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {games?.map((game) => (
          <GameCard key={game.id} game={game} onSelect={setSelectedGame} />
        ))}
      </div>
      {games?.length === 0 && (
        <p className="text-center text-gray-400 mt-10">No games available yet.</p>
      )}
    </div>
  )
}
