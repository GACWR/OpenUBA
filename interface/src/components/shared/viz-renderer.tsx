'use client'

import { useMemo } from 'react'
import {
  BarChart, Bar, LineChart, Line, AreaChart, Area,
  PieChart, Pie, Cell, ScatterChart, Scatter,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts'

const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff7300', '#0088FE', '#00C49F', '#FFBB28', '#FF8042']

interface VizRendererProps {
  backend: string
  outputType: string
  config?: Record<string, any>
  data?: any
  renderedOutput?: string
  code?: string
  width?: number | `${number}%`
  height?: number
}

export default function VizRenderer({
  backend,
  outputType,
  config = {},
  data,
  renderedOutput,
  code,
  width = '100%',
  height = 400,
}: VizRendererProps) {
  const chartType = config.chart_type || 'bar'
  const xKey = config.x_key || 'name'
  const yKey = config.y_key || 'value'
  const color = config.color || COLORS[0]

  const chartData = useMemo(() => {
    if (data?.values) return data.values
    if (data?.datasets) return data.datasets
    if (config.sample_data) return config.sample_data
    if (Array.isArray(data)) return data
    return [
      { name: 'A', value: 400 },
      { name: 'B', value: 300 },
      { name: 'C', value: 600 },
      { name: 'D', value: 500 },
    ]
  }, [data, config.sample_data])

  // for server-rendered backends (matplotlib, seaborn, plotnine, datashader, geopandas)
  // display the rendered SVG/PNG output directly
  if (renderedOutput && ['svg', 'png'].includes(outputType)) {
    if (outputType === 'svg') {
      return (
        <div
          className="viz-rendered-svg"
          dangerouslySetInnerHTML={{ __html: renderedOutput }}
          style={{ width, maxHeight: height, overflow: 'auto' }}
        />
      )
    }
    return (
      <img
        src={`data:image/png;base64,${renderedOutput}`}
        alt="Visualization"
        style={{ maxWidth: '100%', maxHeight: height }}
      />
    )
  }

  // for plotly backend, render plotly JSON spec
  if (backend === 'plotly' && (renderedOutput || config.plotly_spec)) {
    const spec = renderedOutput || JSON.stringify(config.plotly_spec)
    return (
      <div className="text-sm text-muted-foreground">
        <pre className="bg-muted/30 p-4 rounded-md overflow-auto max-h-64 text-xs">
          {spec}
        </pre>
        <p className="mt-2 text-xs">Plotly spec ready for rendering. Install @plotly/react-plotly.js for interactive charts.</p>
      </div>
    )
  }

  // for vega-lite (altair) backend
  if (backend === 'altair' && (renderedOutput || config.vega_spec)) {
    const spec = renderedOutput || JSON.stringify(config.vega_spec)
    return (
      <div className="text-sm text-muted-foreground">
        <pre className="bg-muted/30 p-4 rounded-md overflow-auto max-h-64 text-xs">
          {spec}
        </pre>
        <p className="mt-2 text-xs">Vega-Lite spec ready for rendering.</p>
      </div>
    )
  }

  // recharts-based rendering for interactive viz
  if (chartType === 'line') {
    return (
      <ResponsiveContainer width={width} height={height}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#333" />
          <XAxis dataKey={xKey} stroke="#888" fontSize={12} />
          <YAxis stroke="#888" fontSize={12} />
          <Tooltip contentStyle={{ backgroundColor: '#1a1a2e', border: '1px solid #333' }} />
          <Legend />
          <Line type="monotone" dataKey={yKey} stroke={color} strokeWidth={2} dot={{ fill: color }} />
        </LineChart>
      </ResponsiveContainer>
    )
  }

  if (chartType === 'area') {
    return (
      <ResponsiveContainer width={width} height={height}>
        <AreaChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#333" />
          <XAxis dataKey={xKey} stroke="#888" fontSize={12} />
          <YAxis stroke="#888" fontSize={12} />
          <Tooltip contentStyle={{ backgroundColor: '#1a1a2e', border: '1px solid #333' }} />
          <Legend />
          <Area type="monotone" dataKey={yKey} stroke={color} fill={color} fillOpacity={0.3} />
        </AreaChart>
      </ResponsiveContainer>
    )
  }

  if (chartType === 'pie') {
    return (
      <ResponsiveContainer width={width} height={height}>
        <PieChart>
          <Pie
            data={chartData}
            cx="50%" cy="50%"
            outerRadius={Math.min(height / 3, 120)}
            fill={color}
            dataKey={yKey}
            nameKey={xKey}
            label={({ name, value }: any) => `${name}: ${value}`}
          >
            {chartData.map((_: any, i: number) => (
              <Cell key={i} fill={COLORS[i % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip contentStyle={{ backgroundColor: '#1a1a2e', border: '1px solid #333' }} />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    )
  }

  if (chartType === 'scatter') {
    return (
      <ResponsiveContainer width={width} height={height}>
        <ScatterChart>
          <CartesianGrid strokeDasharray="3 3" stroke="#333" />
          <XAxis dataKey={xKey} stroke="#888" fontSize={12} />
          <YAxis dataKey={yKey} stroke="#888" fontSize={12} />
          <Tooltip contentStyle={{ backgroundColor: '#1a1a2e', border: '1px solid #333' }} />
          <Scatter data={chartData} fill={color} />
        </ScatterChart>
      </ResponsiveContainer>
    )
  }

  if (chartType === 'stat') {
    return (
      <div className="flex items-center justify-center" style={{ height }}>
        <div className="text-center">
          <div className="text-4xl font-bold text-primary">{config.stat_value ?? chartData[0]?.value ?? '—'}</div>
          <div className="text-sm text-muted-foreground mt-1">{config.stat_label || yKey}</div>
        </div>
      </div>
    )
  }

  // default: bar chart
  return (
    <ResponsiveContainer width={width} height={height}>
      <BarChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" stroke="#333" />
        <XAxis dataKey={xKey} stroke="#888" fontSize={12} />
        <YAxis stroke="#888" fontSize={12} />
        <Tooltip contentStyle={{ backgroundColor: '#1a1a2e', border: '1px solid #333' }} />
        <Legend />
        <Bar dataKey={yKey} fill={color} radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  )
}
