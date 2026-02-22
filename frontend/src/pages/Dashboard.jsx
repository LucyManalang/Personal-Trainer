import { useState, useEffect } from 'react'
import GoalList from '../components/GoalList'
import WeeklySchedule from '../components/WeeklySchedule'
import DailyPlan from '../components/DailyPlan'
import api from '../api/client'

export default function Dashboard() {
    const [name, setName] = useState('');

    useEffect(() => {
        api.get('/auth/user')
            .then(res => setName(res.data.name || ''))
            .catch(() => { });
    }, []);

    return (
        <div className="space-y-4 sm:space-y-6">
            <header className="mb-2 sm:mb-4">
                <h2 className="text-2xl sm:text-3xl font-bold mb-1">Hello{name ? `, ${name}` : ''}</h2>
                <p className="text-sm sm:text-base text-gray-500 dark:text-gray-400">Ready to crush your goals today?</p>
            </header>

            <div className="grid grid-cols-1 md:grid-cols-12 gap-4 sm:gap-6">
                {/* Daily Plan (Top Priority) */}
                <div className="md:col-span-8 order-1">
                    <DailyPlan />
                </div>

                {/* Goals Context */}
                <div className="md:col-span-4 order-2 relative">
                    <div className="md:absolute md:inset-0">
                        <GoalList />
                    </div>
                </div>

                {/* Weekly Schedule Preview */}
                <div className="md:col-span-12 order-3">
                    <WeeklySchedule />
                </div>
            </div>
        </div>
    )
}
