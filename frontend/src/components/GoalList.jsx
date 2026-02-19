import { useState, useEffect, useRef } from 'react';
import api from '../api/client';
import GoalModal from './GoalModal';

const DAY_LABELS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

export default function GoalList() {
    const [goals, setGoals] = useState([]);
    const [loading, setLoading] = useState(true);
    const [editingGoal, setEditingGoal] = useState(null);
    const [isCreating, setIsCreating] = useState(false);
    const [showPreferences, setShowPreferences] = useState(true);
    const [showGoals, setShowGoals] = useState(true);
    const [showSchedule, setShowSchedule] = useState(true);

    // Schedule state: { "0": ["Gym", 60], "1": ["Ultimate", 120], ... }
    const [schedule, setSchedule] = useState({});
    const [scheduleSaving, setScheduleSaving] = useState(false);
    const saveTimeout = useRef(null);

    useEffect(() => {
        fetchGoals();
        fetchSchedule();
    }, []);

    const fetchGoals = () => {
        api.get('/data/goals')
            .then(res => setGoals(res.data))
            .catch(err => console.error("Failed to fetch goals:", err))
            .finally(() => setLoading(false));
    };

    const fetchSchedule = () => {
        api.get('/data/schedule')
            .then(res => {
                const saved = res.data.schedule || {};
                // Build full 7-day schedule, filling in blanks
                const full = {};
                for (let i = 0; i < 7; i++) {
                    full[String(i)] = saved[String(i)] || ['', 0];
                }
                setSchedule(full);
            })
            .catch(err => console.error("Failed to fetch schedule:", err));
    };

    const handleScheduleChange = (dayIdx, field, value) => {
        setSchedule(prev => {
            const updated = { ...prev };
            const entry = [...(updated[String(dayIdx)] || ['', 0])];
            if (field === 'type') entry[0] = value;
            if (field === 'duration') entry[1] = parseInt(value) || 0;
            updated[String(dayIdx)] = entry;
            return updated;
        });

        // Debounced auto-save
        if (saveTimeout.current) clearTimeout(saveTimeout.current);
        saveTimeout.current = setTimeout(() => {
            saveSchedule();
        }, 800);
    };

    const saveSchedule = () => {
        setScheduleSaving(true);
        // Use latest state via functional access
        setSchedule(current => {
            api.put('/data/schedule', { schedule: current })
                .catch(err => console.error("Failed to save schedule:", err))
                .finally(() => setScheduleSaving(false));
            return current;
        });
    };

    const handleSave = (goalData) => {
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
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    const activeGoals = goals.filter(g => {
        if (g.is_completed) return false;
        if (g.target_date && new Date(g.target_date) < today) return false;
        return true;
    });

    const datedGoals = activeGoals.filter(g => g.target_date).sort((a, b) => new Date(a.target_date) - new Date(b.target_date));
    const preferenceGoals = activeGoals.filter(g => !g.target_date && g.type === 'preference');
    const undatedGoals = activeGoals.filter(g => !g.target_date && g.type !== 'preference');

    // Collapsible section header
    const SectionHeader = ({ label, isOpen, onToggle }) => (
        <div
            className="flex items-center justify-start cursor-pointer group"
            onClick={onToggle}
        >
            <span className="text-xs text-gray-600 group-hover:text-gray-400 transition">{isOpen ? '▼' : '▶'}</span>
            <span className="w-2" />
            <h4 className="text-xs font-bold text-gray-500 uppercase tracking-wider bg-gray-800 py-1">{label}</h4>
        </div>
    );

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
                                </div>
                                <div className="text-xs text-blue-300 mt-1 flex items-center gap-1">
                                    <span>📅</span>
                                    {new Date(goal.target_date).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })}
                                </div>
                            </div>
                        ))}
                    </div>
                )}

                {/* Preferences (type === 'preference') */}
                <div className="space-y-2">
                    <SectionHeader label="Preferences" isOpen={showPreferences} onToggle={() => setShowPreferences(!showPreferences)} />
                    {showPreferences && (
                        <div className="space-y-2">
                            {preferenceGoals.length === 0 && <div className="text-xs text-gray-600 italic">No preferences set.</div>}
                            {preferenceGoals.map(goal => (
                                <div
                                    key={goal.id}
                                    onClick={() => setEditingGoal(goal)}
                                    className="bg-gray-700/30 p-3 rounded-lg border border-gray-700 cursor-pointer hover:bg-gray-700 transition"
                                >
                                    <div className="text-sm text-gray-300">{goal.description}</div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Goals (short_term, long_term, other) */}
                <div className="space-y-2">
                    <SectionHeader label="Goals" isOpen={showGoals} onToggle={() => setShowGoals(!showGoals)} />
                    {showGoals && (
                        <div className="space-y-2">
                            {undatedGoals.length === 0 && <div className="text-xs text-gray-600 italic">No goals set.</div>}
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

                {/* Schedule (Manual weekly input) */}
                <div className="space-y-2">
                    <div className="flex items-center justify-between">
                        <SectionHeader label="Schedule" isOpen={showSchedule} onToggle={() => setShowSchedule(!showSchedule)} />
                        {scheduleSaving && <span className="text-xs text-blue-400 animate-pulse">Saving...</span>}
                    </div>
                    {showSchedule && (
                        <div className="space-y-1.5">
                            {DAY_LABELS.map((day, idx) => (
                                <div key={idx} className="flex items-center gap-2 bg-gray-700/30 rounded-lg px-3 py-2 border border-gray-700">
                                    <span className="text-xs text-gray-400 font-bold w-8 shrink-0">{day}</span>
                                    <input
                                        type="text"
                                        value={schedule[String(idx)]?.[0] || ''}
                                        onChange={e => handleScheduleChange(idx, 'type', e.target.value)}
                                        placeholder="Activity"
                                        className="flex-1 bg-gray-700 border border-gray-600 rounded px-2 py-1 text-sm text-white placeholder-gray-500 focus:border-blue-500 focus:outline-none transition min-w-0"
                                    />
                                    <div className="relative shrink-0">
                                        <input
                                            type="number"
                                            value={schedule[String(idx)]?.[1] || ''}
                                            onChange={e => handleScheduleChange(idx, 'duration', e.target.value)}
                                            placeholder="0"
                                            className="w-16 bg-gray-700 border border-gray-600 rounded pl-2 pr-8 py-1 text-sm text-white text-right focus:border-blue-500 focus:outline-none transition [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                                        />
                                        <span className="absolute right-2 top-1/2 -translate-y-1/2 text-xs text-gray-500">min</span>
                                    </div>
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
