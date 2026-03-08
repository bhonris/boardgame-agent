import { useCallback, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { textToSpeech } from '../api/client'

interface VoiceInterfaceProps {
  onTranscript: (text: string) => void
  lastAssistantMessage?: string
}

const LANG_MAP: Record<string, string> = {
  en: 'en-US',
  th: 'th-TH',
}

export function VoiceInterface({ onTranscript, lastAssistantMessage }: VoiceInterfaceProps) {
  const { t, i18n } = useTranslation()
  const [isListening, setIsListening] = useState(false)
  const [isSpeaking, setIsSpeaking] = useState(false)
  const [transcript, setTranscript] = useState('')
  const recognitionRef = useRef<SpeechRecognition | null>(null)
  const audioRef = useRef<HTMLAudioElement | null>(null)

  const startListening = useCallback(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SpeechRecognition) {
      alert(t('voice.notSupported'))
      return
    }

    const recognition = new SpeechRecognition()
    recognition.continuous = false
    recognition.interimResults = true
    recognition.lang = LANG_MAP[i18n.language] ?? 'en-US'

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      const result = event.results[event.results.length - 1]
      const text = result[0].transcript
      setTranscript(text)

      if (result.isFinal) {
        onTranscript(text)
        setIsListening(false)
      }
    }

    recognition.onerror = () => {
      setIsListening(false)
    }

    recognition.onend = () => {
      setIsListening(false)
    }

    recognitionRef.current = recognition
    recognition.start()
    setIsListening(true)
    setTranscript('')
  }, [onTranscript, t, i18n.language])

  const stopListening = useCallback(() => {
    recognitionRef.current?.stop()
    setIsListening(false)
  }, [])

  const speakResponse = useCallback(async () => {
    if (!lastAssistantMessage) return
    setIsSpeaking(true)

    try {
      // Try cloud TTS first, fall back to browser TTS
      try {
        const blob = await textToSpeech(lastAssistantMessage)
        const url = URL.createObjectURL(blob)
        const audio = new Audio(url)
        audioRef.current = audio
        audio.onended = () => {
          setIsSpeaking(false)
          URL.revokeObjectURL(url)
        }
        await audio.play()
        return
      } catch {
        // Fall back to browser TTS
      }

      const utterance = new SpeechSynthesisUtterance(lastAssistantMessage)
      utterance.rate = 1.0
      utterance.lang = LANG_MAP[i18n.language] ?? 'en-US'
      utterance.onend = () => setIsSpeaking(false)
      speechSynthesis.speak(utterance)
    } catch {
      setIsSpeaking(false)
    }
  }, [lastAssistantMessage, i18n.language])

  const stopSpeaking = useCallback(() => {
    audioRef.current?.pause()
    speechSynthesis.cancel()
    setIsSpeaking(false)
  }, [])

  return (
    <div className="flex items-center gap-2">
      <button
        onMouseDown={startListening}
        onMouseUp={stopListening}
        onTouchStart={startListening}
        onTouchEnd={stopListening}
        className={`p-3 rounded-full transition-all min-w-[48px] min-h-[48px] flex items-center justify-center ${
          isListening
            ? 'bg-red-500 text-white scale-110 animate-pulse'
            : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
        }`}
        title={t('voice.holdToTalk')}
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" />
          <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
          <line x1="12" x2="12" y1="19" y2="22" />
        </svg>
      </button>

      {lastAssistantMessage && (
        <button
          onClick={isSpeaking ? stopSpeaking : speakResponse}
          className={`p-3 rounded-full transition-all min-w-[48px] min-h-[48px] flex items-center justify-center ${
            isSpeaking
              ? 'bg-indigo-500 text-white animate-pulse'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          }`}
          title={isSpeaking ? t('voice.stopSpeaking') : t('voice.readAloud')}
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
            <path d="M15.54 8.46a5 5 0 0 1 0 7.07" />
            <path d="M19.07 4.93a10 10 0 0 1 0 14.14" />
          </svg>
        </button>
      )}

      {transcript && (
        <span className="text-sm text-gray-500 italic truncate max-w-[200px]">{transcript}</span>
      )}
    </div>
  )
}
