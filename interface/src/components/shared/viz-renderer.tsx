'use client'

import { useMemo, useRef, useEffect, useState } from 'react'
import {
  BarChart, Bar, LineChart, Line, AreaChart, Area,
  PieChart, Pie, Cell, ScatterChart, Scatter,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts'

const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff7300', '#0088FE', '#00C49F', '#FFBB28', '#FF8042']

// ─── CDN Script Loader ──────────────────────────────────────────────
function loadCdnScript(src: string, globalName: string): Promise<void> {
  return new Promise((resolve, reject) => {
    if ((window as any)[globalName]) { resolve(); return }
    const script = document.createElement('script')
    script.src = src
    script.async = true
    // hide AMD define so UMD wrapper falls through to global assignment
    const savedDefine = (window as any).define;
    (window as any).define = undefined
    script.onload = () => {
      if (savedDefine) (window as any).define = savedDefine
      let attempts = 0
      const check = () => {
        if ((window as any)[globalName]) { resolve() }
        else if (attempts++ < 60) { setTimeout(check, 50) }
        else { reject(new Error(`${globalName} not found after loading ${src}`)) }
      }
      check()
    }
    script.onerror = () => {
      if (savedDefine) (window as any).define = savedDefine
      reject(new Error(`failed to load ${src}`))
    }
    document.head.appendChild(script)
  })
}

let _plotlyPromise: Promise<void> | null = null
function loadPlotly(): Promise<void> {
  if ((window as any).Plotly) return Promise.resolve()
  if (_plotlyPromise) return _plotlyPromise
  _plotlyPromise = loadCdnScript('https://cdn.plot.ly/plotly-2.35.2.min.js', 'Plotly')
  _plotlyPromise.catch(() => { _plotlyPromise = null })
  return _plotlyPromise
}

// ─── Plotly Renderer ─────────────────────────────────────────────────
function PlotlyRenderer({ spec, className }: { spec: string; className?: string }) {
  const divRef = useRef<HTMLDivElement>(null)
  const [ready, setReady] = useState(false)
  const [loadError, setLoadError] = useState<string | null>(null)

  useEffect(() => {
    loadPlotly()
      .then(() => setReady(true))
      .catch((err) => setLoadError(err.message))
  }, [])

  useEffect(() => {
    if (!ready || !divRef.current) return
    const Plotly = (window as any).Plotly
    if (!Plotly) return
    try {
      const parsed = typeof spec === 'string' ? JSON.parse(spec) : spec
      const userLayout = parsed.layout || {}
      const layout = {
        ...userLayout,
        paper_bgcolor: userLayout.paper_bgcolor || 'rgba(0,0,0,0)',
        plot_bgcolor: userLayout.plot_bgcolor || 'rgba(0,0,0,0)',
        font: { color: 'rgba(255,255,255,0.7)', ...(userLayout.font || {}) },
        margin: {
          l: 50, r: userLayout.yaxis2 ? 60 : 20, t: 40, b: 40,
          ...(userLayout.margin || {}),
        },
        autosize: true,
      }
      const data = parsed.data || []
      const config = { responsive: true, displayModeBar: false }
      Plotly.newPlot(divRef.current, data, layout, config)
    } catch (err) {
      console.error('Plotly render error:', err)
    }

    return () => {
      if (divRef.current && (window as any).Plotly) {
        try { (window as any).Plotly.purge(divRef.current) } catch {}
      }
    }
  }, [ready, spec])

  if (loadError) {
    return <div className="text-sm text-red-400 p-4">Failed to load Plotly: {loadError}</div>
  }
  if (!ready) {
    return <div className="text-sm text-muted-foreground p-4 animate-pulse">Loading Plotly...</div>
  }

  return (
    <div
      ref={divRef}
      className={`viz-renderer viz-plotly ${className || ''}`}
      style={{ width: '100%', height: '100%', minHeight: 300 }}
    />
  )
}

// ─── Download Utility ────────────────────────────────────────────────
export async function downloadVisualization(
  filename: string,
  outputType: string,
  renderedOutput: string | undefined,
  containerEl: HTMLElement | null,
) {
  if (!renderedOutput) return

  const triggerDownload = (blob: Blob, name: string) => {
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url; a.download = name; a.click()
    URL.revokeObjectURL(url)
  }

  if (outputType === 'svg') {
    const blob = new Blob([renderedOutput], { type: 'image/svg+xml' })
    triggerDownload(blob, `${filename}.svg`)
  } else if (outputType === 'png') {
    const binary = atob(renderedOutput)
    const bytes = new Uint8Array(binary.length)
    for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i)
    triggerDownload(new Blob([bytes], { type: 'image/png' }), `${filename}.png`)
  } else if (outputType === 'plotly' && containerEl) {
    const plotlyDiv = containerEl.querySelector('.viz-plotly')
    const Plotly = (window as any).Plotly
    if (plotlyDiv && Plotly) {
      const url = await Plotly.toImage(plotlyDiv, { format: 'png', width: 1200, height: 800 })
      const res = await fetch(url)
      const blob = await res.blob()
      triggerDownload(blob, `${filename}.png`)
    }
  } else {
    const blob = new Blob([renderedOutput], { type: 'application/json' })
    triggerDownload(blob, `${filename}.json`)
  }
}

