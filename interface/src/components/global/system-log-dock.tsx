'use client'

import * as React from 'react'
import { Terminal, ChevronUp, ChevronDown, X, Activity } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useAuth } from '@/lib/auth-provider'

interface LogEntry {
    id: string
    timestamp: string
    component: string
    level: 'info' | 'warning' | 'error'
    message: string
}

export function SystemLogDock() {
    const [isOpen, setIsOpen] = React.useState(false)
    const [logs, setLogs] = React.useState<LogEntry[]>([])
    const { authFetch } = useAuth()

    const fetchLogs = React.useCallback(async () => {
        try {
            const response = await authFetch('/api/v1/system/logs?limit=50')
            if (response.ok) {
                const data = await response.json()
                setLogs(data)
            }
        } catch (error) {
            console.error('Failed to fetch system logs:', error)
        }
    }, [authFetch])

    React.useEffect(() => {
        fetchLogs()
        const interval = setInterval(fetchLogs, 5000)
        return () => clearInterval(interval)
    }, [fetchLogs])

    return (
        <div className={cn(
            "fixed bottom-0 left-0 right-0 bg-black/90 border-t border-white/10 transition-all duration-300 z-40 backdrop-blur-md",
            isOpen ? "h-64" : "h-8"
        )}>
            {/* Header / Toggle */}
            <div
                className="h-8 flex items-center justify-between px-4 cursor-pointer hover:bg-white/5 border-b border-white/5"
                onClick={() => setIsOpen(!isOpen)}
            >
                <div className="flex items-center gap-2 text-xs font-mono text-muted-foreground">
                    <Terminal className="h-3 w-3" />
                    <span>SYSTEM LOGS</span>
                    <span className="flex items-center gap-1 ml-4">
                        <Activity className="h-3 w-3 text-green-500" />
                        <span className="text-green-500">ONLINE</span>
                    </span>
                </div>
                <div className="flex items-center gap-2">
                    {isOpen ? <ChevronDown className="h-3 w-3" /> : <ChevronUp className="h-3 w-3" />}
                </div>
            </div>

            {/* Log Content */}
            <div className="h-[calc(100%-2rem)] overflow-y-auto p-2 font-mono text-xs">
                <table className="w-full text-left border-collapse">
                    <tbody>
                        {logs.map((log) => (
                            <tr key={log.id} className="hover:bg-white/5 border-b border-white/5 last:border-0">
                                <td className="py-1 px-2 text-muted-foreground w-32 whitespace-nowrap">
                                    {new Date(log.timestamp).toLocaleTimeString()}
                                </td>
                                <td className="py-1 px-2 w-24">
                                    <span className={cn(
                                        "px-1.5 py-0.5 rounded text-[10px] uppercase font-bold",
                                        log.level === 'error' ? "bg-red-500/20 text-red-400" :
                                            log.level === 'warning' ? "bg-yellow-500/20 text-yellow-400" :
                                                "bg-blue-500/20 text-blue-400"
                                    )}>
                                        {log.level}
                                    </span>
                                </td>
                                <td className="py-1 px-2 w-32 text-cyan-400">[{log.component}]</td>
                                <td className="py-1 px-2 text-gray-300">{log.message}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    )
}
