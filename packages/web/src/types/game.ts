export interface Game {
  id: string
  title: string
  coverImageUrl: string | null
  minPlayers: number
  maxPlayers: number
  complexityWeight: number | null
  playTimeMinutes: number | null
  description: string | null
}

export interface TutorialStep {
  id: number
  phase: string
  title: string
  content: string
  imageUrl?: string | null
  estimatedSeconds: number
}

export interface TutorialData {
  gameId: string
  steps: TutorialStep[]
  totalSteps: number
  estimatedMinutes: number
}

export interface ReferenceItem {
  type: string
  title: string
  content: { title?: string; items: string[] }
  displayOrder: number
}

export interface ReferenceData {
  gameId: string
  references: ReferenceItem[]
}

export interface ChatChunk {
  text: string
}

export interface ChatDone {
  citations: Array<{ section?: string; chunkIndex?: number }>
  sessionId: string
}

export interface VisionResponse {
  analysis: string
  confidence: string
  relatedRules: string[]
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  citations?: Array<{ section?: string }>
  isStreaming?: boolean
}
