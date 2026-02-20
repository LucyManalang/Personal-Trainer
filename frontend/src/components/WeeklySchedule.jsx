import { useState, useEffect } from 'react';
import api from '../api/client';
import EditBlockModal from './EditBlockModal';

export default function WeeklySchedule() {
    const [schedule, setSchedule] = useState([]);
    const [loading, setLoading] = useState(true);
    const [editingBlock, setEditingBlock] = useState(null);

    useEffect(() => {
        fetchSchedule();
    }, []);

    const fetchSchedule = () => {
        const now = new Date();
        // Get local YYYY-MM-DD
        const start = new Date(now.getTime() - (now.getTimezoneOffset() * 60000)).toISOString().split('T')[0];
        api.get(`/schedule/?start_date=${start}`)
            .then(res => setSchedule(res.data))
            .catch(err => console.error("Failed to fetch schedule:", err))
            .finally(() => setLoading(false));
    };

    const handleSaveBlock = (updatedBlock) => {
        api.put(`/schedule/${updatedBlock.id}`, updatedBlock)
            .then(res => {
                setSchedule(prev => prev.map(b => b.id === updatedBlock.id ? res.data : b));
                setEditingBlock(null);
            })
            .catch(err => console.error("Failed to update block:", err));
    };

    return (
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 sm:p-6 border border-gray-200 dark:border-gray-700 transition-colors duration-200">
            <div className="flex justify-between items-center mb-4">
                <h3 className="text-base sm:text-lg font-semibold text-green-600 dark:text-green-400">Week Ahead</h3>
                <button
                    onClick={() => api.post('/schedule/init').then(res => setSchedule(res.data))}
                    className="text-xs bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 px-3 py-1 rounded transition text-gray-700 dark:text-white">
                    Reset
                </button>
            </div>

            {loading && <div className="text-sm text-gray-400">Loading schedule...</div>}

            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-7 gap-2">
                {[...Array(7)].map((_, i) => {
                    const block = schedule[i];
                    return (
                        <div
                            key={i}
                            onClick={() => block && setEditingBlock(block)}
                            className={`p-3 rounded text-center border cursor-pointer transition hover:bg-gray-100 dark:hover:bg-gray-600/50 ${block ? 'border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-700/50' : 'border-dashed border-gray-300 dark:border-gray-700 bg-transparent'}`}
                        >
                            <span className="block text-xs text-gray-500 mb-1">
                                {block ? new Date(block.date + 'T12:00:00').toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' }) : `Day ${i + 1}`}
                            </span>
                            {block ? (
                                <>
                                    <div className="font-bold text-sm text-gray-900 dark:text-white truncate">{block.type}</div>
                                    <div className="text-xs text-gray-500 dark:text-gray-400">{block.planned_duration_minutes} min</div>
                                </>
                            ) : (
                                <span className="text-xs text-gray-400 dark:text-gray-600">Free</span>
                            )}
                        </div>
                    );
                })}
            </div>

            {editingBlock && (
                <EditBlockModal
                    block={editingBlock}
                    onClose={() => setEditingBlock(null)}
                    onSave={handleSaveBlock}
                />
            )}
        </div>
    );
}
