export interface ChatMessageData {
  role: "user" | "assistant" | "system" | "task";
  content: string;
  timestamp?: Date;
  queryName?: string;
  status?: "pending" | "processing" | "completed" | "failed" | "running";
  messageId?: string;
  taskId?: string;
}
