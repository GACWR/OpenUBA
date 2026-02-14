'use client'

import { useState, useEffect, useCallback } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { Download, CheckCircle, Loader2, ExternalLink, Tag, Box, User, FileCode, BookOpen } from 'lucide-react'

const RAW_BASE_URL = 'https://raw.githubusercontent.com/GACWR/openuba-model-hub/master'

interface ModelDetailDialogProps {
  model: {
    name: string
    slug?: string
    description?: string
    framework?: string
    runtime?: string
    version?: string
    source_url?: string
    source_type?: string
    tags?: string[]
    author?: string
    path?: string
    parameters?: any[]
    license?: string
    dependencies?: string[]
    components?: string[]
    installed?: boolean
    installed_model_id?: string | null
  }
  open: boolean
  onOpenChange: (open: boolean) => void
  onInstall: () => void
  installing: boolean
}

export function ModelDetailDialog({ model, open, onOpenChange, onInstall, installing }: ModelDetailDialogProps) {
  const [code, setCode] = useState<string>('')
  const [codeLoading, setCodeLoading] = useState(false)
  const [codeError, setCodeError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState('overview')

  const fetchCode = useCallback(async () => {
    if (!model.path) {
      setCodeError('no source path available')
      return
    }
    setCodeLoading(true)
    setCodeError(null)
    try {
      const url = `${RAW_BASE_URL}/${model.path}/MODEL.py`
      const res = await fetch(url)
      if (!res.ok) {
        throw new Error(`failed to fetch (${res.status})`)
      }
      const text = await res.text()
      setCode(text)
    } catch (err: any) {
      console.error('error fetching model code:', err)
      setCodeError('failed to load source code from hub')
    } finally {
      setCodeLoading(false)
    }
  }, [model.path])

  useEffect(() => {
    if (open && activeTab === 'code' && !code && !codeLoading) {
      fetchCode()
    }
  }, [open, activeTab, code, codeLoading, fetchCode])

  useEffect(() => {
    if (!open) {
      setCode('')
      setCodeError(null)
      setActiveTab('overview')
    }
  }, [open])

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[720px] h-[80vh] flex flex-col">
        <DialogHeader>
          <div className="flex items-start justify-between pr-6">
            <div className="space-y-1">
              <DialogTitle className="text-xl">{model.name}</DialogTitle>
              <DialogDescription className="text-sm">
                {model.description || 'no description available'}
              </DialogDescription>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-2 pt-2">
            {model.framework && (
              <Badge variant="info" size="sm" className="gap-1">
                <Box className="h-3 w-3" />
                {model.framework}
              </Badge>
            )}
            {model.version && (
              <Badge variant="default" size="sm">
                v{model.version}
              </Badge>
            )}
            {model.runtime && (
              <Badge variant="default" size="sm" className="gap-1">
                <FileCode className="h-3 w-3" />
                {model.runtime}
              </Badge>
            )}
            {model.installed ? (
              <Badge variant="success" size="sm" className="gap-1">
                <CheckCircle className="h-3 w-3" /> installed
              </Badge>
            ) : null}
          </div>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 min-h-0 flex flex-col">
          <TabsList>
            <TabsTrigger value="overview">
              <BookOpen className="h-3.5 w-3.5 mr-1.5" />
              overview
            </TabsTrigger>
            <TabsTrigger value="code">
              <FileCode className="h-3.5 w-3.5 mr-1.5" />
              source code
            </TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="flex-1 min-h-0 overflow-y-auto space-y-5 pr-1">
            {/* metadata grid */}
            <div className="grid grid-cols-2 gap-4">
              <DetailField label="author" icon={<User className="h-3 w-3" />}>
                {model.author || '-'}
              </DetailField>
              <DetailField label="license">
                {model.license || '-'}
              </DetailField>
              <DetailField label="framework" icon={<Box className="h-3 w-3" />}>
                {model.framework || '-'}
              </DetailField>
              <DetailField label="runtime">
                {model.runtime || '-'}
              </DetailField>
              <DetailField label="version">
                {model.version || '-'}
              </DetailField>
              <DetailField label="source">
                {model.source_type || '-'}
              </DetailField>
            </div>

            {/* tags */}
            {model.tags && model.tags.length > 0 && (
              <div>
                <span className="text-[10px] font-medium uppercase tracking-wide text-muted-foreground flex items-center gap-1 mb-2">
                  <Tag className="h-3 w-3" /> tags
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {model.tags.map((tag) => (
                    <Badge key={tag} variant="default" size="sm">
                      {tag}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {/* parameters */}
            {model.parameters && model.parameters.length > 0 && (
              <div>
                <span className="text-[10px] font-medium uppercase tracking-wide text-muted-foreground mb-2 block">
                  parameters
                </span>
                <div className="border rounded-md overflow-hidden">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b bg-muted/50">
                        <th className="text-left px-3 py-2 text-xs font-medium text-muted-foreground">name</th>
                        <th className="text-left px-3 py-2 text-xs font-medium text-muted-foreground">type</th>
                        <th className="text-left px-3 py-2 text-xs font-medium text-muted-foreground">default</th>
                        <th className="text-left px-3 py-2 text-xs font-medium text-muted-foreground">description</th>
                      </tr>
                    </thead>
                    <tbody>
                      {model.parameters.map((param: any, i: number) => (
                        <tr key={i} className="border-b last:border-0">
                          <td className="px-3 py-2 font-mono text-xs">{param.name || '-'}</td>
                          <td className="px-3 py-2 text-xs text-muted-foreground">{param.type || '-'}</td>
                          <td className="px-3 py-2 text-xs font-mono">{param.default !== undefined ? String(param.default) : '-'}</td>
                          <td className="px-3 py-2 text-xs text-muted-foreground">{param.description || '-'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* dependencies */}
            {model.dependencies && model.dependencies.length > 0 && (
              <div>
                <span className="text-[10px] font-medium uppercase tracking-wide text-muted-foreground mb-2 block">
                  dependencies
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {model.dependencies.map((dep: string) => (
                    <Badge key={dep} variant="default" size="sm" className="font-mono">
                      {dep}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {/* source link */}
            {model.source_url && (
              <div>
                <a
                  href={model.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 text-sm text-blue-400 hover:text-blue-300 transition-colors"
                >
                  <ExternalLink className="h-3.5 w-3.5" />
                  view on github
                </a>
              </div>
            )}
          </TabsContent>

          <TabsContent value="code" className="flex-1 min-h-0 flex flex-col">
            <div className="flex-1 min-h-0 border rounded-md bg-slate-950 overflow-hidden">
              {codeLoading && (
                <div className="flex items-center gap-2 p-4 text-slate-400">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  loading source code...
                </div>
              )}
              {codeError && <div className="p-4 text-red-400">{codeError}</div>}
              {!codeLoading && !codeError && code && (
                <SyntaxHighlighter
                  language="python"
                  style={vscDarkPlus}
                  customStyle={{ margin: 0, height: '100%', fontSize: '13px', paddingTop: '1rem', paddingBottom: '1rem' }}
                  codeTagProps={{ style: { fontFamily: 'var(--font-mono, monospace)' } }}
                  showLineNumbers={true}
                  wrapLines={true}
                >
                  {code}
                </SyntaxHighlighter>
              )}
              {!codeLoading && !codeError && !code && (
                <div className="p-4 text-slate-400">
                  click the &quot;source code&quot; tab to load the model code
                </div>
              )}
            </div>
          </TabsContent>
        </Tabs>

        {/* install footer */}
        <div className="flex items-center justify-between pt-2 border-t">
          <div className="text-xs text-muted-foreground">
            {model.slug || model.name}
          </div>
          {model.installed ? (
            <Button size="sm" variant="outline" disabled className="gap-1.5">
              <CheckCircle className="h-3.5 w-3.5" /> installed
            </Button>
          ) : (
            <Button
              size="sm"
              onClick={onInstall}
              disabled={installing}
              className="gap-1.5"
            >
              {installing ? (
                <>
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  installing...
                </>
              ) : (
                <>
                  <Download className="h-3.5 w-3.5" />
                  install model
                </>
              )}
            </Button>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}

function DetailField({ label, icon, children }: {
  label: string
  icon?: React.ReactNode
  children: React.ReactNode
}) {
  return (
    <div>
      <span className="text-[10px] font-medium uppercase tracking-wide text-muted-foreground flex items-center gap-1">
        {icon}
        {label}
      </span>
      <div className="text-sm mt-0.5">{children}</div>
    </div>
  )
}
