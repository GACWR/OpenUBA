'use client'

import { useEffect, useRef, useState, useMemo } from 'react'
import { BarChart3, Loader2 } from 'lucide-react'

/**
 * Universal visualization renderer.
 *
 * Renders visualization output based on its type:
 *   - "svg"       → inline SVG (matplotlib, seaborn, plotnine, networkx, geopandas)
 *   - "png"       → <img> tag (datashader, base64-encoded)
 *   - "plotly"    → Plotly.js (loaded from CDN on demand)
 *   - "vega-lite" → vega-embed (loaded from CDN on demand)
 *   - "bokeh"     → BokehJS (loaded from CDN on demand)
 */

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
}

export default function VizRenderer({
  backend,
  outputType,
  config,
  data,
  renderedOutput,
  code,
  width = '100%',
  height = 400,
  autoResize = true,
}: VizRendererProps) {
  // SVG — strip fixed dimensions so it scales to 100% container width
  const scaledSvg = useMemo(() => {
    if (outputType !== 'svg' || !renderedOutput) return ''
    const sanitized = renderedOutput.replace(/<script[\s\S]*?<\/script>/gi, '')
    return sanitized.replace(
      /<svg([^>]*)>/,
      (_match: string, attrs: string) => {
        const cleaned = attrs
          .replace(/\s+width="[^"]*"/g, '')
          .replace(/\s+height="[^"]*"/g, '')
        return `<svg${cleaned} style="width:100%;height:auto;display:block">`
      }
    )
  }, [renderedOutput, outputType])

  // ── SVG ──
  if (outputType === 'svg' && renderedOutput) {
    return (
      <div
        className="viz-renderer viz-svg"
        dangerouslySetInnerHTML={{ __html: scaledSvg }}
        style={{ width: '100%' }}
      />
    )
  }

  // ── PNG ──
  if (outputType === 'png' && renderedOutput) {
    const src = renderedOutput.startsWith('data:')
      ? renderedOutput
      : `data:image/png;base64,${renderedOutput}`
    return (
      <div
        className="viz-renderer viz-png flex items-center justify-center"
        style={{ width: '100%', height: '100%' }}
      >
        <img
          src={src}
          alt="Visualization"
          style={{ maxWidth: '100%', maxHeight: '100%', objectFit: 'contain' }}
        />
      </div>
    )
  }

  // ── Plotly ──
  if (outputType === 'plotly' && renderedOutput) {
    return <PlotlyRenderer spec={renderedOutput} className="" autoResize={autoResize} />
  }

  // ── Vega-Lite (Altair) ──
  if (outputType === 'vega-lite' && renderedOutput) {
    return <VegaLiteRenderer spec={renderedOutput} className="" />
  }

  // ── Bokeh ──
  if (outputType === 'bokeh' && renderedOutput) {
    return <BokehRenderer spec={renderedOutput} className="" />
  }

  // ── Empty state ──
  return (
    <div
      className="flex flex-col items-center justify-center text-center p-6"
      style={{ width: '100%', height: '100%', minHeight: 120 }}
    >
      <BarChart3 className="h-8 w-8 text-muted-foreground/20 mb-2" />
      <p className="text-[11px] text-muted-foreground/40">
        {renderedOutput
          ? `Unsupported output type: ${outputType}`
          : 'Not rendered yet — run from a notebook to generate output.'}
      </p>
    </div>
  )
}

// ── Plotly Renderer ────────────────────────────────────────────────

