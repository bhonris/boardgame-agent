import type { Game, TutorialData, ReferenceData, VisionResponse } from '../types/game'

const API_BASE = '/api'

export function snakeToCamel(str: string): string {
  return str.replace(/_([a-z])/g, (_, c) => c.toUpperCase())
}

export function transformKeys<T>(obj: unknown): T {
  if (Array.isArray(obj)) return obj.map((item) => transformKeys(item)) as T
  if (obj !== null && typeof obj === 'object') {
    return Object.fromEntries(
      Object.entries(obj as Record<string, unknown>).map(([k, v]) => [snakeToCamel(k), transformKeys(v)])
    ) as T
  }
  return obj as T
}

export async function fetchGames(): Promise<Game[]> {
  const res = await fetch(`${API_BASE}/games`)
  if (!res.ok) throw new Error('Failed to fetch games')
  const data = await res.json()
  return transformKeys<Game[]>(data.games)
}

export async function fetchGame(gameId: string): Promise<Game> {
  const res = await fetch(`${API_BASE}/games/${gameId}`)
  if (!res.ok) throw new Error('Game not found')
  const data = await res.json()
  return transformKeys<Game>(data)
}

export async function fetchTutorial(gameId: string): Promise<TutorialData> {
  const res = await fetch(`${API_BASE}/games/${gameId}/tutorial`)
  if (!res.ok) throw new Error('Tutorial not found')
  const data = await res.json()
  return transformKeys<TutorialData>(data)
}

export async function fetchReference(gameId: string): Promise<ReferenceData> {
  const res = await fetch(`${API_BASE}/games/${gameId}/reference`)
  if (!res.ok) throw new Error('Reference data not found')
  const data = await res.json()
  return transformKeys<ReferenceData>(data)
}

export async function* streamChat(
  gameId: string,
  message: string,
  sessionId?: string,
): AsyncGenerator<{ event: string; data: string }> {
  const res = await fetch(`${API_BASE}/games/${gameId}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, session_id: sessionId }),
  })

  if (!res.ok) throw new Error('Chat request failed')
  if (!res.body) throw new Error('No response body')

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() ?? ''

    let currentEvent = 'message'
    for (const line of lines) {
      if (line.startsWith('event:')) {
        currentEvent = line.slice(6).trim()
      } else if (line.startsWith('data:')) {
        yield { event: currentEvent, data: line.slice(5).trim() }
      }
    }
  }
}

export async function* streamChatRealtime(
  gameId: string,
  message: string,
  image?: Blob | null,
  sessionId?: string,
  language?: string,
): AsyncGenerator<{ event: string; data: string }> {
  const formData = new FormData()
  formData.append('message', message)
  if (image) formData.append('image', image, 'snapshot.jpg')
  if (sessionId) formData.append('session_id', sessionId)
  if (language) formData.append('language', language)

  const res = await fetch(`${API_BASE}/games/${gameId}/chat/realtime`, {
    method: 'POST',
    body: formData,
  })

  if (!res.ok) throw new Error('Realtime chat request failed')
  if (!res.body) throw new Error('No response body')

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() ?? ''

    let currentEvent = 'message'
    for (const line of lines) {
      if (line.startsWith('event:')) {
        currentEvent = line.slice(6).trim()
      } else if (line.startsWith('data:')) {
        yield { event: currentEvent, data: line.slice(5).trim() }
      }
    }
  }
}

export async function analyzeImage(
  gameId: string,
  image: File,
  mode: string,
  sessionId?: string,
): Promise<VisionResponse> {
  const formData = new FormData()
  formData.append('image', image)
  formData.append('mode', mode)
  if (sessionId) formData.append('session_id', sessionId)

  const res = await fetch(`${API_BASE}/games/${gameId}/vision`, {
    method: 'POST',
    body: formData,
  })

  if (!res.ok) throw new Error('Vision analysis failed')
  const data = await res.json()
  return transformKeys<VisionResponse>(data)
}

export async function textToSpeech(text: string, voice = 'alloy'): Promise<Blob> {
  const res = await fetch(`${API_BASE}/tts`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, voice }),
  })

  if (!res.ok) throw new Error('TTS request failed')
  return res.blob()
}
