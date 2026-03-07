import { useQuery } from '@tanstack/react-query'
import { fetchReference } from '../api/client'
import { useGameStore } from '../stores/gameStore'

export function QuickReference() {
  const game = useGameStore((s) => s.selectedGame)

  const { data, isLoading } = useQuery({
    queryKey: ['reference', game?.id],
    queryFn: () => fetchReference(game!.id),
    enabled: !!game,
  })

  if (isLoading || !data) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-pulse text-gray-400">Loading reference...</div>
      </div>
    )
  }

  const typeIcons: Record<string, string> = {
    turn_order: 'Turn Order',
    icons: 'Key Info',
    scoring: 'Scoring',
    setup: 'Setup',
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <h2 className="text-xl font-bold text-gray-900">Quick Reference - {game?.title}</h2>
      {data.references.map((ref, idx) => (
        <div key={idx} className="bg-white border border-gray-200 rounded-xl p-5">
          <h3 className="text-sm font-semibold text-indigo-600 uppercase tracking-wide mb-3">
            {typeIcons[ref.type] ?? ref.type}
          </h3>
          <h4 className="text-lg font-semibold text-gray-900 mb-3">{ref.content.title}</h4>
          <ul className="space-y-2">
            {ref.content.items?.map((item: string, i: number) => (
              <li key={i} className="text-sm text-gray-700 flex items-start gap-2">
                <span className="text-indigo-400 mt-0.5 shrink-0">-</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  )
}
