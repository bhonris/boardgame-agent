import '@testing-library/jest-dom/vitest'
import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import en from './i18n/locales/en.json'
import th from './i18n/locales/th.json'

// Initialize i18n for tests with both languages
i18n.use(initReactI18next).init({
  resources: { en: { translation: en }, th: { translation: th } },
  lng: 'en',
  fallbackLng: 'en',
  interpolation: { escapeValue: false },
})
