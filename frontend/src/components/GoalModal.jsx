import { useState, useEffect } from 'react';

// Helper: detect if a description is a routine format ("Title:\n- item\n- item")
function parseRoutine(desc) {
    if (!desc) return null;
    const lines = desc.split('\n').filter(l => l.trim());
    if (lines.length < 2) return null;
    // First line should end with ":"
    const titleLine = lines[0].trim();
    if (!titleLine.endsWith(':')) return null;
    // Remaining lines should start with "- "
    const items = [];
    for (let i = 1; i < lines.length; i++) {
        const l = lines[i].trim();
        if (l.startsWith('- ')) {
            items.push(l.slice(2));
        } else {
            return null; // Not a routine format
        }
    }
    if (items.length === 0) return null;
    return { name: titleLine.slice(0, -1), exercises: items };
}

function serializeRoutine(name, exercises) {
    const items = exercises.filter(e => e.trim());
    if (!name.trim() || items.length === 0) return name.trim();
    return `${name.trim()}:\n${items.map(e => `- ${e.trim()}`).join('\n')}`;
}

export default function GoalModal({ goal, onClose, onSave, onDelete }) {
    const [description, setDescription] = useState(goal?.description || '');
    const [isEvent, setIsEvent] = useState(!!goal?.target_date || false);
    const [type, setType] = useState(goal?.type || 'short_term');
    const [targetDate, setTargetDate] = useState(goal?.target_date ? goal.target_date.split('T')[0] : '');
    const [isCompleted, setIsCompleted] = useState(goal?.is_completed || false);

    // Routine state
    const [isRoutine, setIsRoutine] = useState(false);
    const [routineName, setRoutineName] = useState('');
    const [exercises, setExercises] = useState(['']);

    // On mount, detect if existing goal is a routine
    useEffect(() => {
        if (goal?.description && (goal?.type === 'preference' || goal?.type === 'routine')) {
            const parsed = parseRoutine(goal.description);
            if (parsed) {
                setIsRoutine(true);
                setRoutineName(parsed.name);
                setExercises([...parsed.exercises, '']); // empty slot at end
                setType('preference');
            }
        }
    }, [goal]);

    const handleSubmit = (e) => {
        e.preventDefault();
        let finalDescription = description;

        if (!isEvent && isRoutine) {
            finalDescription = serializeRoutine(routineName, exercises);
        }

        const payload = {
            description: finalDescription,
            type: isEvent ? 'event' : type,
            target_date: isEvent && targetDate ? new Date(targetDate).toISOString() : null,
            is_completed: isCompleted,
            status: isCompleted ? 'completed' : 'active'
        };
        onSave(payload);
    };

    const addExercise = () => setExercises(prev => [...prev, '']);

    const updateExercise = (idx, value) => {
        setExercises(prev => prev.map((e, i) => i === idx ? value : e));
    };

    const removeExercise = (idx) => {
        setExercises(prev => prev.filter((_, i) => i !== idx));
    };

    const moveExercise = (idx, dir) => {
        const newIdx = idx + dir;
        if (newIdx < 0 || newIdx >= exercises.length) return;
        setExercises(prev => {
            const arr = [...prev];
            [arr[idx], arr[newIdx]] = [arr[newIdx], arr[idx]];
            return arr;
        });
    };

    // When switching category to/from routine
    const handleCategoryChange = (value) => {
        if (value === 'routine') {
            setIsRoutine(true);
            setType('preference');
        } else {
            setIsRoutine(false);
            setType(value);
        }
    };

    const categoryValue = isRoutine ? 'routine' : type;

    return (
        <div className="fixed inset-0 bg-black/50 flex items-end sm:items-center justify-center z-50">
            <div className="bg-white dark:bg-gray-800 p-5 sm:p-6 rounded-t-xl sm:rounded-xl border-t sm:border border-gray-200 dark:border-gray-700 w-full sm:max-w-md shadow-2xl max-h-[90vh] overflow-y-auto">
                <h3 className="text-xl font-bold mb-4 text-gray-900 dark:text-white">{goal ? 'Edit Goal' : 'New Goal'}</h3>

                <form onSubmit={handleSubmit} className="space-y-4">
                    {/* Event checkbox */}
                    <div className="flex items-center gap-4">
                        <label className="flex items-center gap-2 cursor-pointer">
                            <input
                                type="checkbox"
                                checked={isEvent}
                                onChange={e => { setIsEvent(e.target.checked); if (e.target.checked) setIsRoutine(false); }}
                                className="rounded bg-gray-100 dark:bg-gray-700 border-gray-300 dark:border-gray-600"
                            />
                            <span className="text-sm text-gray-600 dark:text-gray-300">Is this an Event/Deadline?</span>
                        </label>
                    </div>

                    {/* Event date */}
                    {isEvent && (
                        <div>
                            <label className="block text-sm text-gray-500 dark:text-gray-400 mb-1">Target Date</label>
                            <input
                                type="date"
                                value={targetDate}
                                onChange={e => setTargetDate(e.target.value)}
                                className="w-full bg-gray-50 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded p-2 text-gray-900 dark:text-white"
                                required={isEvent}
                            />
                        </div>
                    )}

                    {/* Category (only for non-events) */}
                    {!isEvent && (
                        <div>
                            <label className="block text-sm text-gray-500 dark:text-gray-400 mb-1">Category</label>
                            <select
                                value={categoryValue}
                                onChange={e => handleCategoryChange(e.target.value)}
                                className="w-full bg-gray-50 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded p-2 text-gray-900 dark:text-white"
                            >
                                <option value="short_term">Short Term Goal</option>
                                <option value="long_term">Long Term Goal</option>
                                <option value="preference">Preference / Habit</option>
                                <option value="routine">Workout Routine</option>
                                <option value="other">Other</option>
                            </select>
                        </div>
                    )}

                    {/* --- Routine Editor --- */}
                    {!isEvent && isRoutine ? (
                        <div className="space-y-3">
                            <div>
                                <label className="block text-sm text-gray-500 dark:text-gray-400 mb-1">Routine Name</label>
                                <input
                                    type="text"
                                    value={routineName}
                                    onChange={e => setRoutineName(e.target.value)}
                                    className="w-full bg-gray-50 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded p-2 text-gray-900 dark:text-white"
                                    placeholder="e.g. My yoga routine"
                                    required
                                />
                            </div>

                            <div>
                                <label className="block text-sm text-gray-500 dark:text-gray-400 mb-1">Exercises</label>
                                <div className="space-y-2">
                                    {exercises.map((ex, idx) => (
                                        <div key={idx} className="flex items-center gap-1.5">
                                            <span className="text-xs text-gray-400 dark:text-gray-500 w-5 text-right shrink-0">{idx + 1}.</span>
                                            <input
                                                type="text"
                                                value={ex}
                                                onChange={e => updateExercise(idx, e.target.value)}
                                                className="flex-1 bg-gray-50 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded px-2 py-1.5 text-sm text-gray-900 dark:text-white"
                                                placeholder="Exercise name"
                                            />
                                            {/* Move up */}
                                            <button
                                                type="button"
                                                onClick={() => moveExercise(idx, -1)}
                                                disabled={idx === 0}
                                                className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 disabled:opacity-30 transition"
                                                title="Move up"
                                            >
                                                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" /></svg>
                                            </button>
                                            {/* Move down */}
                                            <button
                                                type="button"
                                                onClick={() => moveExercise(idx, 1)}
                                                disabled={idx === exercises.length - 1}
                                                className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 disabled:opacity-30 transition"
                                                title="Move down"
                                            >
                                                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
                                            </button>
                                            {/* Remove */}
                                            {exercises.length > 1 && (
                                                <button
                                                    type="button"
                                                    onClick={() => removeExercise(idx)}
                                                    className="p-1 text-red-400 hover:text-red-300 transition"
                                                    title="Remove"
                                                >
                                                    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                                                </button>
                                            )}
                                        </div>
                                    ))}
                                </div>
                                <button
                                    type="button"
                                    onClick={addExercise}
                                    className="mt-2 text-sm text-blue-500 hover:text-blue-400 transition flex items-center gap-1"
                                >
                                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" /></svg>
                                    Add exercise
                                </button>
                            </div>
                        </div>
                    ) : (
                        /* --- Plain Description Textarea --- */
                        <div>
                            <label className="block text-sm text-gray-500 dark:text-gray-400 mb-1">Description</label>
                            <textarea
                                value={description}
                                onChange={e => setDescription(e.target.value)}
                                className="w-full max-h-36 min-h-12 bg-gray-50 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded p-2 text-gray-900 dark:text-white break-words"
                                placeholder="e.g. Run a marathon, Prefer morning workouts..."
                                required
                            />
                        </div>
                    )}

                    {/* Mark completed (edit only) */}
                    {goal && (
                        <div className="flex items-center gap-4 pt-2 border-t border-gray-200 dark:border-gray-700">
                            <label className="flex items-center gap-2 cursor-pointer">
                                <input
                                    type="checkbox"
                                    checked={isCompleted}
                                    onChange={e => setIsCompleted(e.target.checked)}
                                    className="rounded bg-gray-100 dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-green-500 focus:ring-green-500"
                                />
                                <span className={`text-sm ${isCompleted ? 'text-green-500 dark:text-green-400 font-medium' : 'text-gray-500 dark:text-gray-400'}`}>
                                    {isCompleted ? 'Completed' : 'Mark as Completed'}
                                </span>
                            </label>
                        </div>
                    )}

                    {/* Footer */}
                    <div className="flex justify-between mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
                        {goal && onDelete && (
                            <button
                                type="button"
                                onClick={onDelete}
                                className="text-red-400 hover:text-red-300 text-sm transition"
                            >
                                Delete
                            </button>
                        )}
                        <div className="flex gap-3 ml-auto">
                            <button
                                type="button"
                                onClick={onClose}
                                className="px-4 py-2 text-gray-500 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white transition"
                            >
                                Cancel
                            </button>
                            <button
                                type="submit"
                                className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded transition"
                            >
                                Save
                            </button>
                        </div>
                    </div>
                </form>
            </div >
        </div >
    );
}
