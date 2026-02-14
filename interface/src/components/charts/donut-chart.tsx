'use client'

import * as React from 'react'
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts'

interface DonutChartProps {
  data: Array<{ name: string; value: number }>
  colors?: string[]
  height?: number
  showCenterLabel?: boolean
  centerLabel?: string
}

const DEFAULT_COLORS = ['#9333ea', '#f97316', '#06b6d4', '#6366f1', '#10b981']

export function DonutChart({ data, colors = DEFAULT_COLORS, height = 300, showCenterLabel = true, centerLabel }: DonutChartProps) {
  const total = data.reduce((sum, item) => sum + item.value, 0)
  const percentage = total > 0 ? Math.round((data[0]?.value / total) * 100) : 0
  const displayLabel = centerLabel || `${percentage}%`

  return (
    <div style={{ height }} className="w-full relative">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={height * 0.25}
            outerRadius={height * 0.4}
            paddingAngle={2}
            dataKey="value"
          >
            {data.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={colors[index % colors.length]}
                style={{ filter: 'drop-shadow(0 0 4px ' + colors[index % colors.length] + '60)' }}
              />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              backgroundColor: 'hsl(var(--card))',
              border: '1px solid hsl(var(--border))',
              borderRadius: '8px',
              boxShadow: '0 4px 20px rgba(0, 0, 0, 0.3)',
              color: 'hsl(var(--foreground))',
            }}
            itemStyle={{ color: 'hsl(var(--foreground))' }}
            labelStyle={{ color: 'hsl(var(--muted-foreground))' }}
          />
          <Legend
            wrapperStyle={{ fontSize: '12px' }}
            iconType="circle"
          />
        </PieChart>
      </ResponsiveContainer>
      {showCenterLabel && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <div className="text-center">
            <div className={`font-bold text-foreground ${displayLabel.length > 4 ? 'text-xl' : 'text-3xl'}`}>{displayLabel}</div>
            {data[0] && <div className="text-xs text-muted-foreground mt-1">{data[0].name}</div>}
          </div>
        </div>
      )}
    </div>
  )
}
