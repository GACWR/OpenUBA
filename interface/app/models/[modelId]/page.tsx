'use client'

import { useQuery } from '@apollo/client'
import { GET_MODEL } from '@/lib/graphql/queries'
import { ModelDetailHeader } from '@/components/models/model-detail-header'
import { ModelJobsTab } from '@/components/models/model-jobs-tab'
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"

export default function ModelDetailPage({ params }: { params: { modelId: string } }) {
    const { data, loading, error } = useQuery(GET_MODEL, {
        variables: { id: params.modelId }
    })

    const model = data?.modelById

    if (loading) return <div>Loading...</div>
    if (error) return <div>Error: {error.message}</div>
    if (!model) return <div>Model not found</div>

    return (
        <div className="space-y-6">
            <ModelDetailHeader modelId={params.modelId} model={model} />

            <Tabs defaultValue="overview" className="space-y-4">
                <TabsList>
                    <TabsTrigger value="overview">Overview</TabsTrigger>
                    <TabsTrigger value="versions">Versions</TabsTrigger>
                    <TabsTrigger value="runs">Runs</TabsTrigger>
                    <TabsTrigger value="config">Config</TabsTrigger>
                    <TabsTrigger value="logs">Logs</TabsTrigger>
                </TabsList>

                <TabsContent value="overview">
                    <div className="p-4 border rounded-md space-y-4">
                        <div>
                            <h3 className="text-lg font-medium">Description</h3>
                            <p className="text-muted-foreground mt-2">
                                {model.description || 'No description provided.'}
                            </p>
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <h4 className="font-medium text-sm text-muted-foreground">Author</h4>
                                <p>{model.author || '-'}</p>
                            </div>
                            <div>
                                <h4 className="font-medium text-sm text-muted-foreground">Source Type</h4>
                                <p>{model.sourceType}</p>
                            </div>
                            <div>
                                <h4 className="font-medium text-sm text-muted-foreground">Version</h4>
                                <p>{model.version}</p>
                            </div>
                            <div>
                                <h4 className="font-medium text-sm text-muted-foreground">Created At</h4>
                                <p>{new Date(model.createdAt).toLocaleDateString()}</p>
                            </div>
                        </div>
                    </div>
                </TabsContent>

                <TabsContent value="runs">
                    <ModelJobsTab modelId={params.modelId} />
                </TabsContent>

                <TabsContent value="versions">
                    <div className="p-4 border rounded-md">
                        <p className="text-muted-foreground">Current Version: {model.version}</p>
                        {/* TODO: List historical versions */}
                    </div>
                </TabsContent>

                <TabsContent value="config">
                    <div className="p-4 border rounded-md">
                        <pre className="bg-muted p-4 rounded-md overflow-auto text-xs">
                            {JSON.stringify(model.manifest, null, 2)}
                        </pre>
                    </div>
                </TabsContent>

                <TabsContent value="logs">
                    <div className="p-4 border rounded-md text-muted-foreground">
                        Log streaming not yet implemented.
                    </div>
                </TabsContent>
            </Tabs>
        </div>
    )
}
