import { api } from './axios';
import { Session } from '../types';

export const getPublicSessions = async (): Promise<Session[]> => {
  const res = await api.get('/sessions/');
  return res.data;
};

export const getPublicSessionDetail = async (id: number): Promise<Session> => {
  const res = await api.get(`/sessions/${id}/`);
  return res.data;
};

export const getCreatorSessions = async (): Promise<Session[]> => {
  const res = await api.get('/creator/sessions/');
  return res.data;
};

export const createCreatorSession = async (data: {
  title: string;
  description: string;
  start_time: string;
  duration: number;
  capacity: number;
}): Promise<Session> => {
  const res = await api.post('/creator/sessions/', data);
  return res.data;
};

export const updateCreatorSession = async (
  id: number,
  data: Partial<{ title: string; description: string; start_time: string; duration: number; capacity: number }>
): Promise<Session> => {
  const res = await api.patch(`/creator/sessions/${id}/`, data);
  return res.data;
};

export const deleteCreatorSession = async (id: number): Promise<void> => {
  await api.delete(`/creator/sessions/${id}/`);
};
