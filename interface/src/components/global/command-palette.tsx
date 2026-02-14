'use client'

import { useState, useEffect } from 'react'
import { Input } from '@/components/ui/input'
import { Card, CardContent } from '@/components/ui/card'

interface Command {
  id: string
  label: string
  action: () => void
}

interface CommandPaletteProps {
  isOpen: boolean
  onClose: () => void
  commands: Command[]
}

export function CommandPalette({ isOpen, onClose, commands }: CommandPaletteProps) {
  const [search, setSearch] = useState('')
  const [filteredCommands, setFilteredCommands] = useState(commands)

  useEffect(() => {
    if (search) {
      setFilteredCommands(
        commands.filter(cmd => 
          cmd.label.toLowerCase().includes(search.toLowerCase())
        )
      )
    } else {
      setFilteredCommands(commands)
    }
  }, [search, commands])

  useEffect(() => {
    if (isOpen) {
      const handleKeyDown = (e: KeyboardEvent) => {
        if (e.key === 'Escape') onClose()
      }
      window.addEventListener('keydown', handleKeyDown)
      return () => window.removeEventListener('keydown', handleKeyDown)
    }
  }, [isOpen, onClose])

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50 flex items-start justify-center pt-32" onClick={onClose}>
      <Card className="w-full max-w-2xl" onClick={(e) => e.stopPropagation()}>
        <CardContent className="pt-6">
          <Input
            placeholder="type a command..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            autoFocus
            className="mb-4"
          />
          <div className="space-y-1 max-h-96 overflow-auto">
            {filteredCommands.map((cmd) => (
              <button
                key={cmd.id}
                onClick={() => {
                  cmd.action()
                  onClose()
                }}
                className="w-full text-left px-4 py-2 hover:bg-accent rounded-md"
              >
                {cmd.label}
              </button>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

