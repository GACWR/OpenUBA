'use client'

import * as React from 'react'
import { usePathname } from 'next/navigation'
import Link from 'next/link'
import { ChevronRight, Home } from 'lucide-react'
import { cn } from '@/lib/utils'

export function Breadcrumbs() {
  const pathname = usePathname()
  const paths = (pathname || '').split('/').filter(Boolean)

  const breadcrumbs = [
    { name: 'Home', href: '/' },
    ...paths.map((path, index) => ({
      name: path.charAt(0).toUpperCase() + path.slice(1),
      href: '/' + paths.slice(0, index + 1).join('/'),
    })),
  ]

  return (
    <nav className="flex items-center gap-2 text-sm">
      <Link
        href="/"
        className="text-muted-foreground hover:text-foreground transition-colors"
      >
        <Home className="h-4 w-4" />
      </Link>
      {breadcrumbs.length > 1 && (
        <>
          <ChevronRight className="h-4 w-4 text-muted-foreground" />
          {breadcrumbs.slice(1).map((crumb, index) => (
            <React.Fragment key={crumb.href}>
              {index < breadcrumbs.length - 2 ? (
                <Link
                  href={crumb.href}
                  className="text-muted-foreground hover:text-foreground transition-colors"
                >
                  {crumb.name}
                </Link>
              ) : (
                <span className="text-foreground font-medium">{crumb.name}</span>
              )}
              {index < breadcrumbs.length - 2 && (
                <ChevronRight className="h-4 w-4 text-muted-foreground" />
              )}
            </React.Fragment>
          ))}
        </>
      )}
    </nav>
  )
}