function PlotlyRenderer({
  spec,
  className,
  autoResize,
}: {
  spec: string
  className: string
  autoResize: boolean
}) {
  const divRef = useRef<HTMLDivElement>(null)
  const [ready, setReady] = useState(false)
  const [loadError, setLoadError] = useState<string | null>(null)

  useEffect(() => {
    loadPlotly()
      .then(() => setReady(true))
      .catch((err) => setLoadError(err.message))
  }, [])

  // Parse spec once
  const parsed = useMemo(() => {
    try {
      return typeof spec === 'string' ? JSON.parse(spec) : spec
    } catch { return null }
  }, [spec])

  useEffect(() => {
    if (!ready || !divRef.current || !parsed) return
    const Plotly = (window as any).Plotly
    if (!Plotly) return
    const el = divRef.current

    const doPlot = () => {
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
      Plotly.newPlot(el, data, layout, config)
    }

    let plotted = false
    const raf = requestAnimationFrame(() => {
      doPlot()
      plotted = true
    })

    // Watch parent for size changes (grid column toggle)
    // Plotly.Plots.resize is the only reliable way to update Plotly's internal SVG
    const parent = el.parentElement
    const observer = parent ? new ResizeObserver(() => {
      if (!plotted) return
      if ((window as any).Plotly) {
        try { (window as any).Plotly.Plots.resize(el) } catch {}
      }
    }) : null
    if (observer && parent) observer.observe(parent)

    return () => {
      cancelAnimationFrame(raf)
      if (observer) observer.disconnect()
      if (el && (window as any).Plotly) {
        try { (window as any).Plotly.purge(el) } catch {}
      }
    }
  }, [ready, parsed, autoResize])

  if (loadError) {
    return (
      <div className="flex items-center justify-center w-full h-full min-h-[120px] text-xs text-red-400">
        Failed to load Plotly: {loadError}
      </div>
    )
  }
  if (!ready) return <LoadingSpinner />

  return (
    <div
      ref={divRef}
      className={`viz-renderer viz-plotly ${className}`}
      style={{ width: '100%', height: '100%' }}
    />
  )
}

// ── Vega-Lite Renderer ─────────────────────────────────────────────

function VegaLiteRenderer({
  spec,
  className,
}: {
  spec: string
  className: string
}) {
  const divRef = useRef<HTMLDivElement>(null)
  const [ready, setReady] = useState(false)
  const [loadError, setLoadError] = useState<string | null>(null)

  useEffect(() => {
    loadVegaEmbed()
      .then(() => setReady(true))
      .catch((err) => setLoadError(err.message))
  }, [])

  useEffect(() => {
    if (!ready || !divRef.current) return
    const el = divRef.current
    let observer: ResizeObserver | null = null
    let viewRef: any = null

    const doEmbed = () => {
      try {
        const parsed = typeof spec === 'string' ? JSON.parse(spec) : spec
        const vegaSpec = {
          ...parsed,
          width: 'container',
          height: 'container',
          background: 'transparent',
          config: {
            ...(parsed.config || {}),
            axis: { labelColor: 'rgba(255,255,255,0.6)', titleColor: 'rgba(255,255,255,0.7)' },
            legend: { labelColor: 'rgba(255,255,255,0.6)', titleColor: 'rgba(255,255,255,0.7)' },
            title: { color: 'rgba(255,255,255,0.8)' },
            view: { stroke: 'transparent' },
          },
        }
        ;(window as any).vegaEmbed(el, vegaSpec, {
          actions: false,
          theme: 'dark',
        }).then((result: any) => {
          viewRef = result.view
          // Force vega-embed wrapper to fill width
          const embedEl = el.querySelector('.vega-embed') as HTMLElement
          if (embedEl) {
            embedEl.style.width = '100%'
            embedEl.style.display = 'block'
          }
          // Watch parent for container resize (e.g. toggle code panel)
          const parent = el.parentElement
          if (parent) {
            observer = new ResizeObserver(() => {
              if (viewRef) {
                try { viewRef.resize().runAsync() } catch {}
              }
            })
            observer.observe(parent)
          }
        })
      } catch (err) {
        console.error('Vega-Lite render error:', err)
      }
    }
    const raf = requestAnimationFrame(doEmbed)
    return () => {
      cancelAnimationFrame(raf)
      if (observer) observer.disconnect()
    }
  }, [ready, spec])

  if (loadError) {
    return (
      <div className="flex items-center justify-center w-full h-full min-h-[120px] text-xs text-red-400">
        Failed to load Vega: {loadError}
      </div>
    )
  }
  if (!ready) return <LoadingSpinner />

  return (
    <div
      ref={divRef}
      className={`viz-renderer viz-vega ${className}`}
      style={{ width: '100%', height: '100%' }}
    />
  )
}

