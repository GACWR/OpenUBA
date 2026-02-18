'use client'

import * as React from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

interface BarChartProps {
  data: Array<Record<string, any>>
  xKey: string
  yKeys: Array<{ key: string; name: string; color: string }>
  height?: number
}

export function BarChartComponent({ data, xKey, yKeys, height = 300 }: BarChartProps) {
  return (
    <div style={{ height }} className="w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
          <defs>
            {yKeys.map((yKey) => {
              const gradientId = `gradient-${yKey.key}`
              return (
                <linearGradient key={gradientId} id={gradientId} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={yKey.color} stopOpacity={0.9} />
                  <stop offset="100%" stopColor={yKey.color} stopOpacity={0.5} />
                </linearGradient>
              )
            })}
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
          {yKeys.map((yKey) => {
            const gradientId = `gradient-${yKey.key}`
            return (
              <Bar
                key={yKey.key}
                dataKey={yKey.key}
                name={yKey.name}
                fill={`url(#${gradientId})`}
                radius={[8, 8, 0, 0]}
                style={{ filter: 'drop-shadow(0 2px 4px ' + yKey.color + '40)' }}
              />
            )
          })}
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

export { BarChartComponent as BarChart }
