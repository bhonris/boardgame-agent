import { create } from 'zustand'
import type { ChatMessage, Game } from '../types/game'

interface GameStore {
  selectedGame: Game | null
  setSelectedGame: (game: Game | null) => void
  sessionId: string | null
  setSessionId: (id: string) => void
  messages: ChatMessage[]
  addMessage: (msg: ChatMessage) => void
  updateLastMessage: (content: string) => void
  clearMessages: () => void
  currentTutorialStep: number
  setTutorialStep: (step: number) => void
  activeTab: 'tutorial' | 'chat' | 'camera' | 'reference'
  setActiveTab: (tab: 'tutorial' | 'chat' | 'camera' | 'reference') => void
  isChatOpen: boolean
  setChatOpen: (open: boolean) => void
}

export const useGameStore = create<GameStore>((set) => ({
  selectedGame: null,
  setSelectedGame: (game) => set({ selectedGame: game, messages: [], sessionId: null, currentTutorialStep: 0 }),
  sessionId: null,
  setSessionId: (id) => set({ sessionId: id }),
  messages: [],
  addMessage: (msg) => set((state) => ({ messages: [...state.messages, msg] })),
  updateLastMessage: (content) =>
    set((state) => {
      const messages = [...state.messages]
      const last = messages[messages.length - 1]
      if (last && last.role === 'assistant') {
        messages[messages.length - 1] = { ...last, content: last.content + content }
      }
      return { messages }
    }),
  clearMessages: () => set({ messages: [] }),
  currentTutorialStep: 0,
  setTutorialStep: (step) => set({ currentTutorialStep: step }),
  activeTab: 'tutorial',
  setActiveTab: (tab) => set({ activeTab: tab }),
  isChatOpen: false,
  setChatOpen: (open) => set({ isChatOpen: open }),
}))
