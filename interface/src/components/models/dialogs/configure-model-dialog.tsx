'use client'

import { useState, useEffect } from 'react'
import { useQuery } from '@apollo/client'
import { GET_MODEL } from '@/lib/graphql/queries'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { useAuth } from '@/lib/auth-provider'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface ConfigureModelDialogProps {
    model: any
    open: boolean
    onOpenChange: (open: boolean) => void
    onExecute: (config: any, artifactId?: string) => void
    onTrain: (config: any) => void
    executing: boolean
    training: boolean
    initialTab?: string
}

export function ConfigureModelDialog({
    model,
    open,
    onOpenChange,
    onExecute,
    onTrain,
    executing,
    training,
    initialTab
}: ConfigureModelDialogProps) {
    const [activeTab, setActiveTab] = useState(initialTab || 'infer')

    // ensure tab updates if prop changes when reopening
    useEffect(() => {
        if (open && initialTab) {
            setActiveTab(initialTab)
        }
    }, [open, initialTab])

    const { data: modelDetails } = useQuery(GET_MODEL, {
        variables: { id: model.id },
        skip: !open // Only fetch when open
    })

    const [executionConfig, setExecutionConfig] = useState({
        dataSource: 'elasticsearch',
        tableName: '',
        indexName: '',
        filePath: '',
        sourceGroupSlug: ''
    })

    const [selectedArtifactId, setSelectedArtifactId] = useState<string>('latest')

    const [sparkTables, setSparkTables] = useState<string[]>([])
    const [esIndices, setEsIndices] = useState<string[]>([])
    const [sourceGroups, setSourceGroups] = useState<any[]>([])
    const [loadingDataSources, setLoadingDataSources] = useState(false)
    const { authFetch } = useAuth()

    // Fetch data sources
    useEffect(() => {
        if (open) {
            fetchDataSources()
        }
    }, [open, executionConfig.dataSource])

    const fetchDataSources = async () => {
        const controller = new AbortController()
        const timeoutId = setTimeout(() => controller.abort(), 15000)
        setLoadingDataSources(true)
        try {
            if (executionConfig.dataSource === 'spark' && sparkTables.length === 0) {
                const res = await authFetch(`${API_URL}/api/v1/data/metrics/spark`, { signal: controller.signal })
                const data = await res.json()
                setSparkTables(Object.keys(data.tables || {}))
            } else if (executionConfig.dataSource === 'elasticsearch' && esIndices.length === 0) {
                const res = await authFetch(`${API_URL}/api/v1/data/metrics/elasticsearch`, { signal: controller.signal })
                const data = await res.json()
                setEsIndices(Object.keys(data.indices || {}))
            } else if (executionConfig.dataSource === 'source_group' && sourceGroups.length === 0) {
                const res = await authFetch(`${API_URL}/api/v1/source_groups/`, { signal: controller.signal })
                const data = await res.json()
                setSourceGroups(data)
            }
        } catch (err: any) {
            if (err.name === 'AbortError') {
                console.warn('data source fetch timed out')
            } else {
                console.error('error fetching data sources:', err)
            }
        } finally {
            clearTimeout(timeoutId)
            setLoadingDataSources(false)
        }
    }

    // Filter artifacts (checkpoints/weights) from model components
    const artifacts = modelDetails?.modelById?.components?.filter((c: any) =>
        // Check for componentType (GraphQL camelCase) or component_type (DB snake_case)
        ['weights', 'checkpoint', 'artifact'].includes(c.componentType || c.component_type)
    ) || []

    // Ensure latest is select by default if artifacts exist
    useEffect(() => {
        if (artifacts.length > 0 && selectedArtifactId === 'latest') {
            // Option to keep 'latest' as special value, or select first
        }
    }, [artifacts])

    const handleRun = () => {
        const artifactId = selectedArtifactId === 'latest' ? undefined : selectedArtifactId
        onExecute(executionConfig, artifactId)
    }

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-[600px]">
                <DialogHeader>
                    <DialogTitle>configure {model.name}</DialogTitle>
                </DialogHeader>

                <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
                    <TabsList className="grid w-full grid-cols-2">
                        <TabsTrigger value="infer">inference (run)</TabsTrigger>
                        <TabsTrigger value="train">training</TabsTrigger>
                    </TabsList>

                    <div className="py-4 space-y-4">
                        {/* Common Data Source Config */}
                        <div className="space-y-2">
                            <Label>data source</Label>
                            <Select
                                value={executionConfig.dataSource}
                                onValueChange={(value) => setExecutionConfig({ ...executionConfig, dataSource: value })}
                            >
                                <SelectTrigger>
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="spark">spark table</SelectItem>
                                    <SelectItem value="elasticsearch">elasticsearch index</SelectItem>
                                    <SelectItem value="local_csv">local csv file</SelectItem>
                                    <SelectItem value="source_group">source group (v2)</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>

                        {executionConfig.dataSource === 'spark' && (
                            <div className="space-y-2">
                                <Label>spark table</Label>
                                <Select
                                    value={executionConfig.tableName}
                                    onValueChange={(value) => setExecutionConfig({ ...executionConfig, tableName: value })}
                                >
                                    <SelectTrigger>
                                        <SelectValue placeholder={loadingDataSources ? "loading tables..." : "select table..."} />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {sparkTables.map(table => (
                                            <SelectItem key={table} value={table}>{table}</SelectItem>
                                        ))}
                                        {!loadingDataSources && sparkTables.length === 0 && (
                                            <div className="px-2 py-1.5 text-sm text-muted-foreground">no tables found</div>
                                        )}
                                    </SelectContent>
                                </Select>
                            </div>
                        )}

                        {executionConfig.dataSource === 'elasticsearch' && (
                            <div className="space-y-2">
                                <Label>elasticsearch index</Label>
                                <Select
                                    value={executionConfig.indexName}
                                    onValueChange={(value) => setExecutionConfig({ ...executionConfig, indexName: value })}
                                >
                                    <SelectTrigger>
                                        <SelectValue placeholder={loadingDataSources ? "loading indices..." : "select index..."} />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {esIndices.map(index => (
                                            <SelectItem key={index} value={index}>{index}</SelectItem>
                                        ))}
                                        {!loadingDataSources && esIndices.length === 0 && (
                                            <div className="px-2 py-1.5 text-sm text-muted-foreground">no indices found</div>
                                        )}
                                    </SelectContent>
                                </Select>
                            </div>
                        )}

                        {executionConfig.dataSource === 'local_csv' && (
                            <div className="space-y-2">
                                <Label>file path</Label>
                                <Input
                                    value={executionConfig.filePath}
                                    onChange={(e) => setExecutionConfig({ ...executionConfig, filePath: e.target.value })}
                                    placeholder="/path/to/file.csv"
                                />
                            </div>
                        )}

                        {executionConfig.dataSource === 'source_group' && (
                            <div className="space-y-2">
                                <Label>source group</Label>
                                <Select
                                    value={executionConfig.sourceGroupSlug}
                                    onValueChange={(value) => setExecutionConfig({ ...executionConfig, sourceGroupSlug: value })}
                                >
                                    <SelectTrigger>
                                        <SelectValue placeholder="select source group..." />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {sourceGroups.map((sg: any) => (
                                            <SelectItem key={sg.slug} value={sg.slug}>{sg.slug}</SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            </div>
                        )}

                        {/* Inference Specific: Artifact Selection */}
                        <TabsContent value="infer" className="space-y-4 mt-0">
                            <div className="space-y-2 pt-2 border-t">
                                <Label>checkpoint / artifact</Label>
                                <Select
                                    value={selectedArtifactId}
                                    onValueChange={setSelectedArtifactId}
                                >
                                    <SelectTrigger>
                                        <SelectValue placeholder="select checkpoint..." />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="latest">latest available</SelectItem>
                                        {artifacts.map((a: any) => (
                                            <SelectItem key={a.id} value={a.id}>
                                                {a.filename} ({new Date(a.createdAt || a.created_at).toLocaleDateString()})
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            </div>

                            <div className="flex justify-end pt-4">
                                <Button onClick={handleRun} disabled={executing}>
                                    {executing ? 'running logic...' : 'run inference'}
                                </Button>
                            </div>
                        </TabsContent>

                        {/* Training Specific */}
                        <TabsContent value="train" className="space-y-4 mt-0">
                            <div className="pt-2 border-t">
                                <p className="text-sm text-muted-foreground mb-4">
                                    training will create a new checkpoint artifact upon completion.
                                </p>
                                <div className="flex justify-end">
                                    <Button onClick={() => onTrain(executionConfig)} disabled={training}>
                                        {training ? 'training started...' : 'start training'}
                                    </Button>
                                </div>
                            </div>
                        </TabsContent>
                    </div>
                </Tabs>
            </DialogContent>
        </Dialog>
    )
}
