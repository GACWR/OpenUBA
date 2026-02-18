'use client'

import * as React from 'react'
import { useRouter } from 'next/navigation'
import { Breadcrumbs } from './breadcrumbs'
import { ThemeToggle } from '@/components/ui/theme-toggle'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Search, Bell, HelpCircle, LogOut, Settings, Check, CheckCheck } from 'lucide-react'
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
} from '@/components/ui/dropdown-menu'
import {
  Popover,
  PopoverTrigger,
  PopoverContent,
} from '@/components/ui/popover'
import { useAuth } from '@/lib/auth-provider'
import { cn } from '@/lib/utils'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface TopbarProps {
  onCommandPaletteOpen?: () => void
}

type Notification = {
  id: string
  title: string
  message: string
  type: string
  read: boolean
  link?: string
  created_at: string
}

function timeAgo(dateStr: string): string {
  const now = Date.now()
  const then = new Date(dateStr).getTime()
  const diff = Math.floor((now - then) / 1000)
  if (diff < 60) return 'just now'
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
  return `${Math.floor(diff / 86400)}d ago`
}

function NotificationIcon({ type }: { type: string }) {
  const colors: Record<string, string> = {
    info: 'text-blue-400',
    success: 'text-green-400',
    warning: 'text-amber-400',
    error: 'text-red-400',
  }
  return <div className={cn('h-2 w-2 rounded-full', colors[type] || 'bg-blue-400')} style={{ backgroundColor: 'currentColor' }} />
}

