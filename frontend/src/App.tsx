import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { Navbar } from './components/Navbar';
import { ProtectedRoute } from './components/ProtectedRoute';
import { CreatorRoute } from './components/CreatorRoute';

import { LoginPage } from './pages/LoginPage';
import { OAuthCallbackPage } from './pages/OAuthCallbackPage';
import { SessionsCatalogPage } from './pages/SessionsCatalogPage';
import { SessionDetailPage } from './pages/SessionDetailPage';
import { UserBookingsPage } from './pages/UserBookingsPage';
import { ProfilePage } from './pages/ProfilePage';
import { CreatorDashboardPage } from './pages/CreatorDashboardPage';
import { CreateSessionPage } from './pages/CreateSessionPage';
import { EditSessionPage } from './pages/EditSessionPage';

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <AuthProvider>
        <div className="min-h-screen bg-slate-900 text-slate-100 flex flex-col font-sans">
          <Navbar />
          <main className="flex-1">
            <Routes>
              {/* Public Routes */}
              <Route path="/" element={<Navigate to="/sessions" replace />} />
              <Route path="/login" element={<LoginPage />} />
              <Route path="/auth/callback" element={<OAuthCallbackPage />} />
              <Route path="/sessions" element={<SessionsCatalogPage />} />
              <Route path="/sessions/:id" element={<SessionDetailPage />} />

              {/* Authenticated User Routes */}
              <Route element={<ProtectedRoute />}>
                <Route path="/bookings" element={<UserBookingsPage />} />
                <Route path="/profile" element={<ProfilePage />} />
              </Route>

              {/* Creator Only Routes */}
              <Route element={<CreatorRoute />}>
                <Route path="/creator" element={<CreatorDashboardPage />} />
                <Route path="/creator/sessions" element={<CreatorDashboardPage />} />
                <Route path="/creator/sessions/new" element={<CreateSessionPage />} />
                <Route path="/creator/sessions/:id/edit" element={<EditSessionPage />} />
              </Route>

              {/* Fallback 404 */}
              <Route path="*" element={<Navigate to="/sessions" replace />} />
            </Routes>
          </main>

          <footer className="bg-slate-950 border-t border-slate-800 py-6 text-center text-xs text-slate-500">
            <p>&copy; {new Date().getFullYear()} Sessions Marketplace. Production-grade DRF & React Platform.</p>
          </footer>
        </div>
      </AuthProvider>
    </BrowserRouter>
  );
};
export default App;
