import { Conversation, Message } from "../types/message";
import { BUILDERS } from "./builders";
const CONVERSATIONS: Conversation[] = [
     { id: 1, with: BUILDERS[0], lastMsg: "Let me know when you push the first commit.", time: "2m", unread: 2 },
      { id: 2, with: BUILDERS[3], lastMsg: "The Figma handoff is ready for review.", time: "1h", unread: 0 },
      { id: 3, with: BUILDERS[1], lastMsg: "K8s setup is done, ping me when ready.", time: "3h", unread: 1 },
      { id: 4, with: BUILDERS[5], lastMsg: "The RAG pipeline is working great now!", time: "1d", unread: 0 },
];

const MESSAGES: Message[] = [
 { id: 1, text: "Hey! I saw your Build With Me post for the AI Platform project.", own: false, time: "10:02 AM" },
  { id: 2, text: "Hi Marcus! Yes, still looking for an ML engineer. Your profile looks like a great fit.", own: true, time: "10:05 AM" },
  { id: 3, text: "Awesome. I've been working on RAG pipelines lately — exactly what you need. Want to hop on a call?", own: false, time: "10:07 AM" },
  { id: 4, text: "Definitely. How does Thursday work for you?", own: true, time: "10:09 AM" },
  { id: 5, text: "Thursday at 3pm PT works perfectly. I'll send a Cal invite.", own: false, time: "10:11 AM" },
  { id: 6, text: "Let me know when you push the first commit.", own: false, time: "10:14 AM" },
];