import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { SetupChecklist } from '../SetupChecklist'

describe('SetupChecklist', () => {
  it('renders checklist items for catan', () => {
    render(<SetupChecklist gameId="catan" />)
    expect(screen.getByText('Setup Checklist')).toBeInTheDocument()
    expect(screen.getByText(/Arrange hex tiles/)).toBeInTheDocument()
    expect(screen.getByText('0/10')).toBeInTheDocument()
  })

  it('toggles checkbox items', async () => {
    render(<SetupChecklist gameId="catan" />)
    const checkboxes = screen.getAllByRole('checkbox')
    expect(checkboxes[0]).not.toBeChecked()

    await userEvent.click(checkboxes[0])
    expect(checkboxes[0]).toBeChecked()
    expect(screen.getByText('1/10')).toBeInTheDocument()
  })

  it('shows completion message when all checked', async () => {
    render(<SetupChecklist gameId="ticket-to-ride" />)
    const checkboxes = screen.getAllByRole('checkbox')

    for (const checkbox of checkboxes) {
      await userEvent.click(checkbox)
    }

    expect(screen.getByText(/Setup complete/)).toBeInTheDocument()
  })

  it('shows message for unknown game', () => {
    render(<SetupChecklist gameId="unknown-game" />)
    expect(screen.getByText(/No setup checklist available/)).toBeInTheDocument()
  })

  it('renders checklist for wingspan', () => {
    render(<SetupChecklist gameId="wingspan" />)
    expect(screen.getByText(/player mat/)).toBeInTheDocument()
  })
})
