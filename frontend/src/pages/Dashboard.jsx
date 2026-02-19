import GoalList from '../components/GoalList'
import WeeklySchedule from '../components/WeeklySchedule'
import DailyPlan from '../components/DailyPlan'

export default function Dashboard() {
    return (
        <div className="space-y-6">
            <header className="mb-4">
                <h2 className="text-3xl font-bold mb-1">Hello, Lucy</h2>
                <p className="text-gray-400">Ready to crush your goals today?</p>
            </header>

            <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
                {/* Daily Plan (Top Priority) */}
                <div className="md:col-span-8">
                    <DailyPlan />
                </div>

                {/* Goals Context */}
                <div className="md:col-span-4 relative">
                    <div className="md:absolute md:inset-0">
                        <GoalList />
                    </div>
                </div>

                {/* Weekly Schedule Preview */}
                <div className="md:col-span-12">
                    <WeeklySchedule />
                </div>
            </div>
        </div>
    )
}
