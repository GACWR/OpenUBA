'use client'

import { useState, useEffect, useMemo } from 'react'
import { useToast } from '@/components/global/toast-provider'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { DataTable, ColumnDef } from '@/components/tables/data-table'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useAuth } from '@/lib/auth-provider'
import { Search, Download, CheckCircle, Loader2, Eye } from 'lucide-react'
import { ModelDetailDialog } from './dialogs/model-detail-dialog'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface Model {
  id?: string
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

export function ModelLibraryTab() {
  const { addToast } = useToast()
  const { authFetch } = useAuth()
  const [allModels, setAllModels] = useState<Model[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [loading, setLoading] = useState(true)
  const [installing, setInstalling] = useState<string | null>(null)
  const [selectedModel, setSelectedModel] = useState<Model | null>(null)

  const fetchModels = async () => {
    setLoading(true)
    try {
      const response = await authFetch(
        `${API_URL}/api/v1/models/search?registry_type=code`
      )
      if (response.ok) {
        const data = await response.json()
        setAllModels(data.models || [])
      } else {
        console.error('search failed')
      }
    } catch (err) {
      console.error('search error:', err)
    } finally {
      setLoading(false)
    }
  }

  // load all models on mount
  useEffect(() => {
    fetchModels()
  }, [])

  // client-side filtering for instant UX
  const filtered = useMemo(() => {
    if (!searchQuery.trim()) return allModels
    const q = searchQuery.toLowerCase()
    return allModels.filter(
      (m) =>
        m.name?.toLowerCase().includes(q) ||
        m.description?.toLowerCase().includes(q) ||
        m.framework?.toLowerCase().includes(q) ||
        m.tags?.some((t) => t.toLowerCase().includes(q))
    )
  }, [allModels, searchQuery])

  const handleInstall = async (model: Model) => {
    setInstalling(model.name)
    try {
      // 1. register model in DB
      const createResponse = await authFetch(`${API_URL}/api/v1/models`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: model.name,
          version: model.version || '1.0.0',
          source_type: model.source_type || 'openuba_hub',
          source_url: model.source_url,
          description: model.description,
          author: model.author,
          runtime: model.runtime || 'python-base',
          enabled: true
        })
      })

      if (!createResponse.ok) {
        const error = await createResponse.json()
        throw new Error(error.detail || 'registration failed')
      }

      const newModel = await createResponse.json()

      // 2. trigger installation (download files)
      const installResponse = await authFetch(`${API_URL}/api/v1/models/${newModel.id}/install`, {
        method: 'POST'
      })

      if (!installResponse.ok) {
        const error = await installResponse.json()
        throw new Error(error.detail || 'installation failed')
      }

      addToast('Model Installed', {
        type: 'success',
        description: `successfully installed model: ${model.name}`,
      })

      // update selected model if open
      if (selectedModel?.name === model.name) {
        setSelectedModel({ ...model, installed: true, installed_model_id: newModel.id })
      }

      // refresh to update installed status
      fetchModels()
    } catch (err: any) {
      addToast('Installation Failed', {
        type: 'error',
        description: err.message,
        duration: 15000,
      })
    } finally {
      setInstalling(null)
    }
  }

  const columns: ColumnDef<Model>[] = [
    {
      accessorKey: 'name',
      header: 'name',
      cell: ({ row }) => (
        <div>
          <button
            className="font-medium hover:text-blue-400 transition-colors text-left"
            onClick={() => setSelectedModel(row.original)}
          >
            {row.original.name}
          </button>
          {row.original.author && (
            <span className="text-xs text-muted-foreground ml-2">by {row.original.author}</span>
          )}
        </div>
      )
    },
    {
      accessorKey: 'description',
      header: 'description',
      cell: ({ row }) => (
        <span className="text-sm text-muted-foreground line-clamp-1">
          {row.original.description}
        </span>
      )
    },
    {
      accessorKey: 'framework',
      header: 'framework',
      cell: ({ row }) => {
        const fw = row.original.framework
        if (!fw) return null
        return <Badge variant="info" size="sm">{fw}</Badge>
      }
    },
    {
      accessorKey: 'version',
      header: 'version',
      cell: ({ row }) => (
        <span className="text-xs text-muted-foreground">{row.original.version}</span>
      )
    },
    {
      header: 'actions',
      cell: ({ row }) => {
        const model = row.original
        return (
          <div className="flex items-center gap-1.5 justify-end">
            <Button
              size="sm"
              variant="ghost"
              className="h-7 px-2 text-xs"
              onClick={() => setSelectedModel(model)}
            >
              <Eye className="h-3.5 w-3.5 mr-1" /> details
            </Button>
            {model.installed ? (
              <Badge variant="success" size="sm" className="gap-1">
                <CheckCircle className="h-3 w-3" /> installed
              </Badge>
            ) : (
              <Button
                size="sm"
                onClick={(e) => { e.stopPropagation(); handleInstall(model) }}
                disabled={installing === model.name}
                className="gap-1"
              >
                {installing === model.name ? (
                  <><Loader2 className="h-3.5 w-3.5 animate-spin" /> installing...</>
                ) : (
                  <><Download className="h-3.5 w-3.5" /> install</>
                )}
              </Button>
            )}
          </div>
        )
      }
    }
  ]

  return (
    <Card>
      <CardHeader>
        <CardTitle>model library</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="search models..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9"
            />
          </div>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-12 text-muted-foreground">
            <Loader2 className="h-5 w-5 animate-spin mr-2" />
            loading models from hub...
          </div>
        ) : filtered.length > 0 ? (
          <>
            <p className="text-xs text-muted-foreground">
              {filtered.length === allModels.length
                ? `${allModels.length} models available`
                : `${filtered.length} of ${allModels.length} models`}
            </p>
            <DataTable columns={columns} data={filtered} />
          </>
        ) : allModels.length > 0 ? (
          <p className="text-sm text-muted-foreground text-center py-8">
            no models matching &quot;{searchQuery}&quot;
          </p>
        ) : (
          <p className="text-sm text-muted-foreground text-center py-8">
            no models found — check hub connectivity
          </p>
        )}
      </CardContent>

      {selectedModel && (
        <ModelDetailDialog
          model={selectedModel}
          open={!!selectedModel}
          onOpenChange={(open) => !open && setSelectedModel(null)}
          onInstall={() => handleInstall(selectedModel)}
          installing={installing === selectedModel.name}
        />
      )}
    </Card>
  )
}
