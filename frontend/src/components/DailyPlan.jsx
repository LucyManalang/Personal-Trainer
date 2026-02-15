import { useState, useEffect } from 'react';
import api from '../api/client';

export default function DailyPlan() {
    const [plan, setPlan] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        handleGenerate();
    }, []);

    const handleGenerate = () => {
        setLoading(true);
        setError(null);
        api.post('/coach/plan-3-day')
            .then(res => {
                console.log("Plan response:", res.data); // Debug
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

    return (
        <div className="bg-gray-800 rounded-xl p-6 border border-gray-700 shadow-lg h-full">
            <div className="flex justify-between items-start mb-4">
                <div>
                    <h3 className="text-xl font-semibold text-blue-400">Coach's Plan</h3>
                    <p className="text-xs text-gray-400">Based on your recovery & goals</p>
                </div>
                <button
                    onClick={handleGenerate}
                    disabled={loading}
                    className="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg text-sm font-medium transition disabled:opacity-50">
                    {loading ? 'Thinking...' : 'Refresh / Update Plan'}
                </button>
            </div>

            {error && <div className="text-red-400 text-sm mb-4">{error}</div>}

            {!plan && !loading && !error && (
                <div className="bg-gray-900/50 rounded-lg p-8 text-center text-gray-500">
                    <p>No plan generated yet.</p>
                    <p className="text-sm mt-2">Click "Refresh Plan" to consult your AI Coach.</p>
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
                            if (typeof val === 'number') return val;
                            if (Array.isArray(val)) return val.join(', ');
                            if (val && typeof val === 'object') return JSON.stringify(val); // Fallback for objects
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
                            <div key={idx} className="bg-gray-700/30 rounded-lg p-4 border border-gray-700 flex flex-col md:flex-row gap-4">
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
                            </div>
                        );
                    })}
                </div>
            )
            }
        </div >
    );
}
