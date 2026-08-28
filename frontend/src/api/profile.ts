import { api } from './axios';
import { User } from '../types';

export const getProfile = async (): Promise<User> => {
  const res = await api.get('/profile/');
  return res.data;
};

export const updateProfile = async (data: Partial<{ name: string; profile_image: string }>): Promise<User> => {
  const res = await api.patch('/profile/', data);
  return res.data;
};
