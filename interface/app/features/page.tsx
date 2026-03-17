'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/lib/auth-provider'
import { Layers } from 'lucide-react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface FeatureGroup {
  id: string
  name: string
  entity?: string
  entity_type?: string
  feature_count?: number
  features?: any[]
  description?: string
  created_at: string
  updated_at?: string
}

export default function FeaturesPage() {
  const { authFetch } = useAuth()
  const [items, setItems] = useState<FeatureGroup[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadItems()
  }, [])

  const loadItems = async () => {
    try {
      const res = await authFetch(`${API_URL}/api/v1/features/groups`)
      if (res.ok) {
        const data = await res.json()
        setItems(Array.isArray(data) ? data : [])
      }
    } catch (err) {
      console.error('failed to load feature groups:', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Feature Store</h1>
          <p className="text-muted-foreground">Manage and version feature groups</p>
        </div>
      </div>

      {loading ? (
        <div className="text-center text-muted-foreground py-12">Loading...</div>
      ) : items.length === 0 ? (
        <div className="text-center text-muted-foreground py-12">
          <Layers className="h-12 w-12 mx-auto mb-3 opacity-30" />
          <p>No feature groups yet</p>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {items.map((group) => (
            <div key={group.id} className="rounded-lg border border-white/10 bg-card p-4 space-y-3">
              <div className="font-medium">{group.name}</div>
              {group.description && (
                <p className="text-sm text-muted-foreground line-clamp-2">{group.description}</p>
              )}

              <div className="space-y-1 text-sm text-muted-foreground">
                <div className="flex justify-between">
                  <span>Entity</span>
                  <span className="font-mono text-foreground">
                    {group.entity || group.entity_type || '-'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Features</span>
                  <span className="font-mono text-foreground">
                    {group.feature_count ?? group.features?.length ?? 0}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Created</span>
                  <span>{new Date(group.created_at).toLocaleDateString()}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