export function Topbar({ onCommandPaletteOpen }: TopbarProps) {
  const { user, logout, authFetch } = useAuth()
  const router = useRouter()
  const [notifications, setNotifications] = React.useState<Notification[]>([])
  const [unreadCount, setUnreadCount] = React.useState(0)
  const [notifOpen, setNotifOpen] = React.useState(false)

  const fetchUnreadCount = React.useCallback(async () => {
    try {
      const res = await authFetch(`${API_URL}/api/v1/notifications/unread-count`)
      if (res.ok) {
        const data = await res.json()
        setUnreadCount(data.count)
      }
    } catch {}
  }, [authFetch])

  const fetchNotifications = React.useCallback(async () => {
    try {
      const res = await authFetch(`${API_URL}/api/v1/notifications?limit=20`)
      if (res.ok) {
        const data = await res.json()
        setNotifications(data)
      }
    } catch {}
  }, [authFetch])

  // poll unread count every 30s
  React.useEffect(() => {
    fetchUnreadCount()
    const interval = setInterval(fetchUnreadCount, 30000)
    return () => clearInterval(interval)
  }, [fetchUnreadCount])

  // fetch notifications when popover opens
  React.useEffect(() => {
    if (notifOpen) {
      fetchNotifications()
    }
  }, [notifOpen, fetchNotifications])

  const markRead = async (id: string) => {
    await authFetch(`${API_URL}/api/v1/notifications/${id}/read`, { method: 'PUT' })
    setNotifications((prev) => prev.map((n) => (n.id === id ? { ...n, read: true } : n)))
    setUnreadCount((c) => Math.max(0, c - 1))
  }

  const markAllRead = async () => {
    await authFetch(`${API_URL}/api/v1/notifications/read-all`, { method: 'PUT' })
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })))
    setUnreadCount(0)
  }

  const handleLogout = () => {
    logout()
    router.replace('/login')
  }

  const initials = user
    ? (user.display_name || user.username).slice(0, 2).toUpperCase()
    : 'U'

  const roleBadgeColor: Record<string, string> = {
    admin: 'bg-red-500/20 text-red-400 border-red-500/30',
    manager: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
    triage: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
    analyst: 'bg-green-500/20 text-green-400 border-green-500/30',
  }

  return (
    <div className="flex h-16 items-center justify-between border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 px-6">
      <Breadcrumbs />
      <div className="flex items-center gap-3">
        <ThemeToggle />
        <div className="relative hidden md:block">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            type="search"
            placeholder="Search... (Cmd+K)"
            className="h-9 w-64 pl-9 bg-muted/50 border-input focus:border-primary/50 focus:ring-primary/20 cursor-pointer"
            onClick={onCommandPaletteOpen}
            readOnly
          />
        </div>

        {/* notifications */}
        <Popover open={notifOpen} onOpenChange={setNotifOpen}>
          <PopoverTrigger asChild>
            <Button variant="ghost" size="icon" className="h-9 w-9 relative">
              <Bell className="h-4 w-4" />
              {unreadCount > 0 && (
                <span className="absolute -top-0.5 -right-0.5 h-4 min-w-[16px] px-1 rounded-full bg-destructive text-[10px] font-bold text-white flex items-center justify-center">
                  {unreadCount > 99 ? '99+' : unreadCount}
                </span>
              )}
              <span className="sr-only">Notifications</span>
            </Button>
          </PopoverTrigger>
          <PopoverContent align="end" className="w-80 p-0">
            <div className="flex items-center justify-between px-4 py-3 border-b">
              <h4 className="text-sm font-semibold">Notifications</h4>
              {unreadCount > 0 && (
                <button onClick={markAllRead} className="text-xs text-muted-foreground hover:text-foreground flex items-center gap-1">
                  <CheckCheck className="h-3 w-3" /> Mark all read
                </button>
              )}
            </div>
            <div className="max-h-96 overflow-y-auto">
              {notifications.length === 0 ? (
                <div className="px-4 py-8 text-center text-sm text-muted-foreground">No notifications</div>
              ) : (
                notifications.map((n) => (
                  <div
                    key={n.id}
                    className={cn(
                      'flex items-start gap-3 px-4 py-3 border-b last:border-0 hover:bg-muted/50 cursor-pointer transition-colors',
                      !n.read && 'bg-muted/30'
                    )}
                    onClick={() => {
                      if (!n.read) markRead(n.id)
                      if (n.link) router.push(n.link)
                    }}
                  >
                    <div className="mt-1.5">
                      <NotificationIcon type={n.type} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium flex items-center gap-2">
                        {n.title}
                        {!n.read && <span className="h-1.5 w-1.5 rounded-full bg-cyan-500 flex-shrink-0" />}
                      </div>
                      <p className="text-xs text-muted-foreground line-clamp-2 mt-0.5">{n.message}</p>
                      <p className="text-xs text-muted-foreground/60 mt-1">{timeAgo(n.created_at)}</p>
                    </div>
                  </div>
                ))
              )}
            </div>
          </PopoverContent>
        </Popover>

        <Button variant="ghost" size="icon" className="h-9 w-9">
          <HelpCircle className="h-4 w-4" />
          <span className="sr-only">Help</span>
        </Button>

        {/* user dropdown */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button className="flex items-center gap-2 pl-3 border-l cursor-pointer hover:opacity-80 transition-opacity outline-none">
              <div className="h-8 w-8 rounded-full bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center text-xs font-bold text-white ring-1 ring-white/20">
                {initials}
              </div>
              <div className="hidden md:block text-left">
                <div className="text-sm font-medium">{user?.display_name || user?.username || 'User'}</div>
                <div className="text-xs text-muted-foreground capitalize">{user?.role || 'analyst'}</div>
              </div>
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            <DropdownMenuLabel className="font-normal">
              <div className="flex flex-col gap-1">
                <p className="text-sm font-medium">{user?.display_name || user?.username}</p>
                <p className="text-xs text-muted-foreground">{user?.email || ''}</p>
                <Badge variant="outline" className={cn('w-fit text-[10px] mt-1', roleBadgeColor[user?.role || 'analyst'])}>
                  {user?.role}
                </Badge>
              </div>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={() => router.push('/settings')}>
              <Settings className="mr-2 h-4 w-4" />
              Settings
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={handleLogout} className="text-destructive focus:text-destructive">
              <LogOut className="mr-2 h-4 w-4" />
              Sign out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </div>
  )
}
