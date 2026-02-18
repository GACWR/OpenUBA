'use client'

import * as React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Gauge } from 'lucide-react'
import { cn } from '@/lib/utils'

interface StatusGaugeProps {
  title?: string
  value: number
  max?: number
  status?: 'healthy' | 'warning' | 'critical'
  height?: number
}

export function StatusGauge({
  title = 'System Status',
  value,
  max = 100,
  status = 'healthy',
  height = 200
}: StatusGaugeProps) {
  const percentage = Math.min((value / max) * 100, 100)

  const statusColors = {
    healthy: { color: '#10b981', bg: 'bg-green-500/20', border: 'border-green-500/30', text: 'text-green-400' },
    warning: { color: '#f59e0b', bg: 'bg-orange-500/20', border: 'border-orange-500/30', text: 'text-orange-400' },
    critical: { color: '#ef4444', bg: 'bg-red-500/20', border: 'border-red-500/30', text: 'text-red-400' },
  }

  const statusConfig = statusColors[status]

  // simple gauge visualization
  const angle = (percentage / 100) * 180 - 90 // -90 to 90 degrees

  return (
    <Card className="hover:shadow-card-hover transition-all">
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle className="text-lg font-semibold">{title}</CardTitle>
          <p className="text-xs text-muted-foreground mt-1">{value} / {max}</p>
        </div>
        <div className="h-10 w-10 rounded-lg bg-muted flex items-center justify-center">
          <Gauge className="h-5 w-5 text-muted-foreground" />
        </div>
      </CardHeader>
      <CardContent>
        <div style={{ height }} className="relative flex items-center justify-center">
          <div className="relative w-32 h-32">
            <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
              <circle
                cx="50"
                cy="50"
                r="40"
                fill="none"
                stroke="hsl(var(--muted))"
                strokeWidth="8"
                className="opacity-20"
              />
              <circle
                cx="50"
                cy="50"
                r="40"
                fill="none"
                stroke={statusConfig.color}
                strokeWidth="8"
                strokeLinecap="round"
                strokeDasharray={`${(percentage / 100) * 251.2} 251.2`}
                className="transition-all duration-500"
                style={{ filter: `drop-shadow(0 0 8px ${statusConfig.color}60)` }}
              />
            </svg>
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-center">
                <div className={cn("text-3xl font-bold", statusConfig.text)}>{Math.round(percentage)}%</div>
                <div className="text-xs text-muted-foreground mt-1 capitalize">{status}</div>
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

