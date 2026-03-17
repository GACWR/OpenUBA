'use client'

import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { ModelLibraryTab } from './model-library-tab'
import { ModelInstalledTab } from './model-installed-tab'
import Link from 'next/link'
import { ExternalLink } from 'lucide-react'

export function ModelsPageShell() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Models</h1>
          <p className="text-muted-foreground">manage and execute analytics models</p>
        </div>
        <Link
          href="/jobs"
          className="inline-flex items-center gap-2 rounded-md border border-white/10 px-3 py-2 text-sm font-medium hover:bg-muted/40 transition-colors text-muted-foreground hover:text-foreground"
        >
          <ExternalLink className="h-4 w-4" /> View all jobs
        </Link>
      </div>

      <Tabs defaultValue="installed" className="w-full">
        <TabsList>
          <TabsTrigger value="library">library</TabsTrigger>
          <TabsTrigger value="installed">installed</TabsTrigger>
        </TabsList>

        <TabsContent value="library">
          <ModelLibraryTab />
        </TabsContent>

        <TabsContent value="installed">
          <ModelInstalledTab />
        </TabsContent>
      </Tabs>
    </div>
  )
}
