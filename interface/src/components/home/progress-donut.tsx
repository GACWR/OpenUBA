'use client'

import * as React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { DonutChart } from '@/components/charts/donut-chart'
import { Target } from 'lucide-react'

interface ProgressDonutProps {
  title?: string
  percentage: number
  segments?: Array<{ name: string; value: number; color: string }>
  height?: number
}

export function ProgressDonut({
  title = 'Progress',
  percentage,
  segments = [
    { name: 'Complete', value: percentage, color: '#9333ea' },
    { name: 'Remaining', value: 100 - percentage, color: '#1f2937' }
  ],
  height = 250
}: ProgressDonutProps) {
  return (
    <Card className="hover:bg-muted/50 transition-colors">
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle className="text-lg font-semibold">{title}</CardTitle>
          <p className="text-xs text-muted-foreground mt-1">{percentage}% complete</p>
        </div>
        <Target className="h-5 w-5 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <DonutChart
          data={segments}
          height={height}
          showCenterLabel={true}
          centerLabel={`${percentage}%`}
          colors={segments.map(s => s.color)}
        />
        <div className="mt-4 space-y-2">
          {segments.map((segment, idx) => (
            <div key={idx} className="flex items-center justify-between text-sm">
              <div className="flex items-center gap-2">
                <div
                  className="h-3 w-3 rounded-full"
                  style={{ backgroundColor: segment.color }}
                />
                <span className="text-muted-foreground">{segment.name}</span>
              </div>
              <span className="font-medium">{segment.value}%</span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

