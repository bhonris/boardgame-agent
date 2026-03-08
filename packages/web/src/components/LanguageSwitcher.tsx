import { useTranslation } from 'react-i18next'

const languages = [
  { code: 'en', label: 'EN' },
  { code: 'th', label: 'TH' },
] as const

export function LanguageSwitcher() {
  const { i18n } = useTranslation()

  return (
    <div className="flex items-center gap-1 rounded-lg bg-gray-100 p-0.5">
      {languages.map(({ code, label }) => (
        <button
          key={code}
          onClick={() => i18n.changeLanguage(code)}
          className={`px-2.5 py-1 rounded-md text-xs font-semibold transition-colors ${
            i18n.language === code
              ? 'bg-white text-indigo-600 shadow-sm'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          {label}
        </button>
      ))}
    </div>
  )
}
