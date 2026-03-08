import { useState } from 'react'
import { useTranslation } from 'react-i18next'

interface ChecklistItem {
  id: string
  textKey: string
  checked: boolean
}

const SETUP_CHECKLISTS: Record<string, { gameKey: string; count: number }> = {
  catan: { gameKey: 'catan', count: 10 },
  'ticket-to-ride': { gameKey: 'ticket_to_ride', count: 7 },
  wingspan: { gameKey: 'wingspan', count: 8 },
}

interface SetupChecklistProps {
  gameId: string
}

export function SetupChecklist({ gameId }: SetupChecklistProps) {
  const { t } = useTranslation()
  const config = SETUP_CHECKLISTS[gameId]

  const [items, setItems] = useState<ChecklistItem[]>(() => {
    if (!config) return []
    return Array.from({ length: config.count }, (_, i) => ({
      id: String(i + 1),
      textKey: `setup.${config.gameKey}.${i}`,
      checked: false,
    }))
  })

  const toggleItem = (id: string) => {
    setItems((prev) =>
      prev.map((item) => (item.id === id ? { ...item, checked: !item.checked } : item))
    )
  }

  const completedCount = items.filter((i) => i.checked).length
  const allComplete = completedCount === items.length && items.length > 0

  if (items.length === 0) {
    return <p className="text-sm text-gray-400">{t('setup.empty')}</p>
  }

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">{t('setup.title')}</h3>
        <span className="text-sm text-gray-500">
          {t('setup.progress', { completed: completedCount, total: items.length })}
        </span>
      </div>

      <div className="w-full bg-gray-200 rounded-full h-1.5 mb-4">
        <div
          className={`h-1.5 rounded-full transition-all duration-300 ${allComplete ? 'bg-green-500' : 'bg-indigo-500'}`}
          style={{ width: `${(completedCount / items.length) * 100}%` }}
        />
      </div>

      <ul className="space-y-2">
        {items.map((item) => (
          <li key={item.id}>
            <label className="flex items-start gap-3 cursor-pointer group py-1">
              <input
                type="checkbox"
                checked={item.checked}
                onChange={() => toggleItem(item.id)}
                className="mt-0.5 w-5 h-5 rounded border-gray-300 text-indigo-500 focus:ring-indigo-500 cursor-pointer"
              />
              <span className={`text-sm leading-relaxed ${item.checked ? 'text-gray-400 line-through' : 'text-gray-700'}`}>
                {t(item.textKey)}
              </span>
            </label>
          </li>
        ))}
      </ul>

      {allComplete && (
        <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg text-sm text-green-700 text-center">
          {t('setup.complete')}
        </div>
      )}
    </div>
  )
}
