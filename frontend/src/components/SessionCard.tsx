import React from 'react';
import { Link } from 'react-router-dom';
import { Session } from '../types';
import { Clock, Users, Calendar, ArrowRight } from 'lucide-react';

interface SessionCardProps {
  session: Session;
}

export const SessionCard: React.FC<SessionCardProps> = ({ session }) => {
  const startDate = new Date(session.start_time).toLocaleString('en-US', {
    dateStyle: 'medium',
    timeStyle: 'short',
  });

  const isFull = session.remaining_seats <= 0;

  return (
    <div className="bg-slate-800/80 border border-slate-700/80 rounded-xl p-5 hover:border-sky-500/50 transition flex flex-col justify-between shadow-lg">
      <div>
        <div className="flex items-start justify-between mb-3">
          <h3 className="text-lg font-semibold text-white line-clamp-1">{session.title}</h3>
          {session.is_started ? (
            <span className="text-xs px-2.5 py-1 rounded-full bg-slate-700 text-slate-300 font-medium">
              Started
            </span>
          ) : isFull ? (
            <span className="text-xs px-2.5 py-1 rounded-full bg-rose-950/80 border border-rose-800 text-rose-300 font-medium">
              Full
            </span>
          ) : (
            <span className="text-xs px-2.5 py-1 rounded-full bg-emerald-950/80 border border-emerald-800 text-emerald-300 font-medium">
              {session.remaining_seats} seat{session.remaining_seats > 1 ? 's' : ''} left
            </span>
          )}
        </div>

        <p className="text-slate-400 text-sm mb-4 line-clamp-2">{session.description}</p>

        <div className="space-y-2 text-xs text-slate-300 mb-5">
          <div className="flex items-center space-x-2">
            <Calendar className="w-4 h-4 text-sky-400" />
            <span>{startDate}</span>
          </div>
          <div className="flex items-center space-x-2">
            <Clock className="w-4 h-4 text-sky-400" />
            <span>{session.duration} minutes</span>
          </div>
          <div className="flex items-center space-x-2">
            <Users className="w-4 h-4 text-sky-400" />
            <span>
              {session.booked_seats} / {session.capacity} booked
            </span>
          </div>
        </div>
      </div>

      <div className="pt-3 border-t border-slate-700/50 flex items-center justify-between">
        <div className="text-xs text-slate-400">
          By <span className="text-slate-200 font-medium">{session.creator?.name || 'Creator'}</span>
        </div>
        <Link
          to={`/sessions/${session.id}`}
          className="inline-flex items-center space-x-1 text-xs font-semibold text-sky-400 hover:text-sky-300 transition"
        >
          <span>View Details</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>
    </div>
  );
};
