import { useGameStore } from '../gameStore'

describe('gameStore', () => {
  beforeEach(() => {
    useGameStore.setState({
      selectedGame: null,
      sessionId: null,
      messages: [],
      currentTutorialStep: 0,
      activeTab: 'tutorial',
      isChatOpen: false,
    })
  })

  it('selects a game and resets state', () => {
    const game = { id: 'catan', title: 'Catan', coverImageUrl: null, minPlayers: 3, maxPlayers: 4, complexityWeight: 2.3, playTimeMinutes: 90, description: 'Test' }

    useGameStore.getState().addMessage({ id: '1', role: 'user', content: 'test' })
    useGameStore.getState().setSessionId('session-1')
    useGameStore.getState().setTutorialStep(3)

    useGameStore.getState().setSelectedGame(game)

    const state = useGameStore.getState()
    expect(state.selectedGame?.id).toBe('catan')
    expect(state.messages).toEqual([])
    expect(state.sessionId).toBeNull()
    expect(state.currentTutorialStep).toBe(0)
  })

  it('adds and updates messages', () => {
    useGameStore.getState().addMessage({ id: '1', role: 'user', content: 'hello' })
    useGameStore.getState().addMessage({ id: '2', role: 'assistant', content: 'Hi' })

    expect(useGameStore.getState().messages).toHaveLength(2)

    useGameStore.getState().updateLastMessage(' there!')
    expect(useGameStore.getState().messages[1].content).toBe('Hi there!')
  })

  it('clears messages', () => {
    useGameStore.getState().addMessage({ id: '1', role: 'user', content: 'test' })
    useGameStore.getState().clearMessages()
    expect(useGameStore.getState().messages).toEqual([])
  })

  it('sets active tab', () => {
    useGameStore.getState().setActiveTab('chat')
    expect(useGameStore.getState().activeTab).toBe('chat')
  })

  it('sets active tab to realtime', () => {
    useGameStore.getState().setActiveTab('realtime')
    expect(useGameStore.getState().activeTab).toBe('realtime')
  })

  it('cycles through all tab values including realtime', () => {
    const tabs: Array<'tutorial' | 'chat' | 'camera' | 'reference' | 'realtime'> = [
      'tutorial', 'chat', 'camera', 'reference', 'realtime',
    ]
    for (const tab of tabs) {
      useGameStore.getState().setActiveTab(tab)
      expect(useGameStore.getState().activeTab).toBe(tab)
    }
  })

  it('sets tutorial step', () => {
    useGameStore.getState().setTutorialStep(5)
    expect(useGameStore.getState().currentTutorialStep).toBe(5)
  })

  it('sets session id', () => {
    useGameStore.getState().setSessionId('abc-123')
    expect(useGameStore.getState().sessionId).toBe('abc-123')
  })

  it('does not update non-assistant last message', () => {
    useGameStore.getState().addMessage({ id: '1', role: 'user', content: 'hello' })
    useGameStore.getState().updateLastMessage(' more')
    expect(useGameStore.getState().messages[0].content).toBe('hello')
  })
})
