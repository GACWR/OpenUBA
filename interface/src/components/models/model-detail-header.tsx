'use client'

import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { ArrowLeft, Play, Terminal } from "lucide-react"
import Link from "next/link"

interface ModelDetailHeaderProps {
    modelId: string
    model?: any
}

export function ModelDetailHeader({ modelId, model }: ModelDetailHeaderProps) {
    if (!model) {
        return (
            <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                <div className="flex items-center gap-4">
                    <Link href="/models">
                        <Button variant="ghost" size="icon">
                            <ArrowLeft className="h-4 w-4" />
                        </Button>
                    </Link>
                    <div>
                        <h1 className="text-2xl font-bold tracking-tight">Model {modelId}</h1>
                    </div>
                </div>
            </div>
        )
    }

    return (
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div className="flex items-center gap-4">
                <Link href="/models">
                    <Button variant="ghost" size="icon">
                        <ArrowLeft className="h-4 w-4" />
                    </Button>
                </Link>
                <div>
                    <div className="flex items-center gap-2">
                        <h1 className="text-2xl font-bold tracking-tight">{model.name}</h1>
                        <Badge variant="default">{model.version}</Badge>
                        <Badge className={model.status === 'active' ? 'bg-green-500' : 'bg-yellow-500'}>
                            {model.status}
                        </Badge>
                    </div>
                    <p className="text-muted-foreground">{model.description || 'No description'}</p>
                </div>
            </div>

            <div className="flex items-center gap-2">
                <Button variant="outline">
                    <Terminal className="mr-2 h-4 w-4" />
                    Test Run
                </Button>
                <Button>
                    <Play className="mr-2 h-4 w-4" />
                    Run Live
                </Button>
            </div>
        </div>
    )
}
