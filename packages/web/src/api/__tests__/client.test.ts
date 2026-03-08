import { describe, it, expect } from 'vitest'
import { snakeToCamel, transformKeys } from '../client'
import type { Game } from '../../types/game'

describe('snakeToCamel', () => {
  it('converts snake_case to camelCase', () => {
    expect(snakeToCamel('min_players')).toBe('minPlayers')
    expect(snakeToCamel('cover_image_url')).toBe('coverImageUrl')
    expect(snakeToCamel('play_time_minutes')).toBe('playTimeMinutes')
  })

  it('leaves camelCase unchanged', () => {
    expect(snakeToCamel('minPlayers')).toBe('minPlayers')
    expect(snakeToCamel('id')).toBe('id')
  })
})

describe('transformKeys', () => {
  it('transforms snake_case API response to camelCase Game object', () => {
    const apiResponse = {
      id: 'catan',
      title: 'Catan',
      cover_image_url: '/images/catan.jpg',
      min_players: 3,
      max_players: 4,
      complexity_weight: 2.3,
      play_time_minutes: 90,
      description: 'Trade and build',
    }

    const result = transformKeys<Game>(apiResponse)
    expect(result.minPlayers).toBe(3)
    expect(result.maxPlayers).toBe(4)
    expect(result.coverImageUrl).toBe('/images/catan.jpg')
    expect(result.playTimeMinutes).toBe(90)
    expect(result.complexityWeight).toBe(2.3)
  })

  it('transforms arrays of objects', () => {
    const apiResponse = [
      { id: 'catan', min_players: 3, max_players: 4 },
      { id: 'wingspan', min_players: 1, max_players: 5 },
    ]

    const result = transformKeys<Array<{ id: string; minPlayers: number; maxPlayers: number }>>(apiResponse)
    expect(result[0].minPlayers).toBe(3)
    expect(result[1].maxPlayers).toBe(5)
  })

  it('handles nested objects', () => {
    const apiResponse = {
      game_id: 'catan',
      references: [
        { display_order: 0, content: { title: 'Turn Structure' } },
      ],
    }

    const result = transformKeys<{ gameId: string; references: Array<{ displayOrder: number; content: { title: string } }> }>(apiResponse)
    expect(result.gameId).toBe('catan')
    expect(result.references[0].displayOrder).toBe(0)
    expect(result.references[0].content.title).toBe('Turn Structure')
  })

  it('handles null and primitive values', () => {
    expect(transformKeys<null>(null)).toBeNull()
    expect(transformKeys<number>(42)).toBe(42)
    expect(transformKeys<string>('hello')).toBe('hello')
  })
})
