import { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import api from '../api/client';

export default function Settings() {
    const [profile, setProfile] = useState({
        age: '',
        gender: '',
        heightFt: '',
        heightIn: '',
        weight: '',
        openai_model: 'gpt-4o',
        units: 'imperial', // Default to imperial
        settings: {}
    });

    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [message, setMessage] = useState('');

    // OAuth statuses
    const [authStatus, setAuthStatus] = useState({
        strava: false,
        whoop: false
    });

    const location = useLocation();
    const navigate = useNavigate();

    useEffect(() => {
        // Check for redirect params
        const params = new URLSearchParams(location.search);
        const status = params.get('status');
        const service = params.get('service');
        const msg = params.get('msg');

        if (status === 'success') {
            setMessage(`Successfully connected to ${service === 'whoop' ? 'WHOOP' : 'Strava'}!`);
            // Clear params
            navigate('/settings', { replace: true });
        } else if (status === 'error') {
            setMessage(`Failed to connect ${service || ''}: ${msg || 'Unknown error'}`);
        }

        // Fetch user settings
        fetchSettings();
    }, [location.search]);

    const fetchSettings = () => {
        api.get('/auth/user')
            .then(res => {
                const user = res.data;
                const settings = user.settings || {};

                // Convert DB metric to UI imperial
                let heightFt = '';
                let heightIn = '';
                if (user.height) { // cm
                    const totalInches = user.height / 2.54;
                    heightFt = Math.floor(totalInches / 12);
                    heightIn = Math.round(totalInches % 12);
                }

                let weightLbs = '';
                if (user.weight) { // kg
                    weightLbs = Math.round(user.weight * 2.20462);
                }

                setProfile({
                    age: user.age || '',
                    gender: user.gender || '',
                    heightFt: heightFt,
                    heightIn: heightIn,
                    weight: weightLbs,
                    openai_model: user.openai_model || 'gpt-4o',
                    units: settings.units || 'imperial',
                    settings: settings
                });
                setAuthStatus({
                    strava: !!user.strava_access_token,
                    whoop: !!user.whoop_access_token
                });
            })
            .catch(err => console.error("Failed to load settings:", err))
            .finally(() => setLoading(false));
    };

    const handleChange = (e) => {
        const { name, value } = e.target;
        setProfile(prev => ({ ...prev, [name]: value }));
    };

    const handleSave = (e) => {
        e.preventDefault();
        setSaving(true);
        setMessage('');

        // Convert UI imperial back to DB metric
        let heightCm = null;
        if (profile.heightFt || profile.heightIn) {
            const ft = parseInt(profile.heightFt || 0);
            const inch = parseInt(profile.heightIn || 0);
            heightCm = Math.round(((ft * 12) + inch) * 2.54);
        }

        let weightKg = null;
        if (profile.weight) {
            weightKg = Math.round(parseInt(profile.weight) / 2.20462);
        }

        const payload = {
            ...profile,
            age: profile.age ? parseInt(profile.age) : null,
            height: heightCm,
            weight: weightKg,
            settings: {
                ...profile.settings,
                units: profile.units
            }
        };

        api.put('/auth/user/settings', payload)
            .then(res => {
                setMessage('Settings saved successfully!');
                setTimeout(() => setMessage(''), 3000);
            })
            .catch(err => setMessage('Failed to save settings.'))
            .finally(() => setSaving(false));
    };

    if (loading) return <div className="text-gray-400">Loading settings...</div>;

    return (
        <div className="max-w-4xl mx-auto space-y-8">
            <header>
                <h2 className="text-3xl font-bold mb-1">Settings</h2>
                <p className="text-gray-400">Customize your trainer and profile</p>
            </header>

            {/* User Profile */}
            <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
                <h3 className="text-xl font-semibold mb-4 text-blue-400">Profile</h3>
                <form onSubmit={handleSave} className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm text-gray-400 mb-1">Age</label>
                            <input
                                type="number"
                                name="age"
                                value={profile.age}
                                onChange={handleChange}
                                className="w-full bg-gray-700 border border-gray-600 rounded p-2 text-white"
                                placeholder="e.g. 30"
                            />
                        </div>
                        <div>
                            <label className="block text-sm text-gray-400 mb-1">Gender</label>
                            <select
                                name="gender"
                                value={profile.gender}
                                onChange={handleChange}
                                className="w-full bg-gray-700 border border-gray-600 rounded p-2 text-white"
                            >
                                <option value="">Select...</option>
                                <option value="Male">Male</option>
                                <option value="Female">Female</option>
                                <option value="Other">Other</option>
                            </select>
                        </div>
                        <div className="md:col-span-1">
                            <label className="block text-sm text-gray-400 mb-1">Height</label>
                            <div className="flex gap-2">
                                <div className="relative w-1/2">
                                    <input
                                        type="number"
                                        name="heightFt"
                                        value={profile.heightFt}
                                        onChange={handleChange}
                                        className="w-full bg-gray-700 border border-gray-600 rounded p-2 text-white pr-8"
                                        placeholder="Ft"
                                    />
                                    <span className="absolute right-3 top-2 text-gray-500 text-sm">ft</span>
                                </div>
                                <div className="relative w-1/2">
                                    <input
                                        type="number"
                                        name="heightIn"
                                        value={profile.heightIn}
                                        onChange={handleChange}
                                        className="w-full bg-gray-700 border border-gray-600 rounded p-2 text-white pr-8"
                                        placeholder="In"
                                    />
                                    <span className="absolute right-3 top-2 text-gray-500 text-sm">in</span>
                                </div>
                            </div>
                        </div>
                        <div>
                            <label className="block text-sm text-gray-400 mb-1">Weight</label>
                            <div className="relative">
                                <input
                                    type="number"
                                    name="weight"
                                    value={profile.weight}
                                    onChange={handleChange}
                                    className="w-full bg-gray-700 border border-gray-600 rounded p-2 text-white pr-10"
                                    placeholder="e.g. 180"
                                />
                                <span className="absolute right-3 top-2 text-gray-500 text-sm">lbs</span>
                            </div>
                        </div>
                    </div>

                    <div className="pt-4 border-t border-gray-700">
                        <label className="block text-sm text-gray-400 mb-1">AI Model</label>
                        <select
                            name="openai_model"
                            value={profile.openai_model}
                            onChange={handleChange}
                            className="w-full bg-gray-700 border border-gray-600 rounded p-2 text-white"
                        >
                            <option value="gpt-4o">GPT-4o (Recommended)</option>
                            <option value="gpt-4-turbo">GPT-4 Turbo</option>
                            <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                        </select>
                        <p className="text-xs text-gray-500 mt-1">Controls the intelligence level of your coach.</p>
                    </div>

                    <div className="flex items-center gap-4 mt-6">
                        <button
                            type="submit"
                            disabled={saving}
                            className="px-6 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded font-medium disabled:opacity-50 transition"
                        >
                            {saving ? 'Saving...' : 'Save Profile'}
                        </button>
                        {message && <span className={message.includes('Failed') ? "text-red-400" : "text-green-400"}>{message}</span>}
                    </div>
                </form>
            </div>

            {/* Integrations */}
            <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
                <h3 className="text-xl font-semibold mb-4 text-purple-400">Integrations</h3>
                <div className="space-y-4">
                    {/* Strava */}
                    <div className="flex justify-between items-center p-4 bg-gray-700/30 rounded-lg border border-gray-600">
                        <div className="flex items-center gap-3">
                            {/* Strava Icon placeholder */}
                            <span className="text-2xl">🏃</span>
                            <div>
                                <h4 className="font-bold text-white">Strava</h4>
                                <p className="text-xs text-gray-400">{authStatus.strava ? 'Connected' : 'Not Connected'}</p>
                            </div>
                        </div>
                        {authStatus.strava ? (
                            <button disabled className="bg-green-900/40 text-green-400 border border-green-800 px-3 py-1 rounded text-sm font-medium cursor-default">
                                Connected
                            </button>
                        ) : (
                            <a href="http://localhost:8000/auth/strava/login" className="text-sm bg-orange-600 hover:bg-orange-500 text-white px-3 py-1 rounded transition">Connect</a>
                        )}
                    </div>

                    {/* Whoop */}
                    <div className="flex justify-between items-center p-4 bg-gray-700/30 rounded-lg border border-gray-600">
                        <div className="flex items-center gap-3">
                            {/* Whoop Icon placeholder */}
                            <span className="text-2xl">⌚</span>
                            <div>
                                <h4 className="font-bold text-white">WHOOP</h4>
                                <p className="text-xs text-gray-400">{authStatus.whoop ? 'Connected' : 'Not Connected'}</p>
                            </div>
                        </div>
                        {authStatus.whoop ? (
                            <button disabled className="bg-green-900/40 text-green-400 border border-green-800 px-3 py-1 rounded text-sm font-medium cursor-default">
                                Connected
                            </button>
                        ) : (
                            <a href="http://localhost:8000/auth/whoop/login" className="text-sm bg-black hover:bg-gray-900 border border-gray-600 text-white px-3 py-1 rounded transition">Connect</a>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
