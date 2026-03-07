import { useState } from 'react'

interface ChecklistItem {
  id: string
  text: string
  checked: boolean
}

const SETUP_CHECKLISTS: Record<string, ChecklistItem[]> = {
  catan: [
    { id: '1', text: 'Arrange hex tiles in the frame (use beginner layout)', checked: false },
    { id: '2', text: 'Place number tokens on hexes (follow letter order)', checked: false },
    { id: '3', text: 'Place the Robber on the desert hex', checked: false },
    { id: '4', text: 'Each player takes 5 settlements, 4 cities, 15 roads', checked: false },
    { id: '5', text: 'Shuffle and place resource card stacks', checked: false },
    { id: '6', text: 'Shuffle development cards', checked: false },
    { id: '7', text: 'Place Longest Road and Largest Army cards nearby', checked: false },
    { id: '8', text: 'Each player places 1st settlement + road (youngest first)', checked: false },
    { id: '9', text: 'Each player places 2nd settlement + road (reverse order)', checked: false },
    { id: '10', text: 'Collect resources for 2nd settlement', checked: false },
  ],
  'ticket-to-ride': [
    { id: '1', text: 'Unfold the board in the center of the table', checked: false },
    { id: '2', text: 'Each player takes 45 train cars and a scoring marker', checked: false },
    { id: '3', text: 'Place scoring markers at 0', checked: false },
    { id: '4', text: 'Shuffle Train Card deck, deal 4 to each player', checked: false },
    { id: '5', text: 'Flip 5 Train Cards face-up', checked: false },
    { id: '6', text: 'Shuffle Destination Tickets, deal 3 to each player', checked: false },
    { id: '7', text: 'Each player keeps at least 2 destination tickets', checked: false },
  ],
  wingspan: [
    { id: '1', text: 'Each player takes a player mat and 8 action cubes', checked: false },
    { id: '2', text: 'Shuffle bird deck, deal 5 birds to each player', checked: false },
    { id: '3', text: 'Place 3 bird cards face-up in the tray', checked: false },
    { id: '4', text: 'Deal 2 bonus cards to each player (keep 1)', checked: false },
    { id: '5', text: 'Give each player 5 food tokens (1 of each type)', checked: false },
    { id: '6', text: 'Players choose birds/food to keep (discard 1 food per bird kept)', checked: false },
    { id: '7', text: 'Place round-end goal tiles for all 4 rounds', checked: false },
    { id: '8', text: 'Roll all 5 food dice into the birdfeeder', checked: false },
  ],
}

interface SetupChecklistProps {
  gameId: string
}

export function SetupChecklist({ gameId }: SetupChecklistProps) {
  const initialItems = SETUP_CHECKLISTS[gameId] ?? []
  const [items, setItems] = useState<ChecklistItem[]>(
    initialItems.map((item) => ({ ...item }))
  )

  const toggleItem = (id: string) => {
    setItems((prev) =>
      prev.map((item) => (item.id === id ? { ...item, checked: !item.checked } : item))
    )
  }

  const completedCount = items.filter((i) => i.checked).length
  const allComplete = completedCount === items.length && items.length > 0

  if (items.length === 0) {
    return <p className="text-sm text-gray-400">No setup checklist available for this game.</p>
  }

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Setup Checklist</h3>
        <span className="text-sm text-gray-500">
          {completedCount}/{items.length}
        </span>
      </div>

      <div className="w-full bg-gray-200 rounded-full h-1.5 mb-4">
        <div
          className={`h-1.5 rounded-full transition-all duration-300 ${allComplete ? 'bg-green-500' : 'bg-indigo-500'}`}
          style={{ width: `${(completedCount / items.length) * 100}%` }}
        />
      </div>

      <ul className="space-y-2">
        {items.map((item) => (
          <li key={item.id}>
            <label className="flex items-start gap-3 cursor-pointer group py-1">
              <input
                type="checkbox"
                checked={item.checked}
                onChange={() => toggleItem(item.id)}
                className="mt-0.5 w-5 h-5 rounded border-gray-300 text-indigo-500 focus:ring-indigo-500 cursor-pointer"
              />
              <span className={`text-sm leading-relaxed ${item.checked ? 'text-gray-400 line-through' : 'text-gray-700'}`}>
                {item.text}
              </span>
            </label>
          </li>
        ))}
      </ul>

      {allComplete && (
        <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg text-sm text-green-700 text-center">
          Setup complete! You're ready to play.
        </div>
      )}
    </div>
  )
}
