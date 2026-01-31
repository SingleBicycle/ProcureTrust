import { useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export default function Home() {
  const [sessionId, setSessionId] = useState("");
  const [message, setMessage] = useState("");
  const [reply, setReply] = useState("");
  const [status, setStatus] = useState("idle");

  const createSession = async () => {
    setStatus("creating");
    setReply("");
    try {
      const res = await fetch(`${API_BASE}/v1/sessions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });
      const data = await res.json();
      setSessionId(data.id || "");
      setStatus("ready");
    } catch (err) {
      setStatus("error");
    }
  };

  const sendChat = async () => {
    setStatus("chatting");
    setReply("");
    try {
      const res = await fetch(`${API_BASE}/v1/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId || undefined, message }),
      });
      const data = await res.json();
      setReply(data.reply || "");
      setStatus("ready");
    } catch (err) {
      setStatus("error");
    }
  };

  return (
    <main style={{ fontFamily: "Arial, sans-serif", padding: 24 }}>
      <h1>ProcureTrust</h1>
      <p>Stage A/B/C/D procurement assistant (P1 infra placeholder).</p>

      <section style={{ marginTop: 24 }}>
        <button onClick={createSession} disabled={status === "creating"}>
          Create Session
        </button>
        <div style={{ marginTop: 12 }}>
          <strong>Session ID:</strong> {sessionId || "(none)"}
        </div>
      </section>

      <section style={{ marginTop: 24 }}>
        <div>
          <label htmlFor="chat-input"><strong>Chat Input</strong></label>
        </div>
        <input
          id="chat-input"
          type="text"
          value={message}
          placeholder="Type a placeholder message..."
          onChange={(event) => setMessage(event.target.value)}
          style={{ width: "100%", maxWidth: 480, marginTop: 8 }}
        />
        <div style={{ marginTop: 12 }}>
          <button onClick={sendChat} disabled={!message || status === "chatting"}>
            Send
          </button>
        </div>
        <div style={{ marginTop: 12 }}>
          <strong>Reply:</strong> {reply || "(none)"}
        </div>
      </section>

      <section style={{ marginTop: 24 }}>
        <div><strong>Status:</strong> {status}</div>
        <div><strong>API Base:</strong> {API_BASE}</div>
      </section>
    </main>
  );
}
