'use client'

import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { ModelLibraryTab } from './model-library-tab'
import { ModelInstalledTab } from './model-installed-tab'
import { ModelJobsTab } from './model-jobs-tab'

export function ModelsPageShell() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Models</h1>
        <p className="text-muted-foreground">manage and execute analytics models</p>
      </div>
      
      <Tabs defaultValue="installed" className="w-full">
        <TabsList>
          <TabsTrigger value="library">library</TabsTrigger>
          <TabsTrigger value="installed">installed</TabsTrigger>
          <TabsTrigger value="jobs">jobs</TabsTrigger>
        </TabsList>
        
        <TabsContent value="library">
          <ModelLibraryTab />
        </TabsContent>
        
        <TabsContent value="installed">
          <ModelInstalledTab />
        </TabsContent>
        
        <TabsContent value="jobs">
          <ModelJobsTab />
        </TabsContent>
      </Tabs>
    </div>
  )
}