// ── Bokeh Renderer ─────────────────────────────────────────────────

function BokehRenderer({
  spec,
  className,
}: {
  spec: string
  className: string
}) {
  const divRef = useRef<HTMLDivElement>(null)
  const [bokehId] = useState(() => `bokeh-${Math.random().toString(36).slice(2)}`)
  const [ready, setReady] = useState(false)
  const [loadError, setLoadError] = useState<string | null>(null)

  useEffect(() => {
    loadBokeh()
      .then(() => setReady(true))
      .catch((err) => setLoadError(err.message))
  }, [])

  useEffect(() => {
    if (!ready || !divRef.current) return
    const el = divRef.current
    let observer: ResizeObserver | null = null

    const doEmbed = () => {
      try {
        const parsed = typeof spec === 'string' ? JSON.parse(spec) : spec
        // Override sizing_mode on all layout-capable models
        if (parsed.doc?.roots?.references) {
          for (const ref of parsed.doc.roots.references) {
            if (ref.attributes && ('sizing_mode' in ref.attributes || ref.type === 'Figure' || ref.type === 'Plot' || ref.type === 'Column' || ref.type === 'Row')) {
              ref.attributes = { ...ref.attributes, sizing_mode: 'stretch_width' }
            }
          }
        }
        el.innerHTML = ''
        ;(window as any).Bokeh.embed.embed_item(parsed, bokehId)

        // Force Bokeh's generated wrapper elements to fill width
        requestAnimationFrame(() => {
          const bkRoot = el.querySelector('.bk-root, .bk-Column, .bk') as HTMLElement
          if (bkRoot) bkRoot.style.width = '100%'
          // Also resize any canvas elements
          const allBk = el.querySelectorAll('.bk') as NodeListOf<HTMLElement>
          allBk.forEach(bk => { bk.style.width = '100%' })
        })

        // Watch parent for container resize
        const parent = el.parentElement
        if (parent) {
          observer = new ResizeObserver(() => {
            try { window.dispatchEvent(new Event('resize')) } catch {}
          })
          observer.observe(parent)
        }
      } catch (err) {
        console.error('Bokeh render error:', err)
      }
    }
    const raf = requestAnimationFrame(doEmbed)
    return () => {
      cancelAnimationFrame(raf)
      if (observer) observer.disconnect()
    }
  }, [ready, spec, bokehId])

  if (loadError) {
    return (
      <div className="flex items-center justify-center w-full h-full min-h-[120px] text-xs text-red-400">
        Failed to load Bokeh: {loadError}
      </div>
    )
  }
  if (!ready) return <LoadingSpinner />

  return (
    <div
      ref={divRef}
      id={bokehId}
      className={`viz-renderer viz-bokeh ${className}`}
      style={{ width: '100%', height: '100%' }}
    />
  )
}

// ── Shared Helpers ─────────────────────────────────────────────────

function LoadingSpinner() {
  return (
    <div className="flex items-center justify-center w-full h-full min-h-[120px]">
      <Loader2 className="h-5 w-5 animate-spin text-muted-foreground/40" />
    </div>
  )
}

// ── Download Utility ──────────────────────────────────────────────

function triggerDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

