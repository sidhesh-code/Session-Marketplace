import React, { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { getPublicSessionDetail, updateCreatorSession } from '../api/sessions';
import { ArrowLeft, Edit3, AlertCircle } from 'lucide-react';

export const EditSessionPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [title, setTitle] = useState<string>('');
  const [description, setDescription] = useState<string>('');
  const [startTime, setStartTime] = useState<string>('');
  const [duration, setDuration] = useState<number>(60);
  const [capacity, setCapacity] = useState<number>(10);

  const [loading, setLoading] = useState<boolean>(true);
  const [saving, setSaving] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    getPublicSessionDetail(Number(id))
      .then((data) => {
        setTitle(data.title);
        setDescription(data.description);
        // Format ISO datetime string for datetime-local input
        const dt = new Date(data.start_time);
        const formatted = new Date(dt.getTime() - dt.getTimezoneOffset() * 60000)
          .toISOString()
          .slice(0, 16);
        setStartTime(formatted);
        setDuration(data.duration);
        setCapacity(data.capacity);
      })
      .catch(() => setErrorMsg('Failed to load session details.'))
      .finally(() => setLoading(false));
  }, [id]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!id) return;

    if (capacity <= 0) {
      setErrorMsg('Capacity must be greater than zero.');
      return;
    }

    try {
      setSaving(true);
      setErrorMsg(null);

      const formattedStartTime = new Date(startTime).toISOString();
      await updateCreatorSession(Number(id), {
        title,
        description,
        start_time: formattedStartTime,
        duration: Number(duration),
        capacity: Number(capacity),
      });

      navigate('/creator');
    } catch (err: any) {
      if (err.response?.status === 403) {
        setErrorMsg('You are not authorized to edit another creator\'s session (403 Forbidden).');
      } else {
        setErrorMsg(err.response?.data?.detail || 'Failed to update session.');
      }
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-sky-500"></div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-8 space-y-6">
      <Link to="/creator" className="inline-flex items-center space-x-1.5 text-sm text-slate-400 hover:text-white transition">
        <ArrowLeft className="w-4 h-4" />
        <span>Back to Dashboard</span>
      </Link>

      <div className="bg-slate-800/90 border border-slate-700/80 rounded-2xl p-6 sm:p-8 space-y-6 shadow-xl">
        <div className="border-b border-slate-700/60 pb-4">
          <h1 className="text-2xl font-bold text-white flex items-center space-x-2">
            <Edit3 className="w-6 h-6 text-sky-400" />
            <span>Edit Session #{id}</span>
          </h1>
          <p className="text-sm text-slate-400 mt-1">Update session details, capacity, or schedule</p>
        </div>

        {errorMsg && (
          <div className="bg-rose-950/80 border border-rose-800 text-rose-300 p-3.5 rounded-xl flex items-center space-x-2 text-sm">
            <AlertCircle className="w-5 h-5 text-rose-400 flex-shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
              Session Title
            </label>
            <input
              type="text"
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-sky-500 transition"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
              Description
            </label>
            <textarea
              required
              rows={4}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-sky-500 transition"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                Start Date & Time
              </label>
              <input
                type="datetime-local"
                required
                value={startTime}
                onChange={(e) => setStartTime(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2.5 text-xs sm:text-sm text-white focus:outline-none focus:border-sky-500 transition"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                Duration (Minutes)
              </label>
              <input
                type="number"
                min="1"
                required
                value={duration}
                onChange={(e) => setDuration(Number(e.target.value))}
                className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-sky-500 transition"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                Capacity (Seats)
              </label>
              <input
                type="number"
                min="1"
                required
                value={capacity}
                onChange={(e) => setCapacity(Number(e.target.value))}
                className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-sky-500 transition"
              />
            </div>
          </div>

          <div className="pt-4 flex space-x-3">
            <button
              type="submit"
              disabled={saving}
              className="flex-1 bg-sky-600 hover:bg-sky-500 text-white font-bold py-3 px-4 rounded-xl text-sm transition shadow-lg disabled:opacity-50 flex items-center justify-center space-x-2"
            >
              {saving ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-t-2 border-b-2 border-white"></div>
                  <span>Saving Changes...</span>
                </>
              ) : (
                <span>Save Changes</span>
              )}
            </button>
            <Link
              to="/creator"
              className="bg-slate-700 hover:bg-slate-600 text-white font-semibold py-3 px-5 rounded-xl text-sm transition flex items-center justify-center"
            >
              Cancel
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
};
