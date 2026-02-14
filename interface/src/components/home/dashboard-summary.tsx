'use client'

import * as React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Users, AlertTriangle, Boxes, Briefcase, Activity, Shield, UserCheck, Database } from 'lucide-react'

interface DashboardSummaryProps {
  summary: {
    total_models?: number
    active_models?: number
    total_anomalies?: number
    unacknowledged_anomalies?: number
    open_cases?: number
    monitored_users?: number
    high_risk_users?: number
    users_discovered?: number
  }
}

const kpiConfig = [
  { key: 'monitored_users', label: 'Monitored Users', icon: Users },
  { key: 'high_risk_users', label: 'High Risk Users', icon: Shield },
  { key: 'users_discovered', label: 'Users Discovered', icon: UserCheck },
  { key: 'total_models', label: 'Total Models', icon: Boxes },
  { key: 'active_models', label: 'Active Models', icon: Activity },
  { key: 'total_anomalies', label: 'Total Anomalies', icon: AlertTriangle },
  { key: 'unacknowledged_anomalies', label: 'Unacknowledged', icon: AlertTriangle },
  { key: 'open_cases', label: 'Open Cases', icon: Briefcase },
]

export function DashboardSummary({ summary }: DashboardSummaryProps) {
  const kpis = kpiConfig.map(config => ({
    ...config,
    value: summary[config.key as keyof typeof summary] || 0,
    Icon: config.icon
  }))

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
      {kpis.map((kpi) => {
        const Icon = kpi.Icon
        return (
          <Card key={kpi.key} className="group hover:bg-muted/50 transition-colors">
            <CardContent className="pt-3 pb-3 px-3">
              <div className="flex items-center gap-2 mb-1">
                <Icon className="h-3.5 w-3.5 text-muted-foreground group-hover:text-foreground transition-colors" />
                <span className="text-[10px] font-medium uppercase tracking-wide text-muted-foreground">{kpi.label}</span>
              </div>
              <div className="text-xl font-bold tabular-nums">{kpi.value.toLocaleString()}</div>
            </CardContent>
          </Card>
        )
      })}
    </div>
  )
}
