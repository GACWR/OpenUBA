'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { StatusGauge } from '@/components/home/status-gauge'
import { Activity } from 'lucide-react'

interface PipelineStatusProps {
  status: 'idle' | 'running' | 'error'
  lastRun?: string
  nextRun?: string
}

export function PipelineStatus({ status, lastRun, nextRun }: PipelineStatusProps) {
  const statusVariant = status === 'running' ? 'success' : status === 'error' ? 'error' : 'default'
  const healthValue = status === 'running' ? 90 : status === 'error' ? 30 : 70
  const healthStatus = status === 'running' ? 'healthy' : status === 'error' ? 'critical' : 'warning'

  return (
    <Card className="hover:shadow-card-hover transition-all">
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle className="text-lg font-semibold">Pipeline Status</CardTitle>
          <p className="text-xs text-muted-foreground mt-1">ingestion pipeline health</p>
        </div>
        <div className="h-10 w-10 rounded-lg bg-muted flex items-center justify-center">
          <Activity className="h-5 w-5 text-muted-foreground" />
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
          <span className="text-sm text-muted-foreground">status:</span>
          <Badge variant={statusVariant} size="sm">{status}</Badge>
        </div>
        {lastRun && (
          <div className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
            <span className="text-sm text-muted-foreground">last run:</span>
            <span className="text-sm font-medium">{new Date(lastRun).toLocaleString()}</span>
          </div>
        )}
        {nextRun && (
          <div className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
            <span className="text-sm text-muted-foreground">next run:</span>
            <span className="text-sm font-medium">{new Date(nextRun).toLocaleString()}</span>
          </div>
        )}
        <div className="pt-2">
          <StatusGauge
            title="Pipeline Health"
            value={healthValue}
            status={healthStatus}
            height={150}
          />
        </div>
      </CardContent>
    </Card>
  )
}

