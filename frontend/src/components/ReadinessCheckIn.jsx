import { useState } from 'react';
import api from '../api/client';

const MOODS = [
    { emoji: '😤', label: 'Rough', value: 'bad' },
    { emoji: '😕', label: 'Low', value: 'low' },
    { emoji: '😐', label: 'Okay', value: 'okay' },
    { emoji: '🙂', label: 'Good', value: 'good' },
    { emoji: '💪', label: 'Great', value: 'great' },
];

export default function ReadinessCheckIn({ onComplete, onSkip }) {
    const [energy, setEnergy] = useState(5);
    const [soreness, setSoreness] = useState('');
    const [mood, setMood] = useState(null);
    const [submitting, setSubmitting] = useState(false);

    const handleSubmit = async () => {
        setSubmitting(true);
        try {
            await api.post('/data/readiness', {
                energy_level: energy,
                soreness_notes: soreness || null,
                mood: mood,
            });
            onComplete();
        } catch (err) {
            console.error('Failed to save readiness check-in:', err);
            // Still proceed even if save fails
            onComplete();
        }
    };

    const getEnergyLabel = (val) => {
        if (val <= 2) return '🔋 Very Low';
        if (val <= 4) return '🪫 Low';
        if (val <= 6) return '⚡ Moderate';
        if (val <= 8) return '🔥 High';
        return '⚡🔥 Peak';
    };

    const getEnergyColor = (val) => {
        if (val <= 2) return 'from-red-500 to-red-600';
        if (val <= 4) return 'from-orange-400 to-orange-500';
        if (val <= 6) return 'from-yellow-400 to-yellow-500';
        if (val <= 8) return 'from-green-400 to-green-500';
        return 'from-emerald-400 to-emerald-500';
    };

    return (
        <div className="bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-gray-800 dark:to-gray-800 rounded-xl p-5 border border-blue-200 dark:border-blue-800/50 shadow-lg">
            <div className="flex items-center gap-2 mb-4">
                <span className="text-2xl">🧠</span>
                <div>
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white">How are you feeling today?</h3>
                    <p className="text-xs text-gray-500 dark:text-gray-400">Your coach uses this to personalize today's plan</p>
                </div>
            </div>

            {/* Energy Level */}
            <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Energy Level
                </label>
                <div className="flex items-center gap-3">
                    <input
                        type="range"
                        min="1"
                        max="10"
                        value={energy}
                        onChange={(e) => setEnergy(parseInt(e.target.value))}
                        className="flex-1 h-2 rounded-lg appearance-none cursor-pointer accent-blue-600"
                    />
                    <span className={`text-sm font-semibold px-2.5 py-1 rounded-full bg-gradient-to-r ${getEnergyColor(energy)} text-white min-w-[100px] text-center`}>
                        {getEnergyLabel(energy)}
                    </span>
                </div>
                <div className="flex justify-between text-xs text-gray-400 dark:text-gray-500 mt-1 px-0.5">
                    <span>1</span>
                    <span>5</span>
                    <span>10</span>
                </div>
            </div>

            {/* Mood */}
            <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Mood
                </label>
                <div className="flex gap-2">
                    {MOODS.map((m) => (
                        <button
                            key={m.value}
                            onClick={() => setMood(m.value)}
                            className={`flex-1 flex flex-col items-center gap-1 py-2 px-1 rounded-lg border-2 transition-all duration-150 ${mood === m.value
                                    ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/30 shadow-md scale-105'
                                    : 'border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500 hover:bg-gray-50 dark:hover:bg-gray-700/50'
                                }`}
                        >
                            <span className="text-xl">{m.emoji}</span>
                            <span className="text-[10px] text-gray-500 dark:text-gray-400">{m.label}</span>
                        </button>
                    ))}
                </div>
            </div>

            {/* Soreness */}
            <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Anything sore or bothering you? <span className="text-gray-400 font-normal">(optional)</span>
                </label>
                <input
                    type="text"
                    value={soreness}
                    onChange={(e) => setSoreness(e.target.value)}
                    placeholder="e.g., Left knee tight, lower back stiff..."
                    className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition"
                />
            </div>

            {/* Actions */}
            <div className="flex items-center justify-between">
                <button
                    onClick={onSkip}
                    className="text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 transition"
                >
                    Skip for today →
                </button>
                <button
                    onClick={handleSubmit}
                    disabled={submitting}
                    className="bg-blue-600 hover:bg-blue-500 text-white px-5 py-2 rounded-lg text-sm font-medium transition disabled:opacity-50 shadow-md hover:shadow-lg"
                >
                    {submitting ? 'Saving...' : 'Submit & Generate Plan'}
                </button>
            </div>
        </div>
    );
}
