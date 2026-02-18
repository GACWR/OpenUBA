'use client'

import * as React from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  Home,
  Database,
  Boxes,
  AlertTriangle,
  Briefcase,
  Settings,
  Gavel,
  Calendar,
  Users,
  Bell,
  Shield,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useAuth } from '@/lib/auth-provider'

// page key maps to permission page name
const navigationGroups = [
  {
    name: 'Core',
    items: [
      { name: 'Home', href: '/', icon: Home, color: 'purple', page: 'home' },
      { name: 'Data', href: '/data', icon: Database, color: 'cyan', page: 'data' },
    ]
  },
  {
    name: 'Analytics',
    items: [
      { name: 'Models', href: '/models', icon: Boxes, color: 'orange', page: 'models' },
      { name: 'Rules', href: '/rules', icon: Gavel, color: 'pink', page: 'rules' },
      { name: 'Alerts', href: '/alerts', icon: Bell, color: 'amber', page: 'alerts' },
      { name: 'Entities', href: '/entities', icon: Users, color: 'emerald', page: 'entities' },
      { name: 'Anomalies', href: '/anomalies', icon: AlertTriangle, color: 'red', page: 'anomalies' },
      { name: 'Cases', href: '/cases', icon: Briefcase, color: 'blue', page: 'cases' },
    ]
  },
  {
    name: 'Management',
    items: [
      { name: 'Schedules', href: '/schedules', icon: Calendar, color: 'green', page: 'schedules' },
      { name: 'Users', href: '/users', icon: Shield, color: 'teal', page: 'users' },
      { name: 'Settings', href: '/settings', icon: Settings, color: 'indigo', page: 'settings' },
    ]
  },
]

export function Sidebar() {
  const currentPath = usePathname()
  const { user, hasPermission } = useAuth()

  const initials = user
    ? (user.display_name || user.username).slice(0, 2).toUpperCase()
    : 'U'

  return (
    <div className="flex w-64 flex-col border-r border-white/10 bg-black/40 backdrop-blur-xl">
      <div className="flex h-16 items-center px-6 border-b border-white/5">
        <div className="flex items-center gap-2">
          <img
            src="/images/openuba-logo-light.png"
            alt="OpenUBA"
            className="h-8 w-auto object-contain"
          />
        </div>
      </div>

      <nav className="flex-1 space-y-6 px-4 py-6 overflow-y-auto">
        {navigationGroups.map((group) => {
          const visibleItems = group.items.filter((item) => hasPermission(item.page))
          if (visibleItems.length === 0) return null

          return (
            <div key={group.name} className="space-y-1">
              <div className="px-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
                {group.name}
              </div>
              {visibleItems.map((item) => {
                const isActive = currentPath === item.href
                const Icon = item.icon

                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    className={cn(
                      'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors',
                      isActive
                        ? 'bg-secondary text-secondary-foreground'
                        : 'text-muted-foreground hover:bg-secondary/50 hover:text-foreground'
                    )}
                  >
                    <Icon className="h-4 w-4" />
                    {item.name}
                  </Link>
                )
              })}
            </div>
          )
        })}
      </nav>

      <div className="border-t border-white/5 p-4">
        <div className="flex items-center gap-3 px-3 py-2 rounded-lg bg-white/5">
          <div className="h-8 w-8 rounded-full bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center text-white text-xs font-bold">
            {initials}
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-xs font-medium text-foreground">{user?.display_name || user?.username || 'User'}</div>
            <div className="text-xs text-muted-foreground truncate capitalize">{user?.role || 'analyst'}</div>
          </div>
          <div className="h-2 w-2 rounded-full bg-green-500" />
        </div>
      </div>
    </div>
  )
}
