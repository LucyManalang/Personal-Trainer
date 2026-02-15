import { useState, useEffect } from 'react';
import api from '../api/client';
import GoalModal from './GoalModal';

export default function GoalList() {
    const [goals, setGoals] = useState([]);
    const [loading, setLoading] = useState(true);
    const [editingGoal, setEditingGoal] = useState(null);
    const [isCreating, setIsCreating] = useState(false);
    const [showPreferences, setShowPreferences] = useState(true);

    useEffect(() => {
        fetchGoals();
    }, []);

    const fetchGoals = () => {
        api.get('/data/goals')
            .then(res => setGoals(res.data))
            .catch(err => console.error("Failed to fetch goals:", err))
            .finally(() => setLoading(false));
    };

    const handleSave = (goalData) => {
        // Optimistic updatish or just refreshed
        const promise = editingGoal
            ? api.put(`/data/goals/${editingGoal.id}`, goalData)
            : api.post('/data/goals', goalData);

        promise
            .then(() => {
                fetchGoals();
                setEditingGoal(null);
                setIsCreating(false);
            })
            .catch(err => console.error("Failed to save goal:", err));
    };

    const handleDelete = () => {
        if (!editingGoal) return;
        if (confirm('Are you sure you want to delete this goal?')) {
            api.delete(`/data/goals/${editingGoal.id}`)
                .then(() => {
                    setGoals(prev => prev.filter(g => g.id !== editingGoal.id));
                    setEditingGoal(null);
                })
                .catch(err => console.error("Failed to delete goal:", err));
        }
    };

    // Filter and Sort
    // 1. Filter out completed.
    // 2. Filter out past dated goals (events that have passed).
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    const activeGoals = goals.filter(g => {
        if (g.is_completed) return false;
        if (g.target_date && new Date(g.target_date) < today) return false;
        return true;
    });

    const datedGoals = activeGoals.filter(g => g.target_date).sort((a, b) => new Date(a.target_date) - new Date(b.target_date));
    const undatedGoals = activeGoals.filter(g => !g.target_date);

    return (
        <div className="bg-gray-800 rounded-xl p-6 border border-gray-700 h-full flex flex-col">
            <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold text-purple-400 flex items-center gap-2">
                    <span className="text-xl">🎯</span> Goals
                </h3>
                <button
                    onClick={() => setIsCreating(true)}
                    className="text-gray-400 hover:text-white p-1 rounded-full hover:bg-gray-700 transition"
                    title="Add Goal"
                >
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                    </svg>
                </button>
            </div>

            {loading && <div className="text-gray-500 text-sm">Loading goals...</div>}

            <div className="space-y-6 overflow-y-auto flex-1 pr-2">
                {/* Dated Goals (Events) */}
                {datedGoals.length > 0 && (
                    <div className="space-y-2">
                        <h4 className="text-xs font-bold text-gray-500 uppercase tracking-wider sticky top-0 bg-gray-800 py-1">Upcoming Events</h4>
                        {datedGoals.map(goal => (
                            <div
                                key={goal.id}
                                onClick={() => setEditingGoal(goal)}
                                className="bg-gray-700/50 p-3 rounded-lg border-l-4 border-blue-500 cursor-pointer hover:bg-gray-700 transition group"
                            >
                                <div className="flex justify-between items-start">
                                    <div className="text-sm text-gray-200 font-medium">{goal.description}</div>
                                    {/* Checkbox visual placeholder (func via modal) */}
                                </div>
                                <div className="text-xs text-blue-300 mt-1 flex items-center gap-1">
                                    <span>📅</span>
                                    {new Date(goal.target_date).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })}
                                </div>
                            </div>
                        ))}
                    </div>
                )}

                {/* Undated Goals (Preferences) */}
                <div className="space-y-2">
                    <div
                        className="flex items-center justify-start cursor-pointer group"
                        onClick={() => setShowPreferences(!showPreferences)}
                    >
                        <span className="text-xs text-gray-600 group-hover:text-gray-400 transition">{showPreferences ? '▼' : '▶'}</span>
                        <span className="w-2" />
                        <h4 className="text-xs font-bold text-gray-500 uppercase tracking-wider bg-gray-800 py-1">Preferences & Habits</h4>
                    </div>

                    {showPreferences && (
                        <div className="space-y-2">
                            {undatedGoals.length === 0 && <div className="text-xs text-gray-600 italic">No preferences set.</div>}
                            {undatedGoals.map(goal => (
                                <div
                                    key={goal.id}
                                    onClick={() => setEditingGoal(goal)}
                                    className="bg-gray-700/30 p-3 rounded-lg border border-gray-700 cursor-pointer hover:bg-gray-700 transition"
                                >
                                    <div className="text-xs text-purple-300 uppercase font-bold mb-1 opacity-75">{goal.type.replace('_', ' ')}</div>
                                    <div className="text-sm text-gray-300">{goal.description}</div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>

            {(editingGoal || isCreating) && (
                <GoalModal
                    goal={editingGoal}
                    onClose={() => { setEditingGoal(null); setIsCreating(false); }}
                    onSave={handleSave}
                    onDelete={editingGoal ? handleDelete : undefined}
                />
            )}
        </div>
    );
}
