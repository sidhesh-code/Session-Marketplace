import { api } from './axios';
import { AuthTokens, Role } from '../types';

export const getGoogleAuthUrl = async (): Promise<{ auth_url: string }> => {
  const res = await api.get('/auth/oauth/');
  return res.data;
};

export const exchangeOAuthCode = async (code: string, role: Role = 'USER'): Promise<AuthTokens> => {
  const res = await api.post('/auth/oauth/callback/', { code, role });
  return res.data;
};

export const devLogin = async (email: string, name?: string, role: Role = 'USER'): Promise<AuthTokens> => {
  const res = await api.post('/auth/dev-login/', { email, name, role });
  return res.data;
};
