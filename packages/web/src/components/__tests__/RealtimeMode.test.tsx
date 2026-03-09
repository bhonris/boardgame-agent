import { render, screen, waitFor, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { RealtimeMode } from '../RealtimeMode'
import { useGameStore } from '../../stores/gameStore'
import { vi } from 'vitest'

// Mock the API client
vi.mock('../../api/client', () => ({
  streamChatRealtime: vi.fn(),
  textToSpeech: vi.fn(),
}))

import { streamChatRealtime, textToSpeech } from '../../api/client'

// Mock SpeechRecognition as a proper class so `new SpeechRecognitionCtor()` works
let mockRecognitionInstance: MockSpeechRecognition | null = null

class MockSpeechRecognition {
  continuous = false
  interimResults = false
  lang = ''
  start = vi.fn()
  stop = vi.fn()
  abort = vi.fn()
  onresult: ((event: unknown) => void) | null = null
  onerror: ((event: unknown) => void) | null = null
  onend: (() => void) | null = null
  addEventListener = vi.fn()
  removeEventListener = vi.fn()
  dispatchEvent = vi.fn(() => true)

  constructor() {
    mockRecognitionInstance = this
  }
}

// Mock getUserMedia
const mockGetUserMedia = vi.fn()

// Mock speechSynthesis
const mockSpeechSynthesis = {
  speak: vi.fn(),
  cancel: vi.fn(),
}

beforeAll(() => {
  Object.defineProperty(window, 'SpeechRecognition', {
    value: MockSpeechRecognition,
    writable: true,
    configurable: true,
  })
  Object.defineProperty(window, 'webkitSpeechRecognition', {
    value: undefined,
    writable: true,
    configurable: true,
  })
  Object.defineProperty(navigator, 'mediaDevices', {
    value: { getUserMedia: mockGetUserMedia },
    writable: true,
    configurable: true,
  })
  Object.defineProperty(window, 'speechSynthesis', {
    value: mockSpeechSynthesis,
    writable: true,
    configurable: true,
  })

  // Mock HTMLMediaElement.play/pause
  vi.spyOn(HTMLMediaElement.prototype, 'play').mockResolvedValue(undefined)
  vi.spyOn(HTMLMediaElement.prototype, 'pause').mockImplementation(() => {})

  // Mock Element.scrollTo (not implemented in jsdom)
  Element.prototype.scrollTo = vi.fn()
})

describe('RealtimeMode', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockRecognitionInstance = null

    // Restore SpeechRecognition in case a test removed it
    Object.defineProperty(window, 'SpeechRecognition', {
      value: MockSpeechRecognition,
      writable: true,
      configurable: true,
    })

    useGameStore.setState({
      selectedGame: {
        id: 'catan',
        title: 'Catan',
        coverImageUrl: null,
        minPlayers: 3,
        maxPlayers: 4,
        complexityWeight: 2.3,
        playTimeMinutes: 90,
        description: 'Test',
      },
      sessionId: null,
      messages: [],
    })

    // Default: camera succeeds
    const mockStream = {
      getTracks: () => [{ stop: vi.fn() }],
    }
    mockGetUserMedia.mockResolvedValue(mockStream)
  })

  it('renders camera feed and start button', async () => {
    render(<RealtimeMode />)

    // The video element is present
    const video = document.querySelector('video')
    expect(video).toBeInTheDocument()
    expect(video).toHaveAttribute('autoplay')
    // React sets muted as a DOM property, not an HTML attribute
    expect(video!.muted).toBe(true)

    // Start button is present
    expect(screen.getByText('Start Realtime')).toBeInTheDocument()

    // Camera should have been requested on mount
    await waitFor(() => {
      expect(mockGetUserMedia).toHaveBeenCalledWith(
        expect.objectContaining({ video: expect.any(Object) })
      )
    })
  })

  it('clicking "Start Realtime" toggles to active state with "Stop Realtime" button', async () => {
    render(<RealtimeMode />)

    const startButton = screen.getByText('Start Realtime')
    await userEvent.click(startButton)

    expect(screen.getByText('Stop Realtime')).toBeInTheDocument()
    expect(screen.queryByText('Start Realtime')).not.toBeInTheDocument()
  })

  it('clicking "Stop Realtime" returns to idle state', async () => {
    render(<RealtimeMode />)

    // Activate
    await userEvent.click(screen.getByText('Start Realtime'))
    expect(screen.getByText('Stop Realtime')).toBeInTheDocument()

    // Deactivate
    await userEvent.click(screen.getByText('Stop Realtime'))
    expect(screen.getByText('Start Realtime')).toBeInTheDocument()
    expect(screen.queryByText('Stop Realtime')).not.toBeInTheDocument()

    // Should show idle state label
    expect(screen.getByText('Inactive')).toBeInTheDocument()
  })

  it('shows camera error message when getUserMedia fails', async () => {
    mockGetUserMedia.mockRejectedValue(new Error('Permission denied'))

    render(<RealtimeMode />)

    await waitFor(() => {
      expect(
        screen.getByText(
          'Camera access denied. Realtime mode works best with a camera, but you can still use voice.: Permission denied'
        )
      ).toBeInTheDocument()
    })
  })

  it('displays state indicator with Inactive label by default', () => {
    render(<RealtimeMode />)
    expect(screen.getByText('Inactive')).toBeInTheDocument()
  })

  it('displays Listening label after starting realtime', async () => {
    render(<RealtimeMode />)

    await userEvent.click(screen.getByText('Start Realtime'))

    await waitFor(() => {
      expect(screen.getByText('Listening...')).toBeInTheDocument()
    })
  })

  it('displays Thinking label when processing a message', async () => {
    // Set up streamChatRealtime to never resolve so we stay in processing state
    const neverResolve = async function* () {
      await new Promise(() => {}) // hang forever
    }
    vi.mocked(streamChatRealtime).mockReturnValue(neverResolve() as ReturnType<typeof streamChatRealtime>)

    render(<RealtimeMode />)

    // Activate
    await userEvent.click(screen.getByText('Start Realtime'))

    await waitFor(() => {
      expect(mockRecognitionInstance).not.toBeNull()
    })

    // Simulate a final speech recognition result
    const speechEvent = {
      results: {
        length: 1,
        0: {
          isFinal: true,
          length: 1,
          0: { transcript: 'How do I play?', confidence: 0.9 },
        },
      },
    }

    await act(() => {
      mockRecognitionInstance!.onresult?.(speechEvent)
    })

    await waitFor(() => {
      expect(screen.getByText('Thinking...')).toBeInTheDocument()
    })
  })

  it('displays Speaking label when speaking a response', async () => {
    // Set up streamChatRealtime to return a response immediately
    const streamGen = async function* () {
      yield { event: 'chunk', data: JSON.stringify({ text: 'Hello there' }) }
      yield { event: 'done', data: JSON.stringify({ session_id: 'sess-1' }) }
    }
    vi.mocked(streamChatRealtime).mockReturnValue(streamGen() as ReturnType<typeof streamChatRealtime>)

    // textToSpeech returns a blob; the Audio mock will hang (onended never fires)
    vi.mocked(textToSpeech).mockResolvedValue(new Blob(['audio'], { type: 'audio/mp3' }))

    render(<RealtimeMode />)

    await userEvent.click(screen.getByText('Start Realtime'))

    await waitFor(() => {
      expect(mockRecognitionInstance).not.toBeNull()
    })

    // Simulate speech result
    const speechEvent = {
      results: {
        length: 1,
        0: {
          isFinal: true,
          length: 1,
          0: { transcript: 'Tell me about Catan', confidence: 0.9 },
        },
      },
    }

    await act(() => {
      mockRecognitionInstance!.onresult?.(speechEvent)
    })

    await waitFor(() => {
      expect(screen.getByText('Speaking...')).toBeInTheDocument()
    })
  })

  it('displays recent messages as overlay', async () => {
    useGameStore.setState({
      messages: [
        { id: '1', role: 'user', content: 'How do I set up Catan?' },
        { id: '2', role: 'assistant', content: 'First, lay out the board tiles...' },
      ],
    })

    render(<RealtimeMode />)

    await waitFor(() => {
      expect(screen.getByText('How do I set up Catan?')).toBeInTheDocument()
    })
    expect(screen.getByText('First, lay out the board tiles...')).toBeInTheDocument()
  })

  it('only shows last 6 messages in overlay', async () => {
    const messages = Array.from({ length: 8 }, (_, i) => ({
      id: String(i),
      role: (i % 2 === 0 ? 'user' : 'assistant') as 'user' | 'assistant',
      content: `Message ${i}`,
    }))
    useGameStore.setState({ messages })

    render(<RealtimeMode />)

    await waitFor(() => {
      expect(screen.getByText('Message 2')).toBeInTheDocument()
    })

    // Messages 0 and 1 should not be visible (only last 6: indices 2-7)
    expect(screen.queryByText('Message 0')).not.toBeInTheDocument()
    expect(screen.queryByText('Message 1')).not.toBeInTheDocument()
    expect(screen.getByText('Message 7')).toBeInTheDocument()
  })

  it('shows speech recognition not supported error when no SpeechRecognition API', async () => {
    // Remove SpeechRecognition so the component falls into the unsupported branch
    Object.defineProperty(window, 'SpeechRecognition', { value: undefined, writable: true, configurable: true })
    Object.defineProperty(window, 'webkitSpeechRecognition', { value: undefined, writable: true, configurable: true })

    // Also make camera fail so streamRef.current is null and the error message renders
    mockGetUserMedia.mockRejectedValue(new Error('No camera'))

    render(<RealtimeMode />)

    // Wait for camera error to be processed first
    await waitFor(() => {
      expect(mockGetUserMedia).toHaveBeenCalled()
    })

    await userEvent.click(screen.getByText('Start Realtime'))

    await waitFor(() => {
      expect(
        screen.getByText('Speech recognition is not supported in this browser.')
      ).toBeInTheDocument()
    })
  })

  it('shows helper text based on active state', async () => {
    render(<RealtimeMode />)

    expect(
      screen.getByText('Point your camera at the board and tap to start')
    ).toBeInTheDocument()

    await userEvent.click(screen.getByText('Start Realtime'))

    expect(
      screen.getByText('Speak naturally — I can see the board and hear you')
    ).toBeInTheDocument()
  })

  it('does not restart recognition when in processing state (regression: stale closure)', async () => {
    // Set up streamChatRealtime to never resolve so we stay in processing state
    const neverResolve = async function* () {
      await new Promise(() => {}) // hang forever
    }
    vi.mocked(streamChatRealtime).mockReturnValue(neverResolve() as ReturnType<typeof streamChatRealtime>)

    render(<RealtimeMode />)

    await userEvent.click(screen.getByText('Start Realtime'))

    await waitFor(() => {
      expect(mockRecognitionInstance).not.toBeNull()
    })

    const firstRecognition = mockRecognitionInstance!

    // Simulate a final speech recognition result -> triggers sendMessage -> state = processing
    const speechEvent = {
      results: {
        length: 1,
        0: {
          isFinal: true,
          length: 1,
          0: { transcript: 'How do I play?', confidence: 0.9 },
        },
      },
    }

    await act(() => {
      firstRecognition.onresult?.(speechEvent)
    })

    await waitFor(() => {
      expect(screen.getByText('Thinking...')).toBeInTheDocument()
    })

    // Now simulate recognition ending (as it normally would after a final result)
    // With the fix, it should NOT restart because we're in 'processing' state
    const startCallsBefore = firstRecognition.start.mock.calls.length

    await act(() => {
      firstRecognition.onend?.()
    })

    // Wait a bit for any setTimeout to fire
    await act(async () => {
      await new Promise((r) => setTimeout(r, 200))
    })

    // Recognition.start should not have been called again
    // (the first recognition instance's start was called once when we clicked Start Realtime)
    expect(firstRecognition.start).toHaveBeenCalledTimes(startCallsBefore)
  })

  it('blocks concurrent sendMessage calls (regression: overlapping SSE)', async () => {
    let callCount = 0

    // First call hangs, second call should be blocked
    vi.mocked(streamChatRealtime).mockImplementation(() => {
      callCount++
      const gen = async function* () {
        await new Promise<void>(() => { /* never resolves — simulates hanging request */ })
        yield { event: 'chunk' as const, data: JSON.stringify({ text: 'hello' }) }
        yield { event: 'done' as const, data: JSON.stringify({ session_id: 's1' }) }
      }
      return gen() as ReturnType<typeof streamChatRealtime>
    })

    render(<RealtimeMode />)
    await userEvent.click(screen.getByText('Start Realtime'))

    await waitFor(() => {
      expect(mockRecognitionInstance).not.toBeNull()
    })

    // First speech result
    await act(() => {
      mockRecognitionInstance!.onresult?.({
        results: {
          length: 1,
          0: { isFinal: true, length: 1, 0: { transcript: 'First', confidence: 0.9 } },
        },
      })
    })

    await waitFor(() => {
      expect(screen.getByText('Thinking...')).toBeInTheDocument()
    })

    // Second speech result while still processing — should be blocked
    await act(() => {
      mockRecognitionInstance!.onresult?.({
        results: {
          length: 1,
          0: { isFinal: true, length: 1, 0: { transcript: 'Second', confidence: 0.9 } },
        },
      })
    })

    // streamChatRealtime should only have been called once
    expect(callCount).toBe(1)
  })

  it('displays SSE error events in transcript (regression: silent error swallowing)', async () => {
    // Backend returns an error event instead of chunks
    const errorStream = async function* () {
      yield { event: 'error', data: JSON.stringify({ error: 'Model unavailable' }) }
    }
    vi.mocked(streamChatRealtime).mockReturnValue(errorStream() as ReturnType<typeof streamChatRealtime>)

    render(<RealtimeMode />)
    await userEvent.click(screen.getByText('Start Realtime'))

    await waitFor(() => {
      expect(mockRecognitionInstance).not.toBeNull()
    })

    await act(() => {
      mockRecognitionInstance!.onresult?.({
        results: {
          length: 1,
          0: { isFinal: true, length: 1, 0: { transcript: 'Hello', confidence: 0.9 } },
        },
      })
    })

    // Error message should appear in the assistant message
    await waitFor(() => {
      const msgs = useGameStore.getState().messages
      const lastAssistant = msgs.filter((m) => m.role === 'assistant').pop()
      expect(lastAssistant?.content).toContain('Error: Model unavailable')
    })
  })

  it('passes current language to streamChatRealtime', async () => {
    // streamChatRealtime hangs so we never reach speakText (avoids SpeechSynthesisUtterance issue)
    const neverResolve = async function* () {
      await new Promise(() => {}) // hang forever
    }
    vi.mocked(streamChatRealtime).mockReturnValue(neverResolve() as ReturnType<typeof streamChatRealtime>)

    render(<RealtimeMode />)
    await userEvent.click(screen.getByText('Start Realtime'))

    await waitFor(() => {
      expect(mockRecognitionInstance).not.toBeNull()
    })

    await act(() => {
      mockRecognitionInstance!.onresult?.({
        results: {
          length: 1,
          0: { isFinal: true, length: 1, 0: { transcript: 'สวัสดี', confidence: 0.9 } },
        },
      })
    })

    await waitFor(() => {
      expect(streamChatRealtime).toHaveBeenCalledWith(
        'catan',
        'สวัสดี',
        null, // snapshot (no real video in test)
        undefined, // sessionId
        expect.any(String), // language
      )
    })
  })

  it('allows new messages after an error (regression: isSendingRef not reset)', async () => {
    let callCount = 0

    // First call returns error, second should succeed
    vi.mocked(streamChatRealtime).mockImplementation(() => {
      callCount++
      if (callCount === 1) {
        const gen = async function* () {
          yield { event: 'error', data: JSON.stringify({ error: 'fail' }) }
        }
        return gen() as ReturnType<typeof streamChatRealtime>
      }
      const gen = async function* () {
        yield { event: 'chunk', data: JSON.stringify({ text: 'Success' }) }
        yield { event: 'done', data: JSON.stringify({ session_id: 's2' }) }
      }
      return gen() as ReturnType<typeof streamChatRealtime>
    })

    render(<RealtimeMode />)
    await userEvent.click(screen.getByText('Start Realtime'))

    await waitFor(() => {
      expect(mockRecognitionInstance).not.toBeNull()
    })

    // First message — will error
    await act(() => {
      mockRecognitionInstance!.onresult?.({
        results: {
          length: 1,
          0: { isFinal: true, length: 1, 0: { transcript: 'First', confidence: 0.9 } },
        },
      })
    })

    // Wait for error to be processed and isSendingRef to reset
    await waitFor(() => {
      expect(callCount).toBe(1)
    })

    // Brief wait for state to settle
    await act(async () => {
      await new Promise((r) => setTimeout(r, 50))
    })

    // Second message — should NOT be blocked by isSendingRef
    await act(() => {
      mockRecognitionInstance!.onresult?.({
        results: {
          length: 1,
          0: { isFinal: true, length: 1, 0: { transcript: 'Second', confidence: 0.9 } },
        },
      })
    })

    await waitFor(() => {
      expect(callCount).toBe(2)
    })
  })
})
