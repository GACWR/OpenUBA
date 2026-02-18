'use client'

import * as React from 'react'
import { Sidebar } from './sidebar'
import { Topbar } from './topbar'
import { BackgroundPattern } from './background-pattern'
import { SystemLogDock } from '@/components/global/system-log-dock'
import { CommandPalette } from '@/components/global/command-palette'
import { useRouter } from 'next/navigation'

interface AppShellProps {
  children: React.ReactNode
}

export function AppShell({ children }: AppShellProps) {
  const [isCommandPaletteOpen, setIsCommandPaletteOpen] = React.useState(false)
  const router = useRouter()

  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        setIsCommandPaletteOpen(true)
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])

  const commands = [
    { id: 'home', label: 'Go to Dashboard', action: () => router.push('/') },
    { id: 'models', label: 'Go to Models', action: () => router.push('/models') },
    { id: 'anomalies', label: 'Go to Anomalies', action: () => router.push('/anomalies') },
    { id: 'cases', label: 'Go to Cases', action: () => router.push('/cases') },
    { id: 'data', label: 'Go to Data Management', action: () => router.push('/data') },
    { id: 'settings', label: 'Go to Settings', action: () => router.push('/settings') },
  ]

  return (
    <div className="flex h-screen overflow-hidden bg-background relative">
      <BackgroundPattern />
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden relative z-10">
        <Topbar onCommandPaletteOpen={() => setIsCommandPaletteOpen(true)} />
        <main className="flex-1 overflow-y-auto p-6 pb-12">
          {children}
        </main>
        <SystemLogDock />
      </div>
      <CommandPalette
        isOpen={isCommandPaletteOpen}
        onClose={() => setIsCommandPaletteOpen(false)}
        commands={commands}
      />
    </div>
  )
}
