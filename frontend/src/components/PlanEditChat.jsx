/**
 * PlanEditChat — Modal for editing a day's plan via conversation with the AI coach.
 *
 * Props:
 *   dayLabel: "today" | "tomorrow"
 *   dayPlan: the current plan object for that day
 *   onClose: called when modal is dismissed
 *   onPlanUpdated: called with the revised plan object after a successful edit
 */
import { useState, useRef, useEffect } from 'react';
import api from '../api/client';

export default function PlanEditChat({ dayLabel, dayPlan, onClose, onPlanUpdated }) {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const chatEndRef = useRef(null);

    useEffect(() => {
        chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const handleSend = () => {
        const text = input.trim();
        if (!text || loading) return;

        const userMsg = { role: 'user', content: text };
        const updatedMessages = [...messages, userMsg];
        setMessages(updatedMessages);
        setInput('');
        setLoading(true);

        api.post('/coach/edit-plan', {
            day: dayLabel,
            messages: updatedMessages
        })
            .then(res => {
                const assistantMsg = { role: 'assistant', content: res.data.reply };
                setMessages(prev => [...prev, assistantMsg]);
                if (res.data.plan) {
                    onPlanUpdated(res.data.plan);
                }
            })
            .catch(err => {
                console.error(err);
                setMessages(prev => [...prev, {
                    role: 'assistant',
                    content: 'Sorry, something went wrong. Please try again.'
                }]);
            })
            .finally(() => setLoading(false));
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    const blockType = dayPlan?.block_type || 'Plan';
    const dayTitle = dayLabel === 'today' ? 'TODAY' : 'TOMORROW';

    return (
        <div className="fixed inset-0 bg-black/60 flex items-end sm:items-center justify-center z-50">
            <div className="bg-white dark:bg-gray-800 sm:rounded-xl border-t sm:border border-gray-200 dark:border-gray-700 w-full sm:max-w-lg shadow-2xl flex flex-col h-[85vh] sm:h-auto" style={{ maxHeight: '85vh' }}>
                {/* Header */}
                <div className="flex items-center justify-between px-5 py-4 border-b border-gray-200 dark:border-gray-700">
                    <div>
                        <h3 className="text-lg font-bold text-gray-900 dark:text-white">Edit {dayTitle}'s Plan</h3>
                        <p className="text-xs text-gray-500 dark:text-gray-400">{blockType} — Chat with your coach to adjust</p>
                    </div>
                    <button
                        onClick={onClose}
                        className="text-gray-400 hover:text-gray-900 dark:hover:text-white transition p-1"
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                </div>

                {/* Chat messages */}
                <div className="flex-1 overflow-y-auto px-5 py-4 space-y-3">
                    {messages.length === 0 && (
                        <div className="text-center text-gray-500 text-sm py-8">
                            <p>Tell your coach what you'd like to change.</p>
                            <p className="text-xs text-gray-600 mt-2">e.g. "Make it 30 min shorter" or "I tweaked my ankle, go easy"</p>
                        </div>
                    )}
                    {messages.map((msg, i) => (
                        <div
                            key={i}
                            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                        >
                            <div
                                className={`max-w-[80%] rounded-xl px-4 py-2.5 text-sm leading-relaxed ${msg.role === 'user'
                                    ? 'bg-blue-600 text-white rounded-br-sm'
                                    : 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200 rounded-bl-sm'
                                    }`}
                            >
                                {msg.content}
                            </div>
                        </div>
                    ))}
                    {loading && (
                        <div className="flex justify-start">
                            <div className="bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400 rounded-xl px-4 py-2.5 text-sm rounded-bl-sm">
                                <span className="animate-pulse">Thinking...</span>
                            </div>
                        </div>
                    )}
                    <div ref={chatEndRef} />
                </div>

                {/* Input */}
                <div className="px-5 py-3 border-t border-gray-200 dark:border-gray-700">
                    <div className="flex gap-2">
                        <input
                            type="text"
                            value={input}
                            onChange={e => setInput(e.target.value)}
                            onKeyDown={handleKeyDown}
                            placeholder="Tell the coach what to change..."
                            className="flex-1 bg-gray-50 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg px-4 py-2.5 text-sm text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:border-blue-500 focus:outline-none transition"
                            disabled={loading}
                            autoFocus
                        />
                        <button
                            onClick={handleSend}
                            disabled={loading || !input.trim()}
                            className="bg-blue-600 hover:bg-blue-500 disabled:opacity-40 text-white px-4 py-2.5 rounded-lg text-sm font-medium transition"
                        >
                            Send
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
