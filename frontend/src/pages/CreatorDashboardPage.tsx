import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Session } from '../types';
import { getCreatorSessions, deleteCreatorSession } from '../api/sessions';
import { PlusCircle, Edit3, Trash2, Calendar, Clock, Users, Video } from 'lucide-react';

export const CreatorDashboardPage: React.FC = () => {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<number | null>(null);

  const fetchSessions = async () => {
    try {
      setLoading(true);
      const data = await getCreatorSessions();
      setSessions(data);
    } catch (err: any) {
      setErrorMsg('Failed to load your creator sessions.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSessions();
  }, []);

  const handleDelete = async (id: number, title: string) => {
    if (!window.confirm(`Are you sure you want to delete session "${title}"? Active bookings will be removed.`)) {
      return;
    }

    try {
      setDeletingId(id);
      await deleteCreatorSession(id);
      await fetchSessions();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to delete session.');
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight">Creator Dashboard</h1>
          <p className="text-slate-400 text-sm mt-1">Manage your sessions, capacity, and active booking counts</p>
        </div>

        <Link
          to="/creator/sessions/new"
          className="inline-flex items-center space-x-2 bg-amber-600 hover:bg-amber-500 text-white font-bold px-4 py-2.5 rounded-xl text-sm transition shadow-lg shadow-amber-950"
        >
          <PlusCircle className="w-5 h-5" />
          <span>Create New Session</span>
        </Link>
      </div>

      {loading ? (
        <div className="flex items-center justify-center min-h-[40vh]">
          <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-amber-500"></div>
        </div>
      ) : errorMsg ? (
        <div className="bg-rose-950/80 border border-rose-800 text-rose-300 p-4 rounded-xl text-center text-sm">
          {errorMsg}
        </div>
      ) : sessions.length === 0 ? (
        <div className="text-center py-16 bg-slate-800/40 border border-slate-800 rounded-2xl p-8 space-y-3">
          <Video className="w-12 h-12 text-slate-500 mx-auto" />
          <h3 className="text-lg font-semibold text-white">You haven't created any sessions yet</h3>
          <p className="text-sm text-slate-400">Click below to publish your first session to the marketplace.</p>
          <Link
            to="/creator/sessions/new"
            className="inline-flex items-center space-x-2 bg-amber-600 hover:bg-amber-500 text-white font-bold px-5 py-2.5 rounded-xl text-sm transition mt-2"
          >
            <PlusCircle className="w-4 h-4" />
            <span>Create Session</span>
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {sessions.map((session) => {
            const startDate = new Date(session.start_time).toLocaleString('en-US', {
              dateStyle: 'medium',
              timeStyle: 'short',
            });

            return (
              <div
                key={session.id}
                className="bg-slate-800/90 border border-slate-700/80 rounded-xl p-5 flex flex-col justify-between space-y-4 shadow-lg"
              >
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-amber-400">Session #{session.id}</span>
                    <span className="text-xs px-2.5 py-0.5 rounded-full bg-slate-900 text-slate-300 font-medium">
                      {session.booked_seats} / {session.capacity} Booked
                    </span>
                  </div>

                  <h3 className="text-lg font-semibold text-white line-clamp-1">{session.title}</h3>
                  <p className="text-xs text-slate-400 line-clamp-2">{session.description}</p>

                  <div className="space-y-1.5 pt-2 text-xs text-slate-300">
                    <div className="flex items-center space-x-1.5">
                      <Calendar className="w-4 h-4 text-amber-400" />
                      <span>{startDate}</span>
                    </div>
                    <div className="flex items-center space-x-1.5">
                      <Clock className="w-4 h-4 text-amber-400" />
                      <span>{session.duration} minutes</span>
                    </div>
                    <div className="flex items-center space-x-1.5">
                      <Users className="w-4 h-4 text-amber-400" />
                      <span>Capacity: {session.capacity} participants</span>
                    </div>
                  </div>
                </div>

                <div className="pt-3 border-t border-slate-700/60 flex items-center justify-between">
                  <Link
                    to={`/creator/sessions/${session.id}/edit`}
                    className="inline-flex items-center space-x-1 text-xs font-semibold text-sky-400 hover:text-sky-300 bg-sky-950/60 px-3 py-1.5 rounded-lg border border-sky-800/50 transition"
                  >
                    <Edit3 className="w-3.5 h-3.5" />
                    <span>Edit</span>
                  </Link>

                  <button
                    onClick={() => handleDelete(session.id, session.title)}
                    disabled={deletingId === session.id}
                    className="inline-flex items-center space-x-1 text-xs font-semibold text-rose-400 hover:text-rose-300 bg-rose-950/60 px-3 py-1.5 rounded-lg border border-rose-800/50 transition disabled:opacity-50"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                    <span>{deletingId === session.id ? 'Deleting...' : 'Delete'}</span>
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
