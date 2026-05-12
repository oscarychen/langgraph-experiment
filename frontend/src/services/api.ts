const API_BASE = "/api";

export interface ChatHistoryMessage {
  role: "user" | "assistant";
  content: string;
}

export async function sendChatMessage(
  question: string,
  history: ChatHistoryMessage[] = []
): Promise<{ answer: string; sources: string[] }> {
  const response = await fetch(`${API_BASE}/chat/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, history }),
  });
  if (!response.ok) throw new Error("Failed to send message");
  return response.json();
}