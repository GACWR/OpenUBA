'use client'

import { useState } from 'react'
import { useQuery } from '@apollo/client'
import { GET_MODELS } from '@/lib/graphql/queries'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { DataTable, ColumnDef } from '@/components/tables/data-table'
import { Skeleton } from '@/components/ui/skeleton'
import { Code, Settings, Play, X, Briefcase } from 'lucide-react'
import { ConfigureModelDialog } from './dialogs/configure-model-dialog'
import { ViewCodeDialog } from './dialogs/view-code-dialog'
import { useToast } from '@/components/global/toast-provider'
import { useAuth } from '@/lib/auth-provider'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface Model {
  id: string
  name: string
  version: string
  status: string
  sourceType: string
  enabled: boolean
  description?: string
  author?: string
  createdAt?: string
}

export function ModelInstalledTab() {
  const { addToast } = useToast()
  const { authFetch } = useAuth()
  const { loading, error, data, refetch } = useQuery(GET_MODELS)
  const models = data?.allModels?.nodes || []

  const [executing, setExecuting] = useState<string | null>(null)
  const [training, setTraining] = useState<string | null>(null)

  // Dialog State: { model, tab }
  const [configureDialogState, setConfigureDialogState] = useState<{ model: Model, tab: string } | null>(null)
  const [viewCodeModel, setViewCodeModel] = useState<Model | null>(null)

  // Detail panel state
  const [selectedModel, setSelectedModel] = useState<Model | null>(null)
  const [panelClosing, setPanelClosing] = useState(false)
  const closePanel = () => setPanelClosing(true)
  const onPanelAnimationEnd = () => {
    if (panelClosing) { setSelectedModel(null); setPanelClosing(false) }
  }

  const handleExecute = async (config: any, artifactId?: string) => {
    if (!configureDialogState) return
    const modelId = configureDialogState.model.id
    setExecuting(modelId)
    try {
      const params = new URLSearchParams()
      params.append('data_source', config.dataSource)
      if (config.dataSource === 'spark' && config.tableName) {
        params.append('table_name', config.tableName)
      } else if (config.dataSource === 'elasticsearch' && config.indexName) {
        params.append('index_name', config.indexName)
      } else if (config.dataSource === 'local_csv' && config.filePath) {
        params.append('file_path', config.filePath)
        params.append('file_name', config.filePath.split('/').pop() || '')
      } else if (config.dataSource === 'source_group' && config.sourceGroupSlug) {
        params.append('source_group_slug', config.sourceGroupSlug)
      }

      if (artifactId) {
        params.append('artifact_id', artifactId)
      }

      const response = await authFetch(`${API_URL}/api/v1/models/${modelId}/execute?${params.toString()}`, {
        method: 'POST'
      })
      if (response.ok) {
        const result = await response.json()
        addToast('Inference Started', {
          type: 'success',
          description: `Run ${result.run_id.slice(0, 8)} dispatched for ${configureDialogState.model.name}`,
        })
        setConfigureDialogState(null)
      } else {
        const error = await response.json()
        addToast('Inference Failed', {
          type: 'error',
          description: error.detail || 'unknown error',
          duration: 15000,
        })
      }
    } catch (err) {
      addToast('Inference Error', { type: 'error', description: 'An unexpected error occurred' })
    } finally {
      setExecuting(null)
    }
  }

  const handleTrain = async (config: any) => {
    if (!configureDialogState) return
    const modelId = configureDialogState.model.id
    setTraining(modelId)
    try {
      const params = new URLSearchParams()
      params.append('data_source', config.dataSource)
      if (config.dataSource === 'spark' && config.tableName) {
        params.append('table_name', config.tableName)
      } else if (config.dataSource === 'elasticsearch' && config.indexName) {
        params.append('index_name', config.indexName)
      } else if (config.dataSource === 'local_csv' && config.filePath) {
        params.append('file_path', config.filePath)
        params.append('file_name', config.filePath.split('/').pop() || '')
      } else if (config.dataSource === 'source_group' && config.sourceGroupSlug) {
        params.append('source_group_slug', config.sourceGroupSlug)
      }

      const response = await authFetch(`${API_URL}/api/v1/models/${modelId}/train?${params.toString()}`, {
        method: 'POST'
      })
      if (response.ok) {
        const result = await response.json()
        addToast('Training Started', {
          type: 'success',
          description: `Run ${result.run_id.slice(0, 8)} dispatched for ${configureDialogState.model.name}`,
        })
        setConfigureDialogState(null)
      } else {
        const error = await response.json()
        addToast('Training Failed', {
          type: 'error',
          description: error.detail || 'unknown error',
          duration: 15000,
        })
      }
    } catch (err) {
      addToast('Training Error', { type: 'error', description: 'An unexpected error occurred' })
    } finally {
      setTraining(null)
    }
  }

  const columns: ColumnDef<Model>[] = [
    {
      accessorKey: 'name',
      header: 'name',
      cell: ({ row }) => (
        <button
          className="font-medium hover:text-blue-400 transition-colors text-left"
          onClick={(e) => { e.stopPropagation(); setSelectedModel(row.original) }}
        >
          {row.original.name}
        </button>
      )
    },
    {
      accessorKey: 'version',
      header: 'version',
      cell: ({ row }) => <Badge variant="info" size="sm">{row.original.version}</Badge>
    },
    {
      accessorKey: 'status',
      header: 'status',
      cell: ({ row }) => {
        const status = row.original.status
        const variant = status === 'active' ? 'success' : status === 'installed' ? 'info' : 'warning'
        return <Badge variant={variant} size="sm">{status}</Badge>
      }
    },
    {
      header: 'actions',
      cell: ({ row }) => {
        const model = row.original
        return (
          <div className="flex items-center gap-1.5 justify-end">
            <Button size="sm" variant="ghost" className="h-7 px-2 text-xs" onClick={() => setViewCodeModel(model)}>
              <Code className="h-3.5 w-3.5 mr-1" /> code
            </Button>

            {(model.status === 'installed' || model.status === 'active') && (
              <>
                <Button
                  size="sm"
                  variant="ghost"
                  className="h-7 w-7 px-0"
                  onClick={() => setConfigureDialogState({ model, tab: 'train' })}
                >
                  <Settings className="h-3.5 w-3.5" />
                </Button>

                <Button
                  size="sm"
                  className="h-7 px-2.5 text-xs"
                  onClick={() => setConfigureDialogState({ model, tab: 'infer' })}
                >
                  <Play className="h-3.5 w-3.5 mr-1" /> run
                </Button>
              </>
            )}

            {model.status === 'pending' && (
              <Button size="sm" className="h-7 px-2.5 text-xs" onClick={() => {
                authFetch(`${API_URL}/api/v1/models/${model.id}/install`, { method: 'POST' })
                  .then(() => refetch())
              }}>
                install
              </Button>
            )}
          </div>
        )
      }
    }
  ]

  return (
    <div className="space-y-4">
      {loading && (
        <div className="space-y-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="flex items-center gap-4">
              <Skeleton className="h-4 w-32" />
              <Skeleton className="h-5 w-14 rounded-full" />
              <Skeleton className="h-5 w-16 rounded-full" />
              <Skeleton className="h-4 flex-1" />
            </div>
          ))}
        </div>
      )}
      {!loading && (
        <>
          <DataTable columns={columns} data={models} />

          {configureDialogState && (
            <ConfigureModelDialog
              model={configureDialogState.model}
              initialTab={configureDialogState.tab}
              open={!!configureDialogState}
              onOpenChange={(open) => !open && setConfigureDialogState(null)}
              onExecute={handleExecute}
              onTrain={handleTrain}
              executing={executing === configureDialogState.model.id}
              training={training === configureDialogState.model.id}
            />
          )}

          {viewCodeModel && (
            <ViewCodeDialog
              model={viewCodeModel}
              open={!!viewCodeModel}
              onOpenChange={(open) => !open && setViewCodeModel(null)}
            />
          )}
        </>
      )}

      {/* ── model detail slide-out panel ─────────────── */}
      {selectedModel && (
        <>
          <div
            className="fixed inset-0 bg-black/30 z-40"
            style={{ animation: panelClosing ? 'fadeOut 150ms ease-in forwards' : 'fadeIn 150ms ease-out' }}
            onClick={closePanel}
          />
          <div
            className="fixed top-0 right-0 h-full w-[420px] z-50 border-l bg-background shadow-2xl flex flex-col"
            style={{ animation: panelClosing ? 'slideOutRight 200ms ease-in forwards' : 'slideInRight 200ms ease-out' }}
            onAnimationEnd={onPanelAnimationEnd}
          >
            <div className="flex items-center justify-between px-5 py-4 border-b shrink-0">
              <div className="flex items-center gap-2">
                <Briefcase className="h-4 w-4 text-muted-foreground" />
                <h2 className="text-sm font-semibold">model details</h2>
              </div>
              <Button variant="ghost" size="icon" className="h-7 w-7" onClick={closePanel}>
                <X className="h-4 w-4" />
              </Button>
            </div>
            <div className="flex-1 overflow-y-auto px-5 py-4 space-y-4">
              <div>
                <h3 className="text-lg font-bold">{selectedModel.name}</h3>
                {selectedModel.description && (
                  <p className="text-sm text-muted-foreground mt-1">{selectedModel.description}</p>
                )}
              </div>
              <div className="grid grid-cols-2 gap-3">
                <DetailField label="version" value={selectedModel.version} />
                <DetailField label="status">
                  <Badge
                    variant={selectedModel.status === 'active' ? 'success' : selectedModel.status === 'installed' ? 'info' : 'warning'}
                    size="sm"
                  >
                    {selectedModel.status}
                  </Badge>
                </DetailField>
                <DetailField label="source" value={selectedModel.sourceType || '-'} />
                <DetailField label="author" value={selectedModel.author || '-'} />
                <DetailField label="enabled" value={selectedModel.enabled ? 'yes' : 'no'} />
                <DetailField label="created" value={selectedModel.createdAt ? new Date(selectedModel.createdAt).toLocaleDateString() : '-'} />
              </div>
              <div className="flex gap-2 pt-2">
                <Button
                  size="sm"
                  variant="outline"
                  className="text-xs"
                  onClick={() => { closePanel(); setTimeout(() => setViewCodeModel(selectedModel), 250) }}
                >
                  <Code className="h-3.5 w-3.5 mr-1" /> view code
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  className="text-xs"
                  onClick={() => { closePanel(); setTimeout(() => setConfigureDialogState({ model: selectedModel, tab: 'train' }), 250) }}
                >
                  <Settings className="h-3.5 w-3.5 mr-1" /> configure
                </Button>
                <Button
                  size="sm"
                  className="text-xs"
                  onClick={() => { closePanel(); setTimeout(() => setConfigureDialogState({ model: selectedModel, tab: 'infer' }), 250) }}
                >
                  <Play className="h-3.5 w-3.5 mr-1" /> run
                </Button>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  )
}

/* ── detail field helper ──────────────────────────── */

function DetailField({ label, value, children }: {
  label: string
  value?: string
  children?: React.ReactNode
}) {
  return (
    <div>
      <span className="text-[10px] font-medium uppercase tracking-wide text-muted-foreground">{label}</span>
      <div className="text-sm mt-0.5">{children || value}</div>
    </div>
  )
}

/* ── inline keyframes ─────────────────────────────── */
const modelPanelStyles = `
@keyframes slideInRight {
    from { transform: translateX(100%); }
    to { transform: translateX(0); }
}
@keyframes slideOutRight {
    from { transform: translateX(0); }
    to { transform: translateX(100%); }
}
@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}
@keyframes fadeOut {
    from { opacity: 1; }
    to { opacity: 0; }
}
`
if (typeof document !== 'undefined' && !document.getElementById('model-panel-keyframes')) {
  const style = document.createElement('style')
  style.id = 'model-panel-keyframes'
  style.textContent = modelPanelStyles
  document.head.appendChild(style)
}
