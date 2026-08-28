export type Role = 'USER' | 'CREATOR';

export interface User {
  id: number;
  email: string;
  name: string;
  role: Role;
  profile_image?: string | null;
  created_at: string;
  updated_at: string;
}

export interface Session {
  id: number;
  creator: User;
  title: string;
  description: string;
  start_time: string;
  duration: number;
  capacity: number;
  booked_seats: number;
  remaining_seats: number;
  is_started: boolean;
  created_at: string;
  updated_at: string;
}

export interface Booking {
  id: number;
  user: User;
  session: Session;
  status: 'ACTIVE' | 'CANCELLED';
  created_at: string;
}

export interface AuthTokens {
  access: string;
  refresh: string;
  user: User;
}
