"use client";

import { useRef, useState } from "react";
import { cancelRun, streamRun } from "@/lib/api";
import type { AgentEvent, Turn } from "@/lib/types";
import { Markdown } from "./Markdown";
import { ToolCardView } from "./ToolCard";

const TOKEN_KEY = "agent-token";

function reduce(turn: Turn, e: AgentEvent): Turn {
  switch (e.type) {
    case "run":
      return { ...turn, runId: e.run_id };
    case "text_delta":
      return { ...turn, text: turn.text + e.text };
    case "tool_call":
      return { ...turn, tools: [...turn.tools, { id: e.id, name: e.name, args: e.args }] };
    case "tool_result":
      return {
        ...turn,
        tools: turn.tools.map((t) =>
          t.id === e.id ? { ...t, resultSize: e.result_size, latencyMs: e.latency_ms, isError: e.is_error, preview: e.preview } : t,
        ),
      };
    case "final":
      return { ...turn, text: e.text, status: "done" };
    case "error":
      return { ...turn, status: e.code === "cancelled" ? "stopped" : "failed", error: e.message };
  }
}

export function Chat() {
  const [token, setToken] = useState(() => {
    try {
      return sessionStorage.getItem(TOKEN_KEY) ?? "";
    } catch {
      return "";
    }
  });
  const [input, setInput] = useState("");
  const [turns, setTurns] = useState<Turn[]>([]);
  const abort = useRef<AbortController | null>(null);
  const busy = turns.at(-1)?.status === "streaming";

  const patchLast = (fn: (t: Turn) => Turn) => setTurns((ts) => ts.map((t, i) => (i === ts.length - 1 ? fn(t) : t)));

  async function send() {
    const text = input.trim();
    if (!text || !token || busy) return;
    try {
      sessionStorage.setItem(TOKEN_KEY, token);
    } catch {}
    setInput("");
    setTurns((ts) => [...ts, { input: text, text: "", tools: [], status: "streaming" }]);
    abort.current = new AbortController();
    try {
      await streamRun(token, text, abort.current.signal, (e) => patchLast((t) => reduce(t, e)));
      // A stream that ends without `final`/`error` was cut off: show it as partial, not as success.
      patchLast((t) => (t.status === "streaming" ? { ...t, status: "interrupted", error: "Connection ended early." } : t));
    } catch (err) {
      if (abort.current?.signal.aborted) return;
      patchLast((t) => ({ ...t, status: "failed", error: err instanceof Error ? err.message : "Request failed" }));
    }
  }

  async function stop() {
    const last = turns.at(-1);
    if (last?.runId) await cancelRun(token, last.runId).catch(() => undefined);
    abort.current?.abort();
    patchLast((t) => (t.status === "streaming" ? { ...t, status: "stopped" } : t));
  }

  return (
    <>
      <div className="row">
        <input type="password" placeholder="API token" value={token} onChange={(e) => setToken(e.target.value)} />
      </div>
      {turns.map((t, i) => (
        <section className="turn" key={i}>
          <div className="user">{t.input}</div>
          {t.tools.map((c) => <ToolCardView key={c.id} card={c} />)}
          <Markdown>{t.text}</Markdown>
          {t.status === "streaming" && <p className="notice">working…</p>}
          {t.status === "stopped" && <p className="notice">Stopped.</p>}
          {t.error && t.status !== "stopped" && <p className="error">{t.error}</p>}
        </section>
      ))}
      <form className="row" onSubmit={(e) => { e.preventDefault(); void send(); }}>
        <input placeholder="Ask something…" value={input} onChange={(e) => setInput(e.target.value)} />
        {busy ? (
          <button type="button" onClick={() => void stop()}>Stop</button>
        ) : (
          <button type="submit" disabled={!input.trim() || !token}>Send</button>
        )}
      </form>
    </>
  );
}
