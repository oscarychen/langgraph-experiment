import { useState } from "react";
import { useChatStore } from "@/stores/chatStore";
import { sendChatMessage } from "@/services/api";

export default function Chat() {
  const [input, setInput] = useState("");
  const { messages, isLoading, addMessage, setLoading } = useChatStore();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const question = input.trim();
    const history = messages.map(({ role, content }) => ({ role, content }));
    setInput("");
    addMessage({ role: "user", content: question });
    setLoading(true);

    try {
      const response = await sendChatMessage(question, history);
      addMessage({ role: "assistant", content: response.answer });
    } catch {
      addMessage({
        role: "assistant",
        content: "Sorry, something went wrong.",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen flex-col">
      <header className="border-b p-4">
        <h1 className="text-xl font-semibold">HR RAG Chat</h1>
      </header>

      <main className="flex-1 overflow-y-auto p-4">
        <div className="mx-auto max-w-2xl space-y-4">
          {messages.map((msg, i) => (
            <div
              key={i}
              className={`rounded-lg p-3 ${
                msg.role === "user"
                  ? "ml-auto max-w-md bg-neutral-900 text-white"
                  : "mr-auto max-w-md bg-gray-100"
              }`}
            >
              {msg.content}
            </div>
          ))}
          {isLoading && (
            <div className="mr-auto max-w-md rounded-lg bg-gray-100 p-3 text-gray-500">
              Thinking...
            </div>
          )}
        </div>
      </main>

      <footer className="border-t p-4">
        <form
          onSubmit={handleSubmit}
          className="mx-auto flex max-w-2xl gap-2"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question..."
            className="flex-1 rounded-lg border px-4 py-2 focus:outline-none focus:ring-2 focus:ring-neutral-400"
          />
          <button
            type="submit"
            disabled={isLoading}
            className="rounded-lg bg-neutral-900 px-6 py-2 text-white hover:bg-neutral-700 disabled:opacity-50"
          >
            Send
          </button>
        </form>
      </footer>
    </div>
  );
}
