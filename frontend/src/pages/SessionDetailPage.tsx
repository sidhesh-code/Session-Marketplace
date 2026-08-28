import React, { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { Session } from '../types';
import { getPublicSessionDetail } from '../api/sessions';
import { bookSession } from '../api/bookings';
import { useAuth } from '../context/AuthContext';
import { Calendar, Clock, Users, ShieldAlert, ArrowLeft, CheckCircle2, User } from 'lucide-react';

export const SessionDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { isAuthenticated, isCreator } = useAuth();

  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [bookingLoading, setBookingLoading] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    getPublicSessionDetail(Number(id))
      .then((data) => setSession(data))
      .catch(() => setErrorMsg('Failed to load session details.'))
      .finally(() => setLoading(false));
  }, [id]);

  const handleBookSession = async () => {
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }

    if (!session) return;

    try {
      setBookingLoading(true);
      setErrorMsg(null);
      setSuccessMsg(null);
      
      await bookSession(session.id);
      setSuccessMsg('Booking successful! View your active bookings on the My Bookings page.');
      
      // Refresh session detail to reflect updated seat counts
      const updated = await getPublicSessionDetail(session.id);
      setSession(updated);
    } catch (err: any) {
      if (err.response?.status === 409) {
        setErrorMsg(err.response.data?.detail || 'Booking unavailable (Session full or already booked).');
      } else if (err.response?.status === 403) {
        setErrorMsg(err.response.data?.detail || 'Creators cannot book sessions.');
      } else {
        setErrorMsg('An unexpected error occurred during booking. Please try again.');
      }
    } finally {
      setBookingLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-sky-500"></div>
      </div>
    );
  }

  if (!session) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-12 text-center space-y-4">
        <h2 className="text-xl font-bold text-white">Session Not Found</h2>
        <p className="text-slate-400">The session you are looking for does not exist or has been removed.</p>
        <Link to="/sessions" className="inline-flex items-center space-x-2 text-sky-400 font-semibold hover:underline">
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Catalog</span>
        </Link>
      </div>
    );
  }

  const startDate = new Date(session.start_time).toLocaleString('en-US', {
    dateStyle: 'full',
    timeStyle: 'short',
  });

  const isFull = session.remaining_seats <= 0;
  const isStarted = session.is_started;

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 space-y-6">
      <Link to="/sessions" className="inline-flex items-center space-x-1.5 text-sm text-slate-400 hover:text-white transition">
        <ArrowLeft className="w-4 h-4" />
        <span>Back to Catalog</span>
      </Link>

      <div className="bg-slate-800/90 border border-slate-700/80 rounded-2xl p-6 sm:p-8 space-y-6 shadow-xl">
        {/* Banner Alert Messages */}
        {errorMsg && (
          <div className="bg-rose-950/90 border border-rose-800 text-rose-300 p-4 rounded-xl flex items-start space-x-3 text-sm">
            <ShieldAlert className="w-5 h-5 flex-shrink-0 text-rose-400 mt-0.5" />
            <span>{errorMsg}</span>
          </div>
        )}

        {successMsg && (
          <div className="bg-emerald-950/90 border border-emerald-800 text-emerald-300 p-4 rounded-xl flex items-start space-x-3 text-sm">
            <CheckCircle2 className="w-5 h-5 flex-shrink-0 text-emerald-400 mt-0.5" />
            <div className="space-y-1">
              <span>{successMsg}</span>
              <div>
                <Link to="/bookings" className="text-emerald-400 font-semibold hover:underline">
                  Go to My Bookings &rarr;
                </Link>
              </div>
            </div>
          </div>
        )}

        {/* Title & Status Badges */}
        <div className="space-y-3">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h1 className="text-2xl sm:text-3xl font-bold text-white">{session.title}</h1>
            {isStarted ? (
              <span className="bg-slate-700 text-slate-300 text-xs px-3 py-1 rounded-full font-medium">
                Already Started
              </span>
            ) : isFull ? (
              <span className="bg-rose-950 border border-rose-800 text-rose-300 text-xs px-3 py-1 rounded-full font-medium">
                Session Full
              </span>
            ) : (
              <span className="bg-emerald-950 border border-emerald-800 text-emerald-300 text-xs px-3 py-1 rounded-full font-medium">
                Available
              </span>
            )}
          </div>

          <div className="flex items-center space-x-3 text-sm text-slate-300">
            <div className="flex items-center space-x-1.5">
              <User className="w-4 h-4 text-sky-400" />
              <span>Hosted by <strong className="text-white">{session.creator?.name}</strong></span>
            </div>
          </div>
        </div>

        {/* Description */}
        <div className="border-t border-slate-700/60 pt-4 space-y-2">
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Description</h3>
          <p className="text-slate-300 leading-relaxed text-sm sm:text-base whitespace-pre-line">
            {session.description}
          </p>
        </div>

        {/* Metadata Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 border-t border-b border-slate-700/60 py-5">
          <div className="flex items-center space-x-3 bg-slate-900/60 p-3.5 rounded-xl border border-slate-700/50">
            <Calendar className="w-6 h-6 text-sky-400 flex-shrink-0" />
            <div>
              <div className="text-xs text-slate-400">Date & Time</div>
              <div className="text-xs sm:text-sm font-semibold text-white">{startDate}</div>
            </div>
          </div>

          <div className="flex items-center space-x-3 bg-slate-900/60 p-3.5 rounded-xl border border-slate-700/50">
            <Clock className="w-6 h-6 text-sky-400 flex-shrink-0" />
            <div>
              <div className="text-xs text-slate-400">Duration</div>
              <div className="text-sm font-semibold text-white">{session.duration} Minutes</div>
            </div>
          </div>

          <div className="flex items-center space-x-3 bg-slate-900/60 p-3.5 rounded-xl border border-slate-700/50">
            <Users className="w-6 h-6 text-sky-400 flex-shrink-0" />
            <div>
              <div className="text-xs text-slate-400">Capacity & Seats</div>
              <div className="text-sm font-semibold text-white">
                {session.remaining_seats} / {session.capacity} seats left
              </div>
            </div>
          </div>
        </div>

        {/* Booking CTA Section */}
        <div className="pt-2 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="text-xs text-slate-400">
            {isCreator ? (
              <span className="text-amber-400 font-medium">Logged in as Creator (Creators cannot book sessions).</span>
            ) : (
              <span>Instant booking confirmation with PostgreSQL capacity locking.</span>
            )}
          </div>

          {isStarted ? (
            <button
              disabled
              className="bg-slate-700 text-slate-400 font-bold px-6 py-3 rounded-xl cursor-not-allowed text-sm"
            >
              Session Already Started
            </button>
          ) : isFull ? (
            <button
              disabled
              className="bg-rose-950/80 text-rose-400 border border-rose-800 font-bold px-6 py-3 rounded-xl cursor-not-allowed text-sm"
            >
              Session Full
            </button>
          ) : (
            <button
              onClick={handleBookSession}
              disabled={bookingLoading || isCreator}
              className="bg-sky-600 hover:bg-sky-500 text-white font-bold px-8 py-3 rounded-xl text-sm transition shadow-lg shadow-sky-950 disabled:opacity-50 flex items-center justify-center space-x-2"
            >
              {bookingLoading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-t-2 border-b-2 border-white"></div>
                  <span>Reserving Seat...</span>
                </>
              ) : (
                <span>Book Session</span>
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
