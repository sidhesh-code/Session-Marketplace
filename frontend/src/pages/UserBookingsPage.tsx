import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Booking } from '../types';
import { getBookings, getActiveBookings, getPastBookings, cancelBooking } from '../api/bookings';
import { Calendar, Clock, BookmarkCheck, XCircle, ArrowRight, ShieldCheck } from 'lucide-react';

export const UserBookingsPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'ACTIVE' | 'PAST'>('ACTIVE');
  const [activeBookings, setActiveBookings] = useState<Booking[]>([]);
  const [pastBookings, setPastBookings] = useState<Booking[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [cancelLoadingId, setCancelLoadingId] = useState<number | null>(null);

  const fetchAllBookings = async () => {
    try {
      setLoading(true);
      const [active, past] = await Promise.all([
        getActiveBookings(),
        getPastBookings(),
      ]);
      setActiveBookings(active);
      setPastBookings(past);
    } catch (err: any) {
      setErrorMsg('Failed to load bookings.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAllBookings();
  }, []);

  const handleCancel = async (bookingId: number) => {
    if (!window.confirm('Are you sure you want to cancel this booking?')) return;

    try {
      setCancelLoadingId(bookingId);
      await cancelBooking(bookingId);
      await fetchAllBookings();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to cancel booking.');
    } finally {
      setCancelLoadingId(null);
    }
  };

  const currentList = activeTab === 'ACTIVE' ? activeBookings : pastBookings;

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      <div className="border-b border-slate-800 pb-5">
        <h1 className="text-3xl font-bold text-white tracking-tight">My Bookings</h1>
        <p className="text-slate-400 text-sm mt-1">Manage your active reservations and view past session history</p>
      </div>

      {/* Tabs */}
      <div className="flex space-x-3 border-b border-slate-800 pb-2">
        <button
          onClick={() => setActiveTab('ACTIVE')}
          className={`px-4 py-2 rounded-xl text-sm font-semibold transition flex items-center space-x-2 ${
            activeTab === 'ACTIVE'
              ? 'bg-sky-600/20 border border-sky-500 text-sky-300'
              : 'text-slate-400 hover:text-white bg-slate-800/40 border border-slate-700/50'
          }`}
        >
          <BookmarkCheck className="w-4 h-4" />
          <span>Active Bookings ({activeBookings.length})</span>
        </button>
        <button
          onClick={() => setActiveTab('PAST')}
          className={`px-4 py-2 rounded-xl text-sm font-semibold transition flex items-center space-x-2 ${
            activeTab === 'PAST'
              ? 'bg-slate-700 border border-slate-600 text-slate-200'
              : 'text-slate-400 hover:text-white bg-slate-800/40 border border-slate-700/50'
          }`}
        >
          <Clock className="w-4 h-4" />
          <span>Past / Cancelled ({pastBookings.length})</span>
        </button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center min-h-[40vh]">
          <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-sky-500"></div>
        </div>
      ) : errorMsg ? (
        <div className="bg-rose-950/80 border border-rose-800 text-rose-300 p-4 rounded-xl text-center text-sm">
          {errorMsg}
        </div>
      ) : currentList.length === 0 ? (
        <div className="text-center py-16 bg-slate-800/40 border border-slate-800 rounded-2xl p-8 space-y-3">
          <BookmarkCheck className="w-12 h-12 text-slate-500 mx-auto" />
          <h3 className="text-lg font-semibold text-white">
            {activeTab === 'ACTIVE' ? 'You have no active bookings' : 'You have no past bookings'}
          </h3>
          <p className="text-sm text-slate-400">
            {activeTab === 'ACTIVE' ? 'Browse the catalog to discover and book live sessions.' : 'Completed or cancelled bookings will appear here.'}
          </p>
          {activeTab === 'ACTIVE' && (
            <Link
              to="/sessions"
              className="inline-flex items-center space-x-2 bg-sky-600 hover:bg-sky-500 text-white font-semibold px-4 py-2 rounded-xl text-sm transition mt-2"
            >
              <span>Browse Catalog</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          )}
        </div>
      ) : (
        <div className="space-y-4">
          {currentList.map((booking) => {
            const startDate = new Date(booking.session.start_time).toLocaleString('en-US', {
              dateStyle: 'medium',
              timeStyle: 'short',
            });

            return (
              <div
                key={booking.id}
                className="bg-slate-800/80 border border-slate-700/80 rounded-xl p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-md"
              >
                <div className="space-y-2">
                  <div className="flex items-center space-x-2">
                    <span className="text-xs font-semibold text-slate-400">Booking #{booking.id}</span>
                    {booking.status === 'ACTIVE' ? (
                      <span className="text-xs px-2.5 py-0.5 rounded-full bg-emerald-950 border border-emerald-800 text-emerald-300 font-medium">
                        Active
                      </span>
                    ) : (
                      <span className="text-xs px-2.5 py-0.5 rounded-full bg-rose-950 border border-rose-800 text-rose-300 font-medium">
                        Cancelled
                      </span>
                    )}
                  </div>

                  <h3 className="text-lg font-semibold text-white">
                    <Link to={`/sessions/${booking.session.id}`} className="hover:text-sky-400 transition">
                      {booking.session.title}
                    </Link>
                  </h3>

                  <div className="flex flex-wrap items-center gap-4 text-xs text-slate-300">
                    <div className="flex items-center space-x-1.5">
                      <Calendar className="w-4 h-4 text-sky-400" />
                      <span>{startDate}</span>
                    </div>
                    <div className="flex items-center space-x-1.5">
                      <Clock className="w-4 h-4 text-sky-400" />
                      <span>{booking.session.duration} mins</span>
                    </div>
                    <div className="flex items-center space-x-1.5">
                      <ShieldCheck className="w-4 h-4 text-sky-400" />
                      <span>Host: {booking.session.creator?.name}</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center space-x-3 pt-3 sm:pt-0 border-t sm:border-t-0 border-slate-700/60">
                  {booking.status === 'ACTIVE' && activeTab === 'ACTIVE' && (
                    <button
                      onClick={() => handleCancel(booking.id)}
                      disabled={cancelLoadingId === booking.id}
                      className="bg-rose-950/80 hover:bg-rose-900 border border-rose-800 text-rose-300 px-4 py-2 rounded-xl text-xs font-semibold flex items-center space-x-1.5 transition disabled:opacity-50"
                    >
                      <XCircle className="w-4 h-4" />
                      <span>{cancelLoadingId === booking.id ? 'Cancelling...' : 'Cancel Booking'}</span>
                    </button>
                  )}
                  <Link
                    to={`/sessions/${booking.session.id}`}
                    className="bg-slate-700 hover:bg-slate-600 text-white px-3.5 py-2 rounded-xl text-xs font-semibold transition"
                  >
                    Details
                  </Link>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
