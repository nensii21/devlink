import { Builder } from "./user";

export interface Conversation {
  id: number;
  with: Builder;
  lastMsg: string;
  time: string;
  unread: number;
}

export interface Message {
  id: number;
  text: string;
  own: boolean;
  time: string;
}