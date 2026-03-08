import { describe, it, expect, beforeEach } from 'vitest'
import i18n from 'i18next'
import en from '../locales/en.json'
import th from '../locales/th.json'

describe('Localization', () => {
  beforeEach(async () => {
    await i18n.changeLanguage('en')
  })

  it('has matching keys between en and th', () => {
    function getKeys(obj: Record<string, unknown>, prefix = ''): string[] {
      const keys: string[] = []
      for (const [k, v] of Object.entries(obj)) {
        const fullKey = prefix ? `${prefix}.${k}` : k
        if (typeof v === 'object' && v !== null && !Array.isArray(v)) {
          keys.push(...getKeys(v as Record<string, unknown>, fullKey))
        } else {
          keys.push(fullKey)
        }
      }
      return keys
    }

    const enKeys = getKeys(en).sort()
    const thKeys = getKeys(th).sort()

    // Every English key should exist in Thai
    const missingInTh = enKeys.filter((k) => !thKeys.includes(k))
    expect(missingInTh).toEqual([])

    // Every Thai key should exist in English
    const missingInEn = thKeys.filter((k) => !enKeys.includes(k))
    expect(missingInEn).toEqual([])
  })

  it('translates to English by default', () => {
    expect(i18n.t('gameSelection.title')).toBe('Choose a Game to Learn')
  })

  it('translates to Thai when language is changed', async () => {
    await i18n.changeLanguage('th')
    expect(i18n.t('gameSelection.title')).toBe('เลือกเกมที่จะเรียนรู้')
  })

  it('handles interpolation correctly in both languages', async () => {
    expect(i18n.t('gameSelection.players', { min: 3, max: 4 })).toBe('3-4 players')

    await i18n.changeLanguage('th')
    expect(i18n.t('gameSelection.players', { min: 3, max: 4 })).toBe('3-4 ผู้เล่น')
  })

  it('handles nested keys (setup checklist items)', async () => {
    expect(i18n.t('setup.catan.0')).toContain('hex tiles')

    await i18n.changeLanguage('th')
    expect(i18n.t('setup.catan.0')).toContain('หกเหลี่ยม')
  })

  it('handles all tab translations', async () => {
    const tabs = ['tabs.tutorial', 'tabs.qa', 'tabs.camera', 'tabs.reference', 'tabs.realtime']
    for (const key of tabs) {
      expect(i18n.t(key)).toBeTruthy()
      await i18n.changeLanguage('th')
      expect(i18n.t(key)).toBeTruthy()
      await i18n.changeLanguage('en')
    }
  })

  it('handles realtime state labels', async () => {
    const states = ['realtime.inactive', 'realtime.listening', 'realtime.processing', 'realtime.speaking']
    for (const key of states) {
      const enVal = i18n.t(key)
      await i18n.changeLanguage('th')
      const thVal = i18n.t(key)
      expect(enVal).not.toBe(thVal) // Should be different translations
      await i18n.changeLanguage('en')
    }
  })

  it('no English values leak into Thai translations', async () => {
    // Spot-check some Thai translations are actually Thai (contain Thai characters)
    await i18n.changeLanguage('th')
    const thaiKeys = [
      'gameSelection.title',
      'tabs.tutorial',
      'chat.send',
      'realtime.start',
      'setup.title',
    ]
    for (const key of thaiKeys) {
      const val = i18n.t(key)
      // Thai characters are in the range U+0E00–U+0E7F
      expect(/[\u0E00-\u0E7F]/.test(val)).toBe(true)
    }
  })
})
