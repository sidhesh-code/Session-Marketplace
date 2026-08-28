import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { exchangeOAuthCode } from '../api/auth';
import { Role } from '../types';
import { AlertCircle } from 'lucide-react';

export const OAuthCallbackPage: React.FC = () => {
  const { loginWithTokens } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    const code = searchParams.get('code');
    const error = searchParams.get('error');

    if (error || !code) {
      if (error === 'access_denied') {
        navigate('/login?error=oauth_cancelled');
      } else {
        navigate('/login?error=oauth_failed');
      }
      return;
    }

    const savedRole = (localStorage.getItem('oauth_role') as Role) || 'USER';
    localStorage.removeItem('oauth_role');

    exchangeOAuthCode(code, savedRole)
      .then((tokens) => {
        loginWithTokens(tokens);
        navigate('/sessions');
      })
      .catch((err: any) => {
        setErrorMsg(err.response?.data?.detail || 'Authentication failed during Google OAuth code exchange.');
      });
  }, [searchParams, loginWithTokens, navigate]);

  if (errorMsg) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center p-4">
        <div className="bg-slate-800 border border-slate-700 rounded-xl p-6 max-w-md w-full text-center space-y-4">
          <AlertCircle className="w-12 h-12 text-rose-500 mx-auto" />
          <h2 className="text-xl font-bold text-white">OAuth Authentication Error</h2>
          <p className="text-sm text-slate-300">{errorMsg}</p>
          <button
            onClick={() => navigate('/login')}
            className="bg-sky-600 hover:bg-sky-500 text-white font-semibold px-4 py-2 rounded-lg text-sm transition"
          >
            Return to Login
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-[60vh] flex flex-col items-center justify-center space-y-4">
      <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-sky-500"></div>
      <p className="text-slate-300 font-medium text-sm">Authenticating with Google OAuth...</p>
    </div>
  );
};
