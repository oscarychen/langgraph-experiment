import { Link } from "react-router-dom";

export default function Home() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-6 p-8">
      <h1 className="text-4xl font-bold">HR RAG</h1>
      <p className="text-lg text-gray-600">
        AI-powered HR document question answering
      </p>
      <Link
        to="/chat"
        className="rounded-lg bg-neutral-900 px-6 py-3 text-white hover:bg-neutral-700"
      >
        Start Chatting
      </Link>
    </div>
  );
}
