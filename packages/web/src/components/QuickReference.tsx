import { useQuery } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { fetchReference } from '../api/client'
import { useGameStore } from '../stores/gameStore'

export function QuickReference() {
  const { t } = useTranslation()
  const game = useGameStore((s) => s.selectedGame)

  const { data, isLoading } = useQuery({
    queryKey: ['reference', game?.id],
    queryFn: () => fetchReference(game!.id),
    enabled: !!game,
  })

  if (isLoading || !data) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-pulse text-gray-400">{t('reference.loading')}</div>
      </div>
    )
  }

  const typeLabels: Record<string, string> = {
    turn_order: t('reference.types.turn_order'),
    icons: t('reference.types.key_info'),
    scoring: t('reference.types.scoring'),
    setup: t('reference.types.setup'),
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <h2 className="text-xl font-bold text-gray-900">{t('reference.title', { game: game?.title })}</h2>
      {data.references.map((ref, idx) => (
        <div key={idx} className="bg-white border border-gray-200 rounded-xl p-5">
          <h3 className="text-sm font-semibold text-indigo-600 uppercase tracking-wide mb-3">
            {typeLabels[ref.type] ?? ref.type}
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
