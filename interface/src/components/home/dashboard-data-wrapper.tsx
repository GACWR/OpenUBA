'use client'

import { useMemo } from 'react'
import { useQuery } from '@apollo/client'
import { GET_MODELS, GET_ANOMALIES, GET_CASES } from '@/lib/graphql/queries'
import { DashboardSummary } from './dashboard-summary'
import { RiskTrends } from './risk-trends'
import { SystemLogPanel } from './system-log-panel'
import { DonutChart } from '@/components/charts/donut-chart'
import { BarChartComponent } from '@/components/charts/bar-chart'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'

function DashboardSkeleton() {
    return (
        <div className="space-y-4">
            {/* row 1: chart skeletons */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <Card>
                    <CardHeader className="pb-2">
                        <Skeleton className="h-4 w-36" />
                        <Skeleton className="h-3 w-48 mt-1" />
                    </CardHeader>
                    <CardContent>
                        <Skeleton className="w-full h-[240px]" />
                    </CardContent>
                </Card>
                <div className="grid grid-rows-2 gap-4">
                    {[200, 200].map((h, i) => (
                        <Card key={i}>
                            <CardHeader className="pb-2"><Skeleton className="h-4 w-28" /></CardHeader>
                            <CardContent><Skeleton className="w-full" style={{ height: h }} /></CardContent>
                        </Card>
                    ))}
                </div>
            </div>
            {/* row 2: KPI skeletons */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {Array.from({ length: 8 }).map((_, i) => (
                    <Card key={i}>
                        <CardContent className="pt-3 pb-3 px-3">
                            <Skeleton className="h-3 w-20 mb-2" />
                            <Skeleton className="h-6 w-12" />
                        </CardContent>
                    </Card>
                ))}
            </div>
            {/* row 3: system events skeleton */}
            <Card>
                <CardHeader className="pb-2"><Skeleton className="h-4 w-28" /></CardHeader>
                <CardContent className="space-y-2">
                    {Array.from({ length: 5 }).map((_, i) => (
                        <div key={i} className="flex items-center gap-2">
                            <Skeleton className="h-3 w-16" />
                            <Skeleton className="h-4 w-12 rounded-full" />
                            <Skeleton className="h-3 w-20" />
                            <Skeleton className="h-3 flex-1" />
                        </div>
                    ))}
                </CardContent>
            </Card>
        </div>
    )
}

export function DashboardDataWrapper() {
    const { data: modelsData, loading: modelsLoading } = useQuery(GET_MODELS, { pollInterval: 10000 })
    const { data: anomaliesData, loading: anomaliesLoading } = useQuery(GET_ANOMALIES, { pollInterval: 10000 })
    const { data: casesData, loading: casesLoading } = useQuery(GET_CASES, { pollInterval: 10000 })

    const isLoading = modelsLoading || anomaliesLoading || casesLoading
    const models = modelsData?.allModels?.nodes || []
    const anomalies = anomaliesData?.allAnomalies?.nodes || []
    const cases = casesData?.allCases?.nodes || []

    // All hooks must be called before any early return (React rules of hooks)

    // Risk trends (7-day)
    const riskTrendsData = useMemo(() => {
        const riskTrendsMap = new Map<string, { date: string, low: number, medium: number, high: number, critical: number }>()
        for (let i = 6; i >= 0; i--) {
            const d = new Date()
            d.setDate(d.getDate() - i)
            const dateStr = d.toISOString().split('T')[0]
            riskTrendsMap.set(dateStr, { date: dateStr, low: 0, medium: 0, high: 0, critical: 0 })
        }
        anomalies.forEach((a: any) => {
            const dateStr = new Date(a.timestamp).toISOString().split('T')[0]
            if (riskTrendsMap.has(dateStr)) {
                const entry = riskTrendsMap.get(dateStr)!
                const score = a.riskScore || 0
                if (score > 80) entry.critical++
                else if (score > 50) entry.high++
                else if (score > 20) entry.medium++
                else entry.low++
            }
        })
        return Array.from(riskTrendsMap.values())
    }, [anomalies])

    // Anomaly severity distribution
    const anomalySeverityData = useMemo(() => {
        const high = anomalies.filter((a: any) => (a.riskScore || 0) >= 80).length
        const medium = anomalies.filter((a: any) => (a.riskScore || 0) >= 50 && (a.riskScore || 0) < 80).length
        const low = anomalies.filter((a: any) => (a.riskScore || 0) < 50).length
        return [
            { name: 'high (80+)', value: high },
            { name: 'medium (50-79)', value: medium },
            { name: 'low (0-49)', value: low },
        ]
    }, [anomalies])

    // Cases by severity
    const caseSeverityData = useMemo(() => {
        const counts: Record<string, number> = { critical: 0, high: 0, medium: 0, low: 0 }
        cases.forEach((c: any) => { if (counts[c.severity] !== undefined) counts[c.severity]++ })
        return Object.entries(counts).map(([severity, count]) => ({ severity, count }))
    }, [cases])

    if (isLoading && models.length === 0 && anomalies.length === 0 && cases.length === 0) {
        return <DashboardSkeleton />
    }

    // Calculate metrics
    const totalModels = models.length
    const activeModels = models.filter((m: any) => m.status === 'active' || m.enabled).length
    const totalAnomalies = anomalies.length
    const unacknowledgedAnomalies = anomalies.filter((a: any) => !a.acknowledged).length
    const openCases = cases.filter((c: any) => c.status !== 'closed').length
    const uniqueEntities = new Set(anomalies.map((a: any) => a.entityId))
    const monitoredUsers = uniqueEntities.size
    const highRiskUsers = new Set(anomalies.filter((a: any) => (a.riskScore || 0) > 70).map((a: any) => a.entityId)).size

    const summary = {
        total_models: totalModels,
        active_models: activeModels,
        total_anomalies: totalAnomalies,
        unacknowledged_anomalies: unacknowledgedAnomalies,
        open_cases: openCases,
        monitored_users: monitoredUsers || 0,
        high_risk_users: highRiskUsers || 0,
        users_discovered: monitoredUsers || 0,
    }

    return (
        <div className="space-y-4">
            {/* row 1: charts — risk trends (6/12) | anomaly severity + cases (6/12) */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <RiskTrends data={riskTrendsData} />
                <div className="grid grid-rows-2 gap-4">
                    <Card>
                        <CardHeader className="pb-2">
                            <CardTitle className="text-sm font-semibold">anomaly severity</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <DonutChart
                                data={anomalySeverityData}
                                colors={['#ef4444', '#f59e0b', '#22c55e']}
                                height={160}
                                centerLabel={`${totalAnomalies}`}
                            />
                        </CardContent>
                    </Card>
                    <Card>
                        <CardHeader className="pb-2">
                            <CardTitle className="text-sm font-semibold">cases by severity</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <BarChartComponent
                                data={caseSeverityData}
                                xKey="severity"
                                yKeys={[{ key: 'count', name: 'cases', color: '#8b5cf6' }]}
                                height={160}
                            />
                        </CardContent>
                    </Card>
                </div>
            </div>

            {/* row 2: KPI cards grid */}
            <DashboardSummary summary={summary} />

            {/* row 3: system events */}
            <SystemLogPanel />
        </div>
    )
}
