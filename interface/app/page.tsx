import { DashboardDataWrapper } from '@/components/home/dashboard-data-wrapper'
import { RiskTrends } from '@/components/home/risk-trends'
import { SystemLogPanel } from '@/components/home/system-log-panel'
import { ActivityFeed } from '@/components/home/activity-feed'

export default function HomePage() {
    return (
        <div className="space-y-6">
            <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>

            <DashboardDataWrapper />
        </div>
    )
}
