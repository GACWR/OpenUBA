'use client'

import { createContext, useContext, useState, useCallback, useRef, useEffect, ReactNode } from 'react'
import { CheckCircle2, XCircle, AlertTriangle, Info, X, Loader2 } from 'lucide-react'

type ToastType = 'success' | 'error' | 'info' | 'warning'

interface ToastOptions {
  description?: string
  type?: ToastType
  duration?: number // ms, 0 = persistent until manually dismissed
}

interface Toast {
  id: string
  title: string
  description?: string
  type: ToastType
  duration: number
  createdAt: number
  exiting: boolean
}

interface ToastContextType {
  toasts: Toast[]
  addToast: (title: string, typeOrOptions?: ToastType | ToastOptions) => string
  removeToast: (id: string) => void
}

const ToastContext = createContext<ToastContextType | undefined>(undefined)

const DEFAULT_DURATION = 10000
const EXIT_DURATION = 400

const toastConfig: Record<ToastType, {
  icon: typeof CheckCircle2
  bg: string
  border: string
  title: string
  desc: string
  iconColor: string
  progressColor: string
  glowColor: string
}> = {
  success: {
    icon: CheckCircle2,
    bg: 'bg-[#0a1f1a]/95',
    border: 'border-emerald-500/20',
    title: 'text-emerald-50',
    desc: 'text-emerald-200/70',
    iconColor: 'text-emerald-400',
    progressColor: 'bg-emerald-400/40',
    glowColor: 'shadow-emerald-500/10',
  },
  error: {
    icon: XCircle,
    bg: 'bg-[#1f0a0a]/95',
    border: 'border-red-500/20',
    title: 'text-red-50',
    desc: 'text-red-200/70',
    iconColor: 'text-red-400',
    progressColor: 'bg-red-400/40',
    glowColor: 'shadow-red-500/10',
  },
  warning: {
    icon: AlertTriangle,
    bg: 'bg-[#1f1a0a]/95',
    border: 'border-amber-500/20',
    title: 'text-amber-50',
    desc: 'text-amber-200/70',
    iconColor: 'text-amber-400',
    progressColor: 'bg-amber-400/40',
    glowColor: 'shadow-amber-500/10',
  },
  info: {
    icon: Info,
    bg: 'bg-[#0a0f1f]/95',
    border: 'border-blue-500/20',
    title: 'text-blue-50',
    desc: 'text-blue-200/70',
    iconColor: 'text-blue-400',
    progressColor: 'bg-blue-400/40',
    glowColor: 'shadow-blue-500/10',
  },
}

function ProgressBar({ duration, createdAt }: { duration: number; createdAt: number }) {
  const [width, setWidth] = useState(100)
  const rafRef = useRef<number>(0)

  useEffect(() => {
    if (duration <= 0) return

    const animate = () => {
      const elapsed = Date.now() - createdAt
      const remaining = Math.max(0, 1 - elapsed / duration)
      setWidth(remaining * 100)
      if (remaining > 0) {
        rafRef.current = requestAnimationFrame(animate)
      }
    }
    rafRef.current = requestAnimationFrame(animate)
    return () => cancelAnimationFrame(rafRef.current)
  }, [duration, createdAt])

  if (duration <= 0) return null

  return (
    <div className="absolute bottom-0 left-0 right-0 h-[2px] overflow-hidden rounded-b-xl">
      <div
        className="h-full bg-white/15 transition-none"
        style={{ width: `${width}%` }}
      />
    </div>
  )
}

function ToastItem({ toast, onRemove }: { toast: Toast; onRemove: (id: string) => void }) {
  const config = toastConfig[toast.type]
  const Icon = config.icon

  return (
    <div
      className={`
        relative flex items-start gap-3 pl-4 pr-3 py-3.5 rounded-xl border backdrop-blur-xl
        min-w-[360px] max-w-[440px] overflow-hidden
        shadow-lg ${config.glowColor}
        ${config.bg} ${config.border}
        ${toast.exiting ? 'animate-toast-out' : 'animate-toast-in'}
      `}
      role="alert"
    >
      <div className={`mt-0.5 shrink-0 ${config.iconColor}`}>
        <Icon className="w-[18px] h-[18px]" strokeWidth={2} />
      </div>

      <div className="flex-1 min-w-0 space-y-0.5">
        <p className={`text-[13px] font-medium leading-tight ${config.title}`}>
          {toast.title}
        </p>
        {toast.description && (
          <p className={`text-[12px] leading-relaxed ${config.desc}`}>
            {toast.description}
          </p>
        )}
      </div>

      <button
        onClick={() => onRemove(toast.id)}
        className="shrink-0 mt-0.5 p-0.5 rounded-md text-white/30 hover:text-white/70 hover:bg-white/5 transition-all"
      >
        <X className="w-3.5 h-3.5" />
      </button>

      <ProgressBar duration={toast.duration} createdAt={toast.createdAt} />
    </div>
  )
}

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([])
  const timersRef = useRef<Map<string, ReturnType<typeof setTimeout>>>(new Map())

  const removeToast = useCallback((id: string) => {
    // clear any existing timer
    const timer = timersRef.current.get(id)
    if (timer) {
      clearTimeout(timer)
      timersRef.current.delete(id)
    }
    // start exit animation
    setToasts((prev) => prev.map((t) => t.id === id ? { ...t, exiting: true } : t))
    // remove after animation completes
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id))
    }, EXIT_DURATION)
  }, [])

  const addToast = useCallback((title: string, typeOrOptions?: ToastType | ToastOptions): string => {
    const id = `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`

    let type: ToastType = 'info'
    let description: string | undefined
    let duration = DEFAULT_DURATION

    if (typeof typeOrOptions === 'string') {
      type = typeOrOptions
    } else if (typeOrOptions && typeof typeOrOptions === 'object') {
      type = typeOrOptions.type || 'info'
      description = typeOrOptions.description
      duration = typeOrOptions.duration !== undefined ? typeOrOptions.duration : DEFAULT_DURATION
    }

    const toast: Toast = {
      id,
      title,
      description,
      type,
      duration,
      createdAt: Date.now(),
      exiting: false,
    }

    setToasts((prev) => [...prev, toast])

    if (duration > 0) {
      const timer = setTimeout(() => {
        timersRef.current.delete(id)
        removeToast(id)
      }, duration)
      timersRef.current.set(id, timer)
    }

    return id
  }, [removeToast])

  // cleanup timers on unmount
  useEffect(() => {
    return () => {
      timersRef.current.forEach((timer) => clearTimeout(timer))
    }
  }, [])

  return (
    <ToastContext.Provider value={{ toasts, addToast, removeToast }}>
      {children}
      <div className="fixed top-5 right-5 z-[100] flex flex-col gap-2.5 pointer-events-none">
        {toasts.map((toast) => (
          <div key={toast.id} className="pointer-events-auto">
            <ToastItem toast={toast} onRemove={removeToast} />
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  )
}

export function useToast() {
  const context = useContext(ToastContext)
  if (!context) throw new Error('useToast must be used within ToastProvider')
  return context
}
