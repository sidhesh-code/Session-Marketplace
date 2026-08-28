import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { updateProfile } from '../api/profile';
import { User, CheckCircle2, AlertCircle, Camera } from 'lucide-react';

export const ProfilePage: React.FC = () => {
  const { user, updateLocalUser } = useAuth();

  const [name, setName] = useState<string>(user?.name || '');
  const [profileImage, setProfileImage] = useState<string>(user?.profile_image || '');
  const [loading, setLoading] = useState<boolean>(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      setSuccessMsg(null);
      setErrorMsg(null);
      
      const updated = await updateProfile({ name, profile_image: profileImage });
      updateLocalUser(updated);
      setSuccessMsg('Profile updated successfully!');
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to update profile.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <div className="bg-slate-800/90 border border-slate-700/80 rounded-2xl p-6 sm:p-8 space-y-6 shadow-xl">
        <div className="flex items-center space-x-4 border-b border-slate-700/60 pb-6">
          <div className="relative">
            {profileImage ? (
              <img src={profileImage} alt={name} className="w-16 h-16 rounded-full object-cover border-2 border-sky-500" />
            ) : (
              <div className="w-16 h-16 rounded-full bg-slate-900 flex items-center justify-center text-sky-400 font-bold text-xl border-2 border-sky-500">
                {name.charAt(0).toUpperCase()}
              </div>
            )}
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">{user?.name}</h1>
            <p className="text-sm text-slate-400">{user?.email}</p>
            <span className="inline-block mt-1 text-xs px-2.5 py-0.5 rounded bg-slate-700 text-sky-300 font-semibold">
              Role: {user?.role}
            </span>
          </div>
        </div>

        {successMsg && (
          <div className="bg-emerald-950/80 border border-emerald-800 text-emerald-300 p-3.5 rounded-xl flex items-center space-x-2 text-sm">
            <CheckCircle2 className="w-5 h-5 text-emerald-400 flex-shrink-0" />
            <span>{successMsg}</span>
          </div>
        )}

        {errorMsg && (
          <div className="bg-rose-950/80 border border-rose-800 text-rose-300 p-3.5 rounded-xl flex items-center space-x-2 text-sm">
            <AlertCircle className="w-5 h-5 text-rose-400 flex-shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
              Full Name
            </label>
            <input
              type="text"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-sky-500 transition"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
              Profile Image URL (Optional)
            </label>
            <input
              type="url"
              placeholder="https://example.com/avatar.jpg"
              value={profileImage}
              onChange={(e) => setProfileImage(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-sky-500 transition"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
              Email Address (Read-only)
            </label>
            <input
              type="email"
              disabled
              value={user?.email || ''}
              className="w-full bg-slate-950/60 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-slate-500 cursor-not-allowed"
            />
          </div>

          <div className="pt-4">
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-sky-600 hover:bg-sky-500 text-white font-bold py-3 px-4 rounded-xl text-sm transition shadow-lg disabled:opacity-50 flex items-center justify-center space-x-2"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-t-2 border-b-2 border-white"></div>
                  <span>Saving...</span>
                </>
              ) : (
                <span>Update Profile</span>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
