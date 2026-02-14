'use client'

import * as React from 'react'
import { useAuth } from '@/lib/auth-provider'
import { usePathname, useRouter } from 'next/navigation'
import { Loader2 } from 'lucide-react'

export function AuthGate({ children }: { children: React.ReactNode }) {
  const { user, isLoading } = useAuth()
  const pathname = usePathname()
  const router = useRouter()

  React.useEffect(() => {
    if (!isLoading && !user && pathname !== '/login') {
      router.replace('/login')
    }
  }, [isLoading, user, pathname, router])

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-[#0a0a1a]">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="h-8 w-8 animate-spin text-cyan-500" />
          <p className="text-sm text-white/50">Loading...</p>
        </div>
      </div>
    )
  }

  // on login page, render children directly (no app shell)
  if (pathname === '/login') {
    return <>{children}</>
  }

  // not authenticated and not on login page — show nothing (useEffect will redirect)
  if (!user) {
    return (
      <div className="flex h-screen items-center justify-center bg-[#0a0a1a]">
        <Loader2 className="h-8 w-8 animate-spin text-cyan-500" />
      </div>
    )
  }

  return <>{children}</>
}
