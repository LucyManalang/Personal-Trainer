import { useState, useEffect } from 'react';
import api from '../api/client';
import PlanEditChat from './PlanEditChat';

export default function DailyPlan() {
    const [plan, setPlan] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [syncInfo, setSyncInfo] = useState(null);
    const [editingDay, setEditingDay] = useState(null); // { idx: 0|1, label: "today"|"tomorrow" }

    useEffect(() => {
        handleGenerate();
    }, []);

    const handleGenerate = () => {
        setLoading(true);
        setError(null);
        setSyncInfo(null);
        api.post('/coach/plan-3-day')
            .then(res => {
                if (res.data.sync) setSyncInfo(res.data.sync);
                if (res.data.plan && Array.isArray(res.data.plan)) {
                    setPlan(res.data.plan);
                } else if (res.data.message) {
                    setError(res.data.message);
                } else {
                    setError("Received invalid plan format from AI Coach.");
                }
            })
            .catch(err => {
                console.error(err);
                setError("Failed to generate plan. Please try again.");
            })
            .finally(() => setLoading(false));
    };

    const renderSyncStatus = () => {
        if (!syncInfo) return null;
        const displayNames = { strava: 'Strava', whoop: 'WHOOP' };
        const items = [];

        for (const [service, info] of Object.entries(syncInfo)) {
            const name = displayNames[service] || service;
            if (info.error && info.error !== "Not connected") {
                items.push(<span key={service} className="text-amber-400">⚠ {name} sync failed</span>);
            } else if (info.error === "Not connected") {
                // Skip disconnected services
            } else {
                if (info.synced > 0) {
                    items.push(<span key={service} className="text-emerald-400">✓ {name}: {info.synced} new</span>);
                } else {
                    items.push(<span key={service} className="text-emerald-400">✓ {name}</span>);
                }
            }
        }

        if (items.length === 0) return null;
        return (
            <div className="flex items-center gap-3 text-xs px-3 py-1.5 bg-gray-700/30 rounded-lg border border-gray-700">
                <span className="text-gray-500 font-medium">Sync</span>
                {items}
            </div>
        );
    };

    return (
        <div className="bg-gray-800 rounded-xl p-6 border border-gray-700 shadow-lg h-full min-h-[400px]">
            <div className="flex justify-between items-center mb-4">
                <div>
                    <h3 className="text-xl font-semibold text-blue-400">Daily Plan</h3>
                    <p className="text-xs text-gray-400">Based on your recovery & goals</p>
                </div>
                <div className="flex items-center gap-2">
                    {renderSyncStatus()}
                    <button
                        onClick={handleGenerate}
                        disabled={loading}
                        className="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg text-sm font-medium transition disabled:opacity-50">
                        {loading ? 'Syncing & Thinking...' : 'Refresh'}
                    </button>
                </div>
            </div>



            {error && <div className="text-red-400 text-sm mb-4">{error}</div>}

            {!plan && !loading && !error && (
                <div className="bg-gray-900/50 rounded-lg p-8 text-center text-gray-500">
                    <p>No plan generated yet.</p>
                    <p className="text-sm mt-2">Click "Refresh" to consult your AI Coach.</p>
                </div>
            )}

            {plan && (
                <div className="space-y-4">
                    {plan.map((day, idx) => {
                        // Guard against null/malformed day objects
                        if (!day || typeof day !== 'object') return null;

                        // Helper to safely render text
                        const renderText = (val) => {
                            if (typeof val === 'string') return val;
                            if (typeof val === 'number') return String(val);
                            if (Array.isArray(val)) return val.map(v => renderText(v)).join('\n');
                            if (val && typeof val === 'object') {
                                // Try to extract meaningful text from nested objects
                                return Object.entries(val)
                                    .map(([k, v]) => {
                                        const text = renderText(v);
                                        // Skip keys that look like metadata
                                        if (!text) return '';
                                        // If the value is just a string, prefix with key for context
                                        return `${k}: ${text}`;
                                    })
                                    .filter(Boolean)
                                    .join('\n');
                            }
                            return '';
                        };

                        const getIntensityClass = (intensity) => {
                            const val = String(intensity).toLowerCase();
                            if (val.includes('low')) return 'bg-green-900/20 text-green-400 border-green-700/50';
                            if (val.includes('mod') || val.includes('med')) return 'bg-yellow-900/20 text-yellow-400 border-yellow-700/50';
                            if (val.includes('high')) return 'bg-red-900/20 text-red-400 border-red-700/50';
                            return 'bg-gray-900/20 text-gray-400 border-gray-700/50';
                        };

                        return (
                            <div key={idx} className="bg-gray-700/30 rounded-lg p-4 border border-gray-700 flex flex-col md:flex-row gap-4 relative">
                                <div className="md:w-1/4 border-r border-gray-700 pr-4">
                                    <div className="text-blue-300 font-bold uppercase text-sm tracking-wider">{idx === 0 ? "TODAY" : "TOMORROW"} - {renderText(day.block_type)}</div>
                                    <div className="text-sm text-gray-400 mt-1">
                                        {day.date ? new Date(day.date + 'T12:00:00').toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric' }) : ''}
                                    </div>
                                    <div className={`mt-2 inline-block px-2 py-1 rounded text-xs border ${getIntensityClass(day.intensity)}`}>
                                        {day.intensity} Intensity
                                    </div>
                                </div>
                                <div className="md:w-3/4">
                                    <h4 className="font-medium text-white mb-1">{renderText(day.focus)}</h4>
                                    <div className="text-sm text-gray-300 leading-relaxed space-y-2">
                                        {renderText(day.routine).split(/(?=\d+\.\s)/).map((step, i) => {
                                            const trimmed = step.trim();
                                            if (!trimmed) return null;
                                            return (
                                                <p key={i} className="mb-1">
                                                    {trimmed}
                                                </p>
                                            )
                                        })}
                                    </div>
                                    {day.notes && <div className="mt-3 text-xs text-gray-400 italic">💡 {renderText(day.notes)}</div>}
                                </div>
                                {/* Pencil edit button */}
                                <button
                                    onClick={() => setEditingDay({ idx, label: idx === 0 ? 'today' : 'tomorrow' })}
                                    className="absolute bottom-3 left-3 text-gray-500 hover:text-blue-400 transition p-1 rounded hover:bg-gray-700/50"
                                    title="Edit this day's plan"
                                >
                                    <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                                    </svg>
                                </button>
                            </div>
                        );
                    })}
                </div>
            )
            }

            {editingDay && plan && (
                <PlanEditChat
                    dayLabel={editingDay.label}
                    dayPlan={plan[editingDay.idx]}
                    onClose={() => setEditingDay(null)}
                    onPlanUpdated={(updatedPlan) => {
                        setPlan(prev => {
                            const updated = [...prev];
                            updated[editingDay.idx] = updatedPlan;
                            return updated;
                        });
                    }}
                />
            )}
        </div >
    );
}
