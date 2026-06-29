import { Builder } from "./user";

export interface Project {
  id: number;
  title: string;
  founder: Builder;
  desc: string;
  skills: string[];
  teamSize: number;
  maxTeam: number;
  stage: string;
  remote: boolean;
  apps: number;
  featured: boolean;
  cover: string;
  rolesNeeded: string[];
}