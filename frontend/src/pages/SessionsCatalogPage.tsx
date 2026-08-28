import React, { useEffect, useState } from 'react';
import { Session } from '../types';
import { getPublicSessions } from '../api/sessions';
import { SessionCard } from '../components/SessionCard';
import { Search, CalendarX } from 'lucide-react';

export const SessionsCatalogPage: React.FC = () => {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>('');

  useEffect(() => {
    getPublicSessions()
      .then((data) => setSessions(data))
      .catch(() => setErrorMsg('Failed to load session catalog. Please try refreshing.'))
      .finally(() => setLoading(false));
  }, []);

  const filteredSessions = sessions.filter((s) =>
    s.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    s.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
    s.creator?.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Hero Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight">Available Sessions</h1>
          <p className="text-slate-400 text-sm mt-1">Browse live mentorship and video sessions from top creators</p>
        </div>

        {/* Search Input */}
        <div className="relative w-full md:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
          <input
            type="text"
            placeholder="Search sessions or creators..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 rounded-xl pl-10 pr-4 py-2 text-sm text-white placeholder-slate-400 focus:outline-none focus:border-sky-500 transition"
          />
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center min-h-[40vh]">
          <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-sky-500"></div>
        </div>
      ) : errorMsg ? (
        <div className="bg-rose-950/80 border border-rose-800 text-rose-300 p-4 rounded-xl text-center">
          {errorMsg}
        </div>
      ) : filteredSessions.length === 0 ? (
        <div className="text-center py-16 bg-slate-800/40 border border-slate-800 rounded-2xl p-8 space-y-3">
          <CalendarX className="w-12 h-12 text-slate-500 mx-auto" />
          <h3 className="text-lg font-semibold text-white">No sessions available</h3>
          <p className="text-sm text-slate-400">
            {searchQuery ? 'No sessions match your search query.' : 'Check back later for newly published creator sessions.'}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredSessions.map((session) => (
            <SessionCard key={session.id} session={session} />
          ))}
        </div>
      )}
    </div>
  );
};
