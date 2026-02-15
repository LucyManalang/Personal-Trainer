import { useState, useEffect } from 'react';

export default function GoalModal({ goal, onClose, onSave, onDelete }) {
    const [description, setDescription] = useState(goal?.description || '');
    const [isEvent, setIsEvent] = useState(!!goal?.target_date || false);
    const [type, setType] = useState(goal?.type || 'short_term'); // default
    const [targetDate, setTargetDate] = useState(goal?.target_date ? goal.target_date.split('T')[0] : '');
    const [isCompleted, setIsCompleted] = useState(goal?.is_completed || false);

    const handleSubmit = (e) => {
        e.preventDefault();
        const payload = {
            description,
            type: isEvent ? 'event' : type, // or keep original type logic? User said "dated goals will be like events".
            // Let's rely on target_date presence or explicit type.
            // If we use 'type' field freely, we can use 'Event', 'Preference', 'Short Term' etc.
            // If isEvent is true, force type 'Event' or similar?
            // Or just save Date.
            target_date: isEvent && targetDate ? new Date(targetDate).toISOString() : null,
            is_completed: isCompleted,
            status: isCompleted ? 'completed' : 'active'
        };
        onSave(payload);
    };

    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-gray-800 p-6 rounded-xl border border-gray-700 w-full max-w-md shadow-2xl">
                <h3 className="text-xl font-bold mb-4 text-white">{goal ? 'Edit Goal' : 'New Goal'}</h3>

                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label className="block text-sm text-gray-400 mb-1">Description</label>
                        <textarea
                            value={description}
                            onChange={e => setDescription(e.target.value)}
                            className="w-full max-h-36 min-h-12 bg-gray-700 border border-gray-600 rounded p-2 text-white break-words"
                            placeholder="e.g. Run a marathon, Prefer morning workouts..."
                            required
                        />
                    </div>

                    <div className="flex items-center gap-4">
                        <label className="flex items-center gap-2 cursor-pointer">
                            <input
                                type="checkbox"
                                checked={isEvent}
                                onChange={e => setIsEvent(e.target.checked)}
                                className="rounded bg-gray-700 border-gray-600"
                            />
                            <span className="text-sm text-gray-300">Is this an Event/Deadline?</span>
                        </label>
                    </div>

                    {isEvent && (
                        <div>
                            <label className="block text-sm text-gray-400 mb-1">Target Date</label>
                            <input
                                type="date"
                                value={targetDate}
                                onChange={e => setTargetDate(e.target.value)}
                                className="w-full bg-gray-700 border border-gray-600 rounded p-2 text-white"
                                required={isEvent}
                            />
                        </div>
                    )}

                    {!isEvent && (
                        <div>
                            <label className="block text-sm text-gray-400 mb-1">Category</label>
                            <select
                                value={type}
                                onChange={e => setType(e.target.value)}
                                className="w-full bg-gray-700 border border-gray-600 rounded p-2 text-white"
                            >
                                <option value="short_term">Short Term Goal</option>
                                <option value="long_term">Long Term Goal</option>
                                <option value="preference">Preference / Habit</option>
                                <option value="other">Other</option>
                            </select>
                        </div>
                    )}

                    {goal && (
                        <div className="flex items-center gap-4 pt-2 border-t border-gray-700">
                            <label className="flex items-center gap-2 cursor-pointer">
                                <input
                                    type="checkbox"
                                    checked={isCompleted}
                                    onChange={e => setIsCompleted(e.target.checked)}
                                    className="rounded bg-gray-700 border-gray-600 text-green-500 focus:ring-green-500"
                                />
                                <span className={`text-sm ${isCompleted ? 'text-green-400 font-medium' : 'text-gray-400'}`}>
                                    {isCompleted ? 'Completed' : 'Mark as Completed'}
                                </span>
                            </label>
                        </div>
                    )}

                    <div className="flex justify-between mt-6 pt-4 border-t border-gray-700">
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
                                className="px-4 py-2 text-gray-300 hover:text-white transition"
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
            </div>
        </div>
    );
}
