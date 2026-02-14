'use client'

import * as React from 'react'
import { cn } from '@/lib/utils'

interface BackgroundPatternProps {
  className?: string
}

export function BackgroundPattern({ className }: BackgroundPatternProps) {
  return (
    <div
      className={cn(
        "fixed inset-0 -z-10 opacity-30 pointer-events-none",
        className
      )}
      style={{
        backgroundImage: `
          linear-gradient(rgba(147, 51, 234, 0.03) 1px, transparent 1px),
          linear-gradient(90deg, rgba(147, 51, 234, 0.03) 1px, transparent 1px)
        `,
        backgroundSize: '50px 50px',
      }}
    >
      <div className="absolute inset-0 bg-gradient-to-br from-background via-transparent to-background" />
    </div>
  )
}

