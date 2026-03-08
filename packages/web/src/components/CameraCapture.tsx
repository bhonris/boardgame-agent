import { useCallback, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { analyzeImage } from '../api/client'
import { useGameStore } from '../stores/gameStore'
import type { VisionResponse } from '../types/game'

type VisionMode = 'identify' | 'read_card' | 'verify_setup'

export function CameraCapture() {
  const { t } = useTranslation()
  const game = useGameStore((s) => s.selectedGame)
  const sessionId = useGameStore((s) => s.sessionId)

  const [mode, setMode] = useState<VisionMode>('identify')
  const [preview, setPreview] = useState<string | null>(null)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [result, setResult] = useState<VisionResponse | null>(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fileInputRef = useRef<HTMLInputElement>(null)
  const videoRef = useRef<HTMLVideoElement>(null)
  const [isCameraActive, setIsCameraActive] = useState(false)

  const startCamera = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment', width: { ideal: 1280 }, height: { ideal: 720 } },
      })
      if (videoRef.current) {
        videoRef.current.srcObject = stream
        setIsCameraActive(true)
      }
    } catch {
      setError(t('camera.cameraError'))
    }
  }, [t])

  const capturePhoto = useCallback(() => {
    if (!videoRef.current) return
    const canvas = document.createElement('canvas')
    canvas.width = videoRef.current.videoWidth
    canvas.height = videoRef.current.videoHeight
    const ctx = canvas.getContext('2d')
    if (!ctx) return
    ctx.drawImage(videoRef.current, 0, 0)

    canvas.toBlob((blob) => {
      if (blob) {
        const file = new File([blob], 'capture.jpg', { type: 'image/jpeg' })
        setSelectedFile(file)
        setPreview(canvas.toDataURL('image/jpeg'))
        stopCamera()
      }
    }, 'image/jpeg', 0.85)
  }, [])

  const stopCamera = useCallback(() => {
    if (videoRef.current?.srcObject) {
      const stream = videoRef.current.srcObject as MediaStream
      stream.getTracks().forEach((t) => t.stop())
      videoRef.current.srcObject = null
    }
    setIsCameraActive(false)
  }, [])

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setSelectedFile(file)
    setPreview(URL.createObjectURL(file))
    setResult(null)
    setError(null)
  }, [])

  const handleAnalyze = useCallback(async () => {
    if (!selectedFile || !game) return
    setIsAnalyzing(true)
    setError(null)

    try {
      const response = await analyzeImage(game.id, selectedFile, mode, sessionId ?? undefined)
      setResult(response)
    } catch {
      setError(t('camera.analysisError'))
    } finally {
      setIsAnalyzing(false)
    }
  }, [selectedFile, game, mode, sessionId, t])

  const resetCapture = useCallback(() => {
    setPreview(null)
    setSelectedFile(null)
    setResult(null)
    setError(null)
  }, [])

  const modes: { value: VisionMode; labelKey: string; descKey: string }[] = [
    { value: 'identify', labelKey: 'camera.modes.identify', descKey: 'camera.modes.identifyDesc' },
    { value: 'read_card', labelKey: 'camera.modes.read_card', descKey: 'camera.modes.read_cardDesc' },
    { value: 'verify_setup', labelKey: 'camera.modes.verify_setup', descKey: 'camera.modes.verify_setupDesc' },
  ]

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <h2 className="text-xl font-bold text-gray-900">{t('camera.title', { game: game?.title })}</h2>

      <div className="flex gap-2 flex-wrap">
        {modes.map((m) => (
          <button
            key={m.value}
            onClick={() => setMode(m.value)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors min-h-[48px] ${
              mode === m.value
                ? 'bg-indigo-500 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            {t(m.labelKey)}
          </button>
        ))}
      </div>
      <p className="text-sm text-gray-500">{t(modes.find((m) => m.value === mode)?.descKey ?? '')}</p>

      {!preview && !isCameraActive && (
        <div className="flex gap-4">
          <button
            onClick={startCamera}
            className="flex-1 py-4 bg-indigo-500 text-white rounded-xl hover:bg-indigo-600 transition-colors text-sm font-medium min-h-[48px]"
          >
            {t('camera.openCamera')}
          </button>
          <button
            onClick={() => fileInputRef.current?.click()}
            className="flex-1 py-4 bg-gray-100 text-gray-700 rounded-xl hover:bg-gray-200 transition-colors text-sm font-medium min-h-[48px]"
          >
            {t('camera.uploadPhoto')}
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/jpeg,image/png,image/webp"
            onChange={handleFileSelect}
            className="hidden"
          />
        </div>
      )}

      {isCameraActive && (
        <div className="relative">
          <video ref={videoRef} autoPlay playsInline className="w-full rounded-xl" />
          <div className="flex gap-2 mt-4">
            <button
              onClick={capturePhoto}
              className="flex-1 py-4 bg-indigo-500 text-white rounded-xl hover:bg-indigo-600 text-sm font-medium min-h-[48px]"
            >
              {t('camera.capture')}
            </button>
            <button
              onClick={stopCamera}
              className="px-6 py-4 bg-gray-100 text-gray-600 rounded-xl hover:bg-gray-200 text-sm font-medium min-h-[48px]"
            >
              {t('camera.cancel')}
            </button>
          </div>
        </div>
      )}

      {preview && (
        <div className="space-y-4">
          <img src={preview} alt="Captured" className="w-full rounded-xl border border-gray-200" />
          <div className="flex gap-2">
            <button
              onClick={handleAnalyze}
              disabled={isAnalyzing}
              className="flex-1 py-3 bg-indigo-500 text-white rounded-xl hover:bg-indigo-600 disabled:opacity-50 text-sm font-medium min-h-[48px]"
            >
              {isAnalyzing ? t('camera.analyzing') : t('camera.analyze')}
            </button>
            <button
              onClick={resetCapture}
              className="px-6 py-3 bg-gray-100 text-gray-600 rounded-xl hover:bg-gray-200 text-sm font-medium min-h-[48px]"
            >
              {t('camera.retake')}
            </button>
          </div>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-sm text-red-700">
          {error}
        </div>
      )}

      {result && (
        <div className="bg-white border border-gray-200 rounded-xl p-5 space-y-3">
          <div className="flex items-center gap-2">
            <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
              result.confidence === 'high' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'
            }`}>
              {t('camera.confidence', { level: result.confidence })}
            </span>
          </div>
          <p className="text-sm text-gray-800 leading-relaxed whitespace-pre-wrap">{result.analysis}</p>
          {result.relatedRules.length > 0 && (
            <div className="border-t border-gray-100 pt-3">
              <h4 className="text-xs font-semibold text-gray-500 uppercase mb-2">{t('camera.relatedRules')}</h4>
              <ul className="space-y-1">
                {result.relatedRules.map((rule, i) => (
                  <li key={i} className="text-sm text-gray-600">{rule}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
