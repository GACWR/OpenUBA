'use client'

import * as React from 'react'
import { usePathname } from 'next/navigation'
import { useAuth } from '@/lib/auth-provider'
import { AppShell } from './app-shell'
import { LLMChatWindow } from '@/components/global/llm-chat/chat-window'

export function AuthenticatedShell({ children }: { children: React.ReactNode }) {
  const { user } = useAuth()
  const pathname = usePathname()

  // login page or unauthenticated — render children directly (no shell)
  if (!user || pathname === '/login') {
    return <>{children}</>
  }

  return (
    <>
      <AppShell>{children}</AppShell>
      <LLMChatWindow />
    </>
  )
}
