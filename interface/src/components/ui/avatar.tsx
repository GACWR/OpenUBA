'use client'

import * as React from 'react'
import { cn } from '@/lib/utils'

interface AvatarProps extends React.HTMLAttributes<HTMLDivElement> {
  src?: string
  alt?: string
  initials?: string
  size?: 'sm' | 'md' | 'lg' | 'xl'
}

export function Avatar({
  src,
  alt,
  initials,
  size = 'md',
  className,
  ...props
}: Omit<AvatarProps, 'borderColor' | 'status'> & { borderColor?: never, status?: never }) {
  const sizeClasses = {
    sm: 'h-8 w-8 text-xs',
    md: 'h-10 w-10 text-sm',
    lg: 'h-12 w-12 text-base',
    xl: 'h-16 w-16 text-lg',
  }

  return (
    <div className={cn("relative inline-flex items-center justify-center", className)} {...props}>
      <div className={cn(
        "rounded-full flex items-center justify-center font-semibold overflow-hidden bg-muted text-muted-foreground",
        sizeClasses[size]
      )}>
        {src ? (
          <img src={src} alt={alt} className="w-full h-full object-cover" />
        ) : (
          <span>{initials || 'U'}</span>
        )}
      </div>
    </div>
  )
}

