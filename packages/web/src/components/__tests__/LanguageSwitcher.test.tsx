import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, beforeEach } from 'vitest'
import i18n from 'i18next'
import { LanguageSwitcher } from '../LanguageSwitcher'

describe('LanguageSwitcher', () => {
  beforeEach(() => {
    i18n.changeLanguage('en')
  })

  it('renders EN and TH buttons', () => {
    render(<LanguageSwitcher />)
    expect(screen.getByText('EN')).toBeInTheDocument()
    expect(screen.getByText('TH')).toBeInTheDocument()
  })

  it('highlights the active language', () => {
    render(<LanguageSwitcher />)
    const enBtn = screen.getByText('EN')
    expect(enBtn.className).toContain('text-indigo-600')

    const thBtn = screen.getByText('TH')
    expect(thBtn.className).toContain('text-gray-500')
  })

  it('switches language to Thai on click', async () => {
    render(<LanguageSwitcher />)
    fireEvent.click(screen.getByText('TH'))
    expect(i18n.language).toBe('th')
  })

  it('switches back to English', async () => {
    i18n.changeLanguage('th')
    render(<LanguageSwitcher />)
    fireEvent.click(screen.getByText('EN'))
    expect(i18n.language).toBe('en')
  })
})
