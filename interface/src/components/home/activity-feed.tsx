'use client'

import * as React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Clock, User } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Badge } from '@/components/ui/badge'

interface ActivityItem {
  id: string
  user: string
  action: string
  timestamp: string
  type?: 'info' | 'success' | 'warning' | 'error'
}

const defaultActivities: ActivityItem[] = [
  { id: '1', user: 'System', action: 'model execution completed', timestamp: '2m ago', type: 'success' },
  { id: '2', user: 'Admin', action: 'new anomaly detected', timestamp: '5m ago', type: 'warning' },
  { id: '3', user: 'Analyst', action: 'case created', timestamp: '10m ago', type: 'info' },
]

interface ActivityFeedProps {
  title?: string
  anomalies?: any[]
  cases?: any[]
  maxItems?: number
}

export function ActivityFeed({
  title = 'Recent Activity',
  anomalies = [],
  cases = [],
  maxItems = 5
}: ActivityFeedProps) {
  // Map anomalies and cases to activities
  const anomalyActivities: ActivityItem[] = anomalies.map(a => ({
    id: `anomaly-${a.id}`,
    user: 'System',
    action: `Anomaly detected: ${a.anomalyType}`,
    timestamp: new Date(a.timestamp).toLocaleTimeString(),
    type: a.riskScore > 80 ? 'error' : 'warning'
  }))

  const caseActivities: ActivityItem[] = cases.map(c => ({
    id: `case-${c.id}`,
    user: 'Analyst',
    action: `Case created: ${c.title}`,
    timestamp: new Date(c.createdAt).toLocaleTimeString(),
    type: 'info'
  }))

  const allActivities = [...anomalyActivities, ...caseActivities]
    .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
    .slice(0, maxItems)

  const displayActivities = allActivities.length > 0 ? allActivities : defaultActivities

  return (
    <Card className="hover:bg-muted/50 transition-colors">
      <CardHeader>
        <CardTitle className="text-lg font-semibold">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {displayActivities.map((activity) => {
            const initials = activity.user.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)

            return (
              <div key={activity.id} className="flex items-start gap-3 p-3 rounded-lg hover:bg-muted/50 transition-colors">
                <div className="h-10 w-10 rounded-full flex items-center justify-center text-xs font-bold border bg-muted text-muted-foreground">
                  {initials || <User className="h-4 w-4" />}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-sm font-medium">{activity.user}</span>
                    <Badge variant={activity.type || 'info'} className="text-[10px] px-1.5 py-0 h-5">
                      {activity.type || 'info'}
                    </Badge>
                  </div>
                  <p className="text-sm text-muted-foreground">{activity.action}</p>
                  <div className="flex items-center gap-1 text-xs text-muted-foreground mt-1">
                    <Clock className="h-3 w-3" />
                    {activity.timestamp}
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </CardContent>
    </Card>
  )
}

