import { useCallback, useEffect, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { streamChatRealtime, textToSpeech } from '../api/client'
import { useGameStore } from '../stores/gameStore'

type RealtimeState = 'idle' | 'listening' | 'processing' | 'speaking'

const LANG_MAP: Record<string, string> = {
  en: 'en-US',
  th: 'th-TH',
}

export function RealtimeMode() {
  const { t, i18n } = useTranslation()
  const game = useGameStore((s) => s.selectedGame)
  const sessionId = useGameStore((s) => s.sessionId)
  const setSessionId = useGameStore((s) => s.setSessionId)
  const messages = useGameStore((s) => s.messages)
  const addMessage = useGameStore((s) => s.addMessage)
  const updateLastMessage = useGameStore((s) => s.updateLastMessage)

  const [realtimeState, setRealtimeState] = useState<RealtimeState>('idle')
  const [isActive, setIsActive] = useState(false)
  const [cameraError, setCameraError] = useState<string | null>(null)
  const [transcript, setTranscript] = useState('')

  const videoRef = useRef<HTMLVideoElement>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const recognitionRef = useRef<SpeechRecognition | null>(null)
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const isActiveRef = useRef(false)
  const transcriptRef = useRef<HTMLDivElement>(null)
  const realtimeStateRef = useRef<RealtimeState>('idle')
  const isSendingRef = useRef(false)

  // Keep refs in sync with state
  useEffect(() => {
    isActiveRef.current = isActive
  }, [isActive])

  useEffect(() => {
    realtimeStateRef.current = realtimeState
  }, [realtimeState])

  // Auto-scroll transcript
  useEffect(() => {
    transcriptRef.current?.scrollTo({ top: transcriptRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages])

  // Start camera on mount
  useEffect(() => {
    startCamera()
    return () => {
      stopCamera()
      stopRecognition()
      stopAudio()
    }
  }, [])

  const startCamera = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment', width: { ideal: 1280 }, height: { ideal: 720 } },
      })
      if (videoRef.current) {
        videoRef.current.srcObject = stream
        streamRef.current = stream
      }
    } catch (err) {
      console.error('Camera access error:', err)
      setCameraError(`${t('realtime.cameraError')}: ${err instanceof Error ? err.message : String(err)}`)
    }
  }, [t])

  const stopCamera = useCallback(() => {
    streamRef.current?.getTracks().forEach((t) => t.stop())
    if (videoRef.current) videoRef.current.srcObject = null
    streamRef.current = null
  }, [])

  const captureSnapshot = useCallback((): Blob | null => {
    if (!videoRef.current || !videoRef.current.videoWidth) return null
    const canvas = document.createElement('canvas')
    canvas.width = 1280
    canvas.height = 720
    const ctx = canvas.getContext('2d')
    if (!ctx) return null
    ctx.drawImage(videoRef.current, 0, 0, 1280, 720)

    const dataUrl = canvas.toDataURL('image/jpeg', 0.8)
    const byteString = atob(dataUrl.split(',')[1])
    const ab = new ArrayBuffer(byteString.length)
    const ia = new Uint8Array(ab)
    for (let i = 0; i < byteString.length; i++) {
      ia[i] = byteString.charCodeAt(i)
    }
    return new Blob([ab], { type: 'image/jpeg' })
  }, [])

  const speakText = useCallback(async (text: string): Promise<void> => {
    setRealtimeState('speaking')
    try {
      try {
        const blob = await textToSpeech(text)
        const url = URL.createObjectURL(blob)
        const audio = new Audio(url)
        audioRef.current = audio
        await new Promise<void>((resolve) => {
          audio.onended = () => {
            URL.revokeObjectURL(url)
            resolve()
          }
          audio.onerror = () => {
            URL.revokeObjectURL(url)
            resolve()
          }
          audio.play().catch(() => resolve())
        })
        return
      } catch {
        // Fall back to browser TTS
      }

      await new Promise<void>((resolve) => {
        const utterance = new SpeechSynthesisUtterance(text)
        utterance.rate = 1.0
        utterance.lang = LANG_MAP[i18n.language] ?? 'en-US'
        utterance.onend = () => resolve()
        utterance.onerror = () => resolve()
        speechSynthesis.speak(utterance)
      })
    } finally {
      if (isActiveRef.current) {
        setRealtimeState('listening')
      }
    }
  }, [i18n.language])

  const stopAudio = useCallback(() => {
    audioRef.current?.pause()
    audioRef.current = null
    speechSynthesis.cancel()
  }, [])

  const sendMessage = useCallback(async (text: string) => {
    if (!game || isSendingRef.current) return
    isSendingRef.current = true
    setRealtimeState('processing')

    addMessage({ id: crypto.randomUUID(), role: 'user', content: text })
    addMessage({ id: crypto.randomUUID(), role: 'assistant', content: '', isStreaming: true })

    const snapshot = captureSnapshot()
    let fullResponse = ''

    try {
      for await (const event of streamChatRealtime(game.id, text, snapshot, sessionId ?? undefined)) {
        if (event.event === 'chunk') {
          const data = JSON.parse(event.data)
          fullResponse += data.text
          updateLastMessage(data.text)
        } else if (event.event === 'done') {
          const data = JSON.parse(event.data)
          if (data.session_id) setSessionId(data.session_id)
        } else if (event.event === 'error') {
          const data = JSON.parse(event.data)
          updateLastMessage(`\n\n_${t('realtime.error', { message: data.error })}_`)
        }
      }
    } catch {
      updateLastMessage(`\n\n_${t('realtime.connectionError')}_`)
    }

    isSendingRef.current = false

    if (fullResponse && isActiveRef.current) {
      await speakText(fullResponse)
    } else if (isActiveRef.current) {
      setRealtimeState('listening')
    }
  }, [game, sessionId, captureSnapshot, addMessage, updateLastMessage, setSessionId, speakText, t])

  const startRecognition = useCallback(() => {
    const SpeechRecognitionCtor = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SpeechRecognitionCtor) {
      setCameraError(t('realtime.speechError'))
      return
    }

    const recognition = new SpeechRecognitionCtor()
    recognition.continuous = false
    recognition.interimResults = true
    recognition.lang = LANG_MAP[i18n.language] ?? 'en-US'

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      const result = event.results[event.results.length - 1]
      const text = result[0].transcript
      setTranscript(text)

      if (result.isFinal) {
        setTranscript('')
        sendMessage(text)
      }
    }

    recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
      // "no-speech" and "aborted" are normal — onend will handle restart
      if (event.error === 'no-speech' || event.error === 'aborted') {
        return
      }
    }

    recognition.onend = () => {
      // Clear ref so useEffect can detect we need a new instance
      recognitionRef.current = null

      // Auto-restart if still active and in listening state
      if (isActiveRef.current && realtimeStateRef.current === 'listening') {
        setTimeout(() => {
          if (isActiveRef.current && !recognitionRef.current) startRecognition()
        }, 100)
      }
    }

    recognitionRef.current = recognition
    recognition.start()
    setRealtimeState('listening')
  }, [sendMessage, t, i18n.language])

  const stopRecognition = useCallback(() => {
    recognitionRef.current?.stop()
    recognitionRef.current = null
  }, [])

  const handleToggle = useCallback(() => {
    if (isActive) {
      // Deactivate
      setIsActive(false)
      isActiveRef.current = false
      stopRecognition()
      stopAudio()
      setRealtimeState('idle')
      setTranscript('')
    } else {
      // Activate
      setIsActive(true)
      isActiveRef.current = true
      startRecognition()
    }
  }, [isActive, startRecognition, stopRecognition, stopAudio])

  // Restart recognition after speaking finishes
  useEffect(() => {
    if (realtimeState === 'listening' && isActive && !recognitionRef.current) {
      startRecognition()
    }
  }, [realtimeState, isActive, startRecognition])

  const stateLabels: Record<RealtimeState, string> = {
    idle: t('realtime.inactive'),
    listening: t('realtime.listening'),
    processing: t('realtime.processing'),
    speaking: t('realtime.speaking'),
  }

  const stateConfig = {
    idle: { color: 'bg-gray-400', pulse: false },
    listening: { color: 'bg-green-500', pulse: true },
    processing: { color: 'bg-yellow-500', pulse: true },
    speaking: { color: 'bg-blue-500', pulse: true },
  }

  const { color, pulse } = stateConfig[realtimeState]

  // Show last 6 messages for the overlay
  const recentMessages = messages.slice(-6)

  return (
    <div className="max-w-4xl mx-auto">
      <div className="relative rounded-2xl overflow-hidden bg-black">
        {/* Camera feed */}
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted
          className="w-full aspect-video object-cover"
        />

        {cameraError && !streamRef.current && (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-900">
            <p className="text-white text-sm text-center px-8">{cameraError}</p>
          </div>
        )}

        {/* State indicator */}
        <div className="absolute top-4 left-4 flex items-center gap-2 bg-black/50 backdrop-blur-sm rounded-full px-3 py-1.5">
          <span className={`w-3 h-3 rounded-full ${color} ${pulse ? 'animate-pulse' : ''}`} />
          <span className="text-white text-xs font-medium">{stateLabels[realtimeState]}</span>
        </div>

        {/* Interim transcript */}
        {transcript && (
          <div className="absolute top-4 right-4 bg-black/50 backdrop-blur-sm rounded-lg px-3 py-1.5 max-w-[60%]">
            <p className="text-white text-sm italic truncate">{transcript}</p>
          </div>
        )}

        {/* Chat transcript overlay */}
        {recentMessages.length > 0 && (
          <div
            ref={transcriptRef}
            className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 via-black/60 to-transparent p-4 pt-12 max-h-[50%] overflow-y-auto"
          >
            <div className="space-y-2">
              {recentMessages.map((msg) => (
                <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-[80%] rounded-xl px-3 py-2 text-sm ${
                    msg.role === 'user'
                      ? 'bg-indigo-500/80 text-white'
                      : 'bg-white/20 backdrop-blur-sm text-white'
                  }`}>
                    {msg.content || <span className="inline-block w-2 h-4 bg-white/50 animate-pulse rounded" />}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Controls */}
      <div className="flex flex-col items-center gap-3 mt-4">
        <button
          onClick={handleToggle}
          className={`px-8 py-4 rounded-2xl text-lg font-semibold transition-all min-h-[56px] ${
            isActive
              ? 'bg-red-500 hover:bg-red-600 text-white shadow-lg shadow-red-500/25'
              : 'bg-indigo-500 hover:bg-indigo-600 text-white shadow-lg shadow-indigo-500/25'
          }`}
        >
          {isActive ? t('realtime.stop') : t('realtime.start')}
        </button>
        <p className="text-xs text-gray-500">
          {isActive ? t('realtime.hintActive') : t('realtime.hintInactive')}
        </p>
      </div>
    </div>
  )
}
