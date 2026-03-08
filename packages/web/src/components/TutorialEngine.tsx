import { useQuery } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { fetchTutorial } from '../api/client'
import { useGameStore } from '../stores/gameStore'

export function TutorialEngine() {
  const { t } = useTranslation()
  const game = useGameStore((s) => s.selectedGame)
  const currentStep = useGameStore((s) => s.currentTutorialStep)
  const setStep = useGameStore((s) => s.setTutorialStep)

  const { data: tutorial, isLoading } = useQuery({
    queryKey: ['tutorial', game?.id],
    queryFn: () => fetchTutorial(game!.id),
    enabled: !!game,
  })

  if (isLoading || !tutorial) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-pulse text-gray-400">{t('tutorial.loading')}</div>
      </div>
    )
  }

  const step = tutorial.steps[currentStep]
  if (!step) return null

  const phaseColors: Record<string, string> = {
    theme_and_goal: 'bg-blue-100 text-blue-700',
    components: 'bg-green-100 text-green-700',
    setup: 'bg-yellow-100 text-yellow-700',
    turn_structure: 'bg-purple-100 text-purple-700',
    core_actions: 'bg-red-100 text-red-700',
    walkthrough: 'bg-indigo-100 text-indigo-700',
  }

  const phaseLabel = t(`tutorial.phases.${step.phase}`, { defaultValue: step.phase.replace(/_/g, ' ') })
  const phaseColor = phaseColors[step.phase] ?? 'bg-gray-100 text-gray-700'

  return (
    <div className="max-w-3xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <span className={`text-xs font-medium px-2.5 py-1 rounded-full capitalize ${phaseColor}`}>
          {phaseLabel}
        </span>
        <span className="text-sm text-gray-400">
          {t('tutorial.stepOf', { current: currentStep + 1, total: tutorial.totalSteps })}
        </span>
      </div>

      <div className="w-full bg-gray-200 rounded-full h-1.5 mb-6">
        <div
          className="bg-indigo-500 h-1.5 rounded-full transition-all duration-300"
          style={{ width: `${((currentStep + 1) / tutorial.totalSteps) * 100}%` }}
        />
      </div>

      <h2 className="text-2xl font-bold text-gray-900 mb-4">{step.title}</h2>

      <div className="prose prose-gray max-w-none mb-8">
        {step.content.split('\n').map((line, i) => {
          if (!line.trim()) return <br key={i} />
          const formatted = line
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')

          if (line.trim().startsWith('|')) {
            return <p key={i} className="font-mono text-sm" dangerouslySetInnerHTML={{ __html: formatted }} />
          }
          if (line.trim().startsWith('- ')) {
            return <li key={i} className="ml-4" dangerouslySetInnerHTML={{ __html: formatted.replace(/^- /, '') }} />
          }
          if (line.trim().match(/^\d+\./)) {
            return <li key={i} className="ml-4 list-decimal" dangerouslySetInnerHTML={{ __html: formatted.replace(/^\d+\.\s*/, '') }} />
          }
          return <p key={i} dangerouslySetInnerHTML={{ __html: formatted }} />
        })}
      </div>

      <div className="flex justify-between items-center pt-4 border-t border-gray-100">
        <button
          onClick={() => setStep(Math.max(0, currentStep - 1))}
          disabled={currentStep === 0}
          className="px-6 py-3 text-sm font-medium text-gray-600 bg-gray-100 rounded-lg hover:bg-gray-200 disabled:opacity-40 disabled:cursor-not-allowed transition-colors min-h-[48px]"
        >
          {t('tutorial.previous')}
        </button>
        <button
          onClick={() => setStep(Math.min(tutorial.totalSteps - 1, currentStep + 1))}
          disabled={currentStep === tutorial.totalSteps - 1}
          className="px-6 py-3 text-sm font-medium text-white bg-indigo-500 rounded-lg hover:bg-indigo-600 disabled:opacity-40 disabled:cursor-not-allowed transition-colors min-h-[48px]"
        >
          {t('tutorial.next')}
        </button>
      </div>
    </div>
  )
}