// ─── Main VizRenderer ────────────────────────────────────────────────
interface VizRendererProps {
  backend: string
  outputType: string
  config?: Record<string, any>
  data?: any
  renderedOutput?: string
  code?: string
  width?: number | `${number}%`
  height?: number
  autoResize?: boolean
  containerRef?: React.RefObject<HTMLDivElement>
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
  autoResize = false,
  containerRef,
}: VizRendererProps) {
  const safeConfig = config || {}
  const chartType = safeConfig.chart_type || 'bar'
  const xKey = safeConfig.x_key || 'name'
  const yKey = safeConfig.y_key || 'value'
  const color = safeConfig.color || COLORS[0]

  const chartData = useMemo(() => {
    if (data?.values) return data.values
    if (data?.datasets) return data.datasets
    if (safeConfig.sample_data) return safeConfig.sample_data
    if (Array.isArray(data)) return data
    return [
      { name: 'A', value: 400 },
      { name: 'B', value: 300 },
      { name: 'C', value: 600 },
      { name: 'D', value: 500 },
    ]
  }, [data, safeConfig.sample_data])

  // server-rendered SVG/PNG (matplotlib, seaborn, plotnine, datashader, geopandas, networkx)
  if (renderedOutput && ['svg', 'png'].includes(outputType)) {
    if (outputType === 'svg') {
      return (
        <div
          ref={containerRef as any}
          className="viz-rendered-svg"
          dangerouslySetInnerHTML={{ __html: renderedOutput }}
          style={{ width: '100%', overflow: 'auto' }}
        />
      )
    }
    return (
      <div ref={containerRef as any}>
        <img
          src={`data:image/png;base64,${renderedOutput}`}
          alt="Visualization"
          style={{ maxWidth: '100%' }}
        />
      </div>
    )
  }

  // plotly backend — interactive rendering via CDN
  if (backend === 'plotly' && renderedOutput) {
    return (
      <div ref={containerRef as any} style={{ width: '100%', height: '100%', minHeight: 300 }}>
        <PlotlyRenderer spec={renderedOutput} />
      </div>
    )
  }

  // vega-lite (altair) backend
  if (backend === 'altair' && (renderedOutput || safeConfig.vega_spec)) {
    const spec = renderedOutput || JSON.stringify(safeConfig.vega_spec)
    return (
      <div ref={containerRef as any} className="text-sm text-muted-foreground">
        <pre className="bg-muted/30 p-4 rounded-md overflow-auto max-h-64 text-xs">
          {spec}
        </pre>
        <p className="mt-2 text-xs">Vega-Lite spec ready for rendering.</p>
      </div>
    )
  }

  // bokeh backend
  if (backend === 'bokeh' && renderedOutput) {
    return (
      <div ref={containerRef as any} className="text-sm text-muted-foreground">
        <pre className="bg-muted/30 p-4 rounded-md overflow-auto max-h-64 text-xs">
          {renderedOutput}
        </pre>
        <p className="mt-2 text-xs">Bokeh spec ready for rendering.</p>
      </div>
    )
  }

  // recharts fallback for config-driven viz
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
          <div className="text-4xl font-bold text-primary">{safeConfig.stat_value ?? chartData[0]?.value ?? '—'}</div>
          <div className="text-sm text-muted-foreground mt-1">{safeConfig.stat_label || yKey}</div>
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
