import { api } from './axios';
import { Booking } from '../types';

export const bookSession = async (sessionId: number): Promise<Booking> => {
  const res = await api.post(`/sessions/${sessionId}/book/`);
  return res.data;
};

export const getBookings = async (): Promise<Booking[]> => {
  const res = await api.get('/bookings/');
  return res.data;
};

export const getActiveBookings = async (): Promise<Booking[]> => {
  const res = await api.get('/bookings/active/');
  return res.data;
};

export const getPastBookings = async (): Promise<Booking[]> => {
  const res = await api.get('/bookings/past/');
  return res.data;
};

export const cancelBooking = async (bookingId: number): Promise<Booking> => {
  const res = await api.post(`/bookings/${bookingId}/cancel/`);
  return res.data;
};
