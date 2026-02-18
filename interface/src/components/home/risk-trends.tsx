'use client'

import * as React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { TimeseriesChart } from '@/components/charts/timeseries-chart'
import { TrendingUp } from 'lucide-react'

interface RiskTrendsProps {
  data?: Array<{
    date: string
    low: number
    medium: number
    high: number
    critical: number
  }>
}

export function RiskTrends({ data = [] }: RiskTrendsProps) {
  const chartData = data.length > 0 ? data : [
    { date: '2024-01-01', low: 10, medium: 5, high: 2, critical: 0 },
    { date: '2024-01-02', low: 12, medium: 6, high: 3, critical: 1 },
    { date: '2024-01-03', low: 8, medium: 4, high: 1, critical: 0 },
    { date: '2024-01-04', low: 15, medium: 8, high: 4, critical: 2 },
    { date: '2024-01-05', low: 18, medium: 10, high: 5, critical: 3 },
  ]

  return (
    <Card className="hover:bg-muted/50 transition-colors">
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle className="text-lg font-semibold">Risk Over Time</CardTitle>
          <p className="text-xs text-muted-foreground mt-1">security risk trends</p>
        </div>
        <TrendingUp className="h-5 w-5 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <TimeseriesChart
          data={chartData}
          xKey="date"
          yKeys={[
            { key: 'low', name: 'Low', color: '#10b981' },
            { key: 'medium', name: 'Medium', color: '#f59e0b' },
            { key: 'high', name: 'High', color: '#ef4444' },
            { key: 'critical', name: 'Critical', color: '#dc2626' },
          ]}
          height={300}
        />
      </CardContent>
    </Card>
  )
}
