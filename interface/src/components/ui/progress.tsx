'use client'

import * as React from 'react'
import { cn } from '@/lib/utils'

interface ProgressProps extends React.HTMLAttributes<HTMLDivElement> {
  value: number
  max?: number
  variant?: 'default' | 'gradient' | 'purple' | 'orange' | 'cyan'
  showLabel?: boolean
  height?: number
}

const variantClasses = {
  default: 'bg-primary',
  gradient: 'bg-gradient-purple-orange',
  purple: 'bg-gradient-to-r from-purple-500 to-purple-600',
  orange: 'bg-gradient-to-r from-orange-500 to-orange-600',
  cyan: 'bg-gradient-to-r from-cyan-500 to-cyan-600',
}

export function Progress({ 
  value, 
  max = 100, 
  variant = 'gradient',
  showLabel = false,
  height = 8,
  className,
  ...props 
}: ProgressProps) {
  const percentage = Math.min((value / max) * 100, 100)
  
  return (
    <div className={cn("relative w-full", className)} {...props}>
      <div 
        className="w-full rounded-full bg-muted overflow-hidden"
        style={{ height }}
      >
        <div
          className={cn(
            "h-full rounded-full transition-all duration-500 ease-out",
            variantClasses[variant],
            'shadow-sm'
          )}
          style={{ width: `${percentage}%` }}
        />
      </div>
      {showLabel && (
        <div className="absolute inset-0 flex items-center justify-center text-xs font-medium text-foreground">
          {Math.round(percentage)}%
        </div>
      )}
    </div>
  )
}

