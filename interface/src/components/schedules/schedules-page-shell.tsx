'use client'

import { useState, useEffect, useCallback } from 'react'
import { useQuery } from '@apollo/client'
import { GET_MODELS } from '@/lib/graphql/queries'
import { DataTable, ColumnDef } from '@/components/tables/data-table'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { RefreshCw, Trash2 } from 'lucide-react'
import { useAuth } from '@/lib/auth-provider'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface Schedule {
    id: string
    model_id: string
    cron_expression: string
    enabled: boolean
    next_run?: string
}

export function SchedulesPageShell() {
    const [schedules, setSchedules] = useState<Schedule[]>([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const { authFetch } = useAuth()

    // Fetch models to map IDs to Names
    const { data: modelsData } = useQuery(GET_MODELS)
    const models = modelsData?.allModels?.nodes || []
    const modelMap = new Map(models.map((m: any) => [m.id, m.name]))

    const fetchSchedules = useCallback(async () => {
        setLoading(true)
        try {
            const res = await authFetch(`${API_URL}/api/v1/schedules`)
            if (!res.ok) throw new Error('Failed to fetch schedules')
            const data = await res.json()
            setSchedules(data)
            setError(null)
        } catch (err: any) {
            setError(err.message)
        } finally {
            setLoading(false)
        }
    }, [authFetch])

    useEffect(() => {
        fetchSchedules()
    }, [fetchSchedules])

    const handleDelete = async (modelId: string) => {
        if (!confirm('Are you sure you want to delete this schedule?')) return
        try {
            const res = await authFetch(`${API_URL}/api/v1/models/${modelId}/schedule`, { method: 'DELETE' })
            if (!res.ok) throw new Error('Failed to delete schedule')
            fetchSchedules()
        } catch (err: any) {
            alert(err.message)
        }
    }

    const columns: ColumnDef<Schedule>[] = [
        {
            accessorKey: 'model_id',
            header: 'Model',
            cell: ({ row }) => (
                <span className="font-medium">
                    {(modelMap.get(row.original.model_id) as string) || row.original.model_id}
                </span>
            )
        },
        {
            accessorKey: 'cron_expression',
            header: 'Schedule (Cron)',
            cell: ({ row }) => <code className="bg-secondary px-2 py-1 rounded">{row.original.cron_expression}</code>
        },
        {
            accessorKey: 'next_run',
            header: 'Next Run',
            cell: ({ row }) => row.original.next_run ? new Date(row.original.next_run).toLocaleString() : 'N/A'
        },
        {
            accessorKey: 'enabled',
            header: 'Status',
            cell: ({ row }) => (
                <Badge variant={row.original.enabled ? 'success' : 'secondary'}>
                    {row.original.enabled ? 'Active' : 'Paused'}
                </Badge>
            )
        },
        {
            header: 'Actions',
            cell: ({ row }) => (
                <Button variant="ghost" size="icon" onClick={() => handleDelete(row.original.model_id)}>
                    <Trash2 className="h-4 w-4 text-red-500" />
                </Button>
            )
        }
    ]

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold">Schedules</h1>
                    <p className="text-muted-foreground">Manage automated model execution jobs</p>
                </div>
                <Button onClick={fetchSchedules} variant="outline" size="icon">
                    <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
                </Button>
            </div>

            <Card>
                <CardHeader>
                    <CardTitle>Scheduled Jobs</CardTitle>
                </CardHeader>
                <CardContent>
                    {error && <p className="text-red-500 mb-4">Error: {error}</p>}
                    <DataTable columns={columns} data={schedules} />
                    {!loading && schedules.length === 0 && (
                        <div className="text-center py-8 text-muted-foreground">
                            No active schedules found. Configure schedules in the Models page.
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>
    )
}
