'use client'

import * as React from 'react'
import {
  LineChart, Line, Area, AreaChart, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer
} from 'recharts'

interface TimeseriesChartProps {
  data: Array<Record<string, any>>
  xKey: string
  yKeys: Array<{ key: string; name: string; color: string }>
  height?: number
}

export function TimeseriesChart({ data, xKey, yKeys, height = 300 }: TimeseriesChartProps) {
  // create gradient definitions
  const gradients = yKeys.map((yKey, idx) => {
    const gradientId = `gradient-${yKey.key}`
    const colors = [
      { offset: '0%', color: yKey.color, opacity: 0.8 },
      { offset: '100%', color: yKey.color, opacity: 0.1 }
    ]
    return { gradientId, colors }
  })

  return (
    <div style={{ height }} className="w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
          <defs>
            {gradients.map((grad) => (
              <linearGradient key={grad.gradientId} id={grad.gradientId} x1="0" y1="0" x2="0" y2="1">
                {grad.colors.map((c, i) => (
                  <stop key={i} offset={c.offset} stopColor={c.color} stopOpacity={c.opacity} />
                ))}
              </linearGradient>
            ))}
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.2} />
          <XAxis
            dataKey={xKey}
            stroke="hsl(var(--muted-foreground))"
            style={{ fontSize: '12px' }}
          />
          <YAxis
            stroke="hsl(var(--muted-foreground))"
            style={{ fontSize: '12px' }}
          />
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
          <Legend />
          {yKeys.map((yKey, idx) => {
            const gradientId = `gradient-${yKey.key}`
            return (
              <Area
                key={yKey.key}
                type="monotone"
                dataKey={yKey.key}
                name={yKey.name}
                stroke={yKey.color}
                strokeWidth={2}
                fill={`url(#${gradientId})`}
                style={{ filter: 'drop-shadow(0 0 6px ' + yKey.color + '40)' }}
              />
            )
          })}
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}
