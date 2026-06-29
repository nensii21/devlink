import { Builder, CurrentUser } from "../types/user";
export interface Builder {
  id: number;
  name: string;
  role: string;
  avatar: string;
  skills: string[];
  bio: string;
  location: string;
  available: boolean;
  online: boolean;
  xp: string;
}

export interface CurrentUser {
  name: string;
  role: string;
  avatar: string;
  location: string;
}