const API_BASE = "/api";

export async function sendChatMessage(
  question: string
): Promise<{ answer: string; sources: string[] }> {
  const response = await fetch(`${API_BASE}/chat/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  if (!response.ok) throw new Error("Failed to send message");
  return response.json();
}