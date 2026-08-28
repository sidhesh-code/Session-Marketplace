import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Calendar, User as UserIcon, LogOut, Video, PlusCircle, BookmarkCheck } from 'lucide-react';

export const Navbar: React.FC = () => {
  const { user, isAuthenticated, isCreator, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <nav className="bg-slate-950 border-b border-slate-800 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Brand Logo */}
          <Link to="/sessions" className="flex items-center space-x-3 text-sky-400 font-bold text-xl tracking-tight">
            <Video className="w-7 h-7 text-sky-500" />
            <span className="text-white">Sessions</span>
            <span className="text-sky-400 text-xs px-2 py-0.5 rounded bg-sky-950/80 border border-sky-800">MARKETPLACE</span>
          </Link>

          {/* Nav Items */}
          <div className="flex items-center space-x-6">
            <Link
              to="/sessions"
              className="text-slate-300 hover:text-white flex items-center space-x-1.5 text-sm font-medium transition"
            >
              <Calendar className="w-4 h-4" />
              <span>Catalog</span>
            </Link>

            {isAuthenticated ? (
              <>
                {!isCreator && (
                  <Link
                    to="/bookings"
                    className="text-slate-300 hover:text-white flex items-center space-x-1.5 text-sm font-medium transition"
                  >
                    <BookmarkCheck className="w-4 h-4" />
                    <span>My Bookings</span>
                  </Link>
                )}

                {isCreator && (
                  <Link
                    to="/creator"
                    className="text-amber-400 hover:text-amber-300 flex items-center space-x-1.5 text-sm font-medium transition bg-amber-950/40 px-3 py-1.5 rounded-md border border-amber-800/50"
                  >
                    <PlusCircle className="w-4 h-4" />
                    <span>Creator Dashboard</span>
                  </Link>
                )}

                <Link
                  to="/profile"
                  className="flex items-center space-x-2 text-slate-300 hover:text-white text-sm font-medium transition"
                >
                  {user?.profile_image ? (
                    <img src={user.profile_image} alt={user.name} className="w-7 h-7 rounded-full object-cover border border-slate-700" />
                  ) : (
                    <div className="w-7 h-7 rounded-full bg-slate-800 flex items-center justify-center text-slate-300 text-xs font-bold border border-slate-700">
                      {user?.name.charAt(0).toUpperCase()}
                    </div>
                  )}
                  <span className="hidden sm:inline">{user?.name}</span>
                  <span className="text-xs text-slate-500 bg-slate-800 px-1.5 py-0.5 rounded">
                    {user?.role}
                  </span>
                </Link>

                <button
                  onClick={logout}
                  className="text-slate-400 hover:text-rose-400 flex items-center space-x-1 text-sm font-medium transition ml-2"
                  title="Logout"
                >
                  <LogOut className="w-4 h-4" />
                  <span className="hidden sm:inline">Logout</span>
                </button>
              </>
            ) : (
              <button
                onClick={() => navigate('/login')}
                className="bg-sky-600 hover:bg-sky-500 text-white px-4 py-2 rounded-lg text-sm font-semibold transition shadow-md shadow-sky-950"
              >
                Sign In
              </button>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
};
