import { useCallback, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { streamChat } from '../api/client'
import { useGameStore } from '../stores/gameStore'

export function ChatInterface() {
  const { t } = useTranslation()
  const game = useGameStore((s) => s.selectedGame)
  const sessionId = useGameStore((s) => s.sessionId)
  const setSessionId = useGameStore((s) => s.setSessionId)
  const messages = useGameStore((s) => s.messages)
  const addMessage = useGameStore((s) => s.addMessage)
  const updateLastMessage = useGameStore((s) => s.updateLastMessage)

  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const handleSend = useCallback(async () => {
    if (!input.trim() || !game || isLoading) return

    const userMessage = input.trim()
    setInput('')
    setIsLoading(true)

    addMessage({
      id: crypto.randomUUID(),
      role: 'user',
      content: userMessage,
    })

    addMessage({
      id: crypto.randomUUID(),
      role: 'assistant',
      content: '',
      isStreaming: true,
    })

    try {
      for await (const event of streamChat(game.id, userMessage, sessionId ?? undefined)) {
        if (event.event === 'chunk') {
          const data = JSON.parse(event.data)
          updateLastMessage(data.text)
          scrollToBottom()
        } else if (event.event === 'done') {
          const data = JSON.parse(event.data)
          if (data.session_id) {
            setSessionId(data.session_id)
          }
        } else if (event.event === 'error') {
          const data = JSON.parse(event.data)
          updateLastMessage(`\n\n_${t('chat.error', { message: data.error })}_`)
        }
      }
    } catch (err) {
      updateLastMessage(`\n\n_${t('chat.connectionError')}_`)
    } finally {
      setIsLoading(false)
      scrollToBottom()
    }
  }, [input, game, isLoading, sessionId, addMessage, updateLastMessage, setSessionId, t])

  return (
    <div className="flex flex-col h-full max-w-3xl mx-auto">
      <div className="flex-1 overflow-y-auto space-y-4 pb-4">
        {messages.length === 0 && (
          <div className="text-center text-gray-400 mt-20">
            <p className="text-lg">{t('chat.askAnything', { game: game?.title })}</p>
            <p className="text-sm mt-2">{t('chat.hint')}</p>
          </div>
        )}
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                msg.role === 'user'
                  ? 'bg-indigo-500 text-white'
                  : 'bg-white border border-gray-200 text-gray-800'
              }`}
            >
              {msg.content || (
                <span className="inline-block w-2 h-4 bg-gray-300 animate-pulse rounded" />
              )}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      <div className="border-t border-gray-200 pt-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
            placeholder={t('chat.placeholder', { game: game?.title ?? '' })}
            disabled={isLoading}
            className="flex-1 px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent disabled:opacity-50 text-sm min-h-[48px]"
          />
          <button
            onClick={handleSend}
            disabled={isLoading || !input.trim()}
            className="px-6 py-3 bg-indigo-500 text-white rounded-xl hover:bg-indigo-600 disabled:opacity-40 disabled:cursor-not-allowed transition-colors text-sm font-medium min-h-[48px]"
          >
            {isLoading ? t('chat.thinking') : t('chat.send')}
          </button>
        </div>
      </div>
    </div>
  )
}