export async function downloadVisualization(
  name: string,
  outputType: string,
  renderedOutput: string | undefined,
  containerEl?: HTMLElement | null,
) {
  const filename = name.replace(/[^a-zA-Z0-9_-]/g, '_')

  if (outputType === 'svg' && renderedOutput) {
    const blob = new Blob([renderedOutput], { type: 'image/svg+xml' })
    triggerDownload(blob, `${filename}.svg`)
  } else if (outputType === 'png' && renderedOutput) {
    const src = renderedOutput.startsWith('data:')
      ? renderedOutput
      : `data:image/png;base64,${renderedOutput}`
    const res = await fetch(src)
    const blob = await res.blob()
    triggerDownload(blob, `${filename}.png`)
  } else if (outputType === 'plotly' && containerEl) {
    const plotlyDiv = containerEl.querySelector('.viz-plotly')
    const Plotly = (window as any).Plotly
    if (plotlyDiv && Plotly) {
      const url = await Plotly.toImage(plotlyDiv, { format: 'png', width: 1200, height: 800 })
      const res = await fetch(url)
      const blob = await res.blob()
      triggerDownload(blob, `${filename}.png`)
    }
  } else if ((outputType === 'vega-lite' || outputType === 'bokeh') && containerEl) {
    const canvas = containerEl.querySelector('canvas') as HTMLCanvasElement | null
    if (canvas) {
      canvas.toBlob((blob) => {
        if (blob) triggerDownload(blob, `${filename}.png`)
      })
    }
  }
}

// ── CDN Script Loading ─────────────────────────────────────────────
// UMD libraries set globals but Webpack's `define` intercepts AMD.
// We hide `define` before script injection so UMD falls through to globals.

const _scriptCache = new Map<string, Promise<void>>()

function loadCdnScript(src: string, globalName: string): Promise<void> {
  if ((window as any)[globalName]) return Promise.resolve()
  if (_scriptCache.has(src)) return _scriptCache.get(src)!

  const promise = new Promise<void>((resolve, reject) => {
    const script = document.createElement('script')
    script.src = src
    script.async = true

    const savedDefine = (window as any).define
    ;(window as any).define = undefined

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
      _scriptCache.delete(src)
      reject(new Error(`Failed to load ${src}`))
    }

    document.head.appendChild(script)
  })

  _scriptCache.set(src, promise)
  return promise
}

// ── Plotly Loader ──────────────────────────────────────────────────

let _plotlyPromise: Promise<void> | null = null

function loadPlotly(): Promise<void> {
  if ((window as any).Plotly) return Promise.resolve()
  if (_plotlyPromise) return _plotlyPromise
  _plotlyPromise = loadCdnScript(
    'https://cdn.plot.ly/plotly-2.35.2.min.js',
    'Plotly'
  )
  _plotlyPromise.catch(() => { _plotlyPromise = null })
  return _plotlyPromise
}

// ── Vega-Embed Loader ──────────────────────────────────────────────
// Must load vega -> vega-lite -> vega-embed sequentially (each depends on prior).

let _vegaPromise: Promise<void> | null = null

function loadVegaEmbed(): Promise<void> {
  if ((window as any).vegaEmbed) return Promise.resolve()
  if (_vegaPromise) return _vegaPromise

  _vegaPromise = loadCdnScript('https://cdn.jsdelivr.net/npm/vega@5', 'vega')
    .then(() => loadCdnScript('https://cdn.jsdelivr.net/npm/vega-lite@5', 'vegaLite'))
    .then(() => loadCdnScript('https://cdn.jsdelivr.net/npm/vega-embed@6', 'vegaEmbed'))

  _vegaPromise.catch(() => { _vegaPromise = null })
  return _vegaPromise
}

// ── Bokeh Loader ───────────────────────────────────────────────────
// Load main bokeh first, then API extension (which adds to window.Bokeh).

let _bokehPromise: Promise<void> | null = null

function loadBokeh(): Promise<void> {
  if ((window as any).Bokeh) return Promise.resolve()
  if (_bokehPromise) return _bokehPromise

  _bokehPromise = loadCdnScript(
    'https://cdn.bokeh.org/bokeh/release/bokeh-3.4.3.min.js',
    'Bokeh'
  ).then(() => {
    return new Promise<void>((resolve, reject) => {
      const script = document.createElement('script')
      script.src = 'https://cdn.bokeh.org/bokeh/release/bokeh-api-3.4.3.min.js'
      script.async = true
      script.onload = () => resolve()
      script.onerror = () => reject(new Error('Failed to load bokeh-api'))
      document.head.appendChild(script)
    })
  })

  _bokehPromise.catch(() => { _bokehPromise = null })
  return _bokehPromise
}
