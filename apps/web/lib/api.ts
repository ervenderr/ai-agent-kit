import { parseSse } from "./sse";
import type { AgentEvent } from "./types";

// A URL, not a secret. The bearer token is typed by the user and kept in memory/sessionStorage only.
const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const headers = (token: string) => ({
  Authorization: `Bearer ${token}`,
  "Content-Type": "application/json",
});

export async function streamRun(
  token: string,
  input: string,
  signal: AbortSignal,
  onEvent: (e: AgentEvent) => void,
): Promise<void> {
  const res = await fetch(`${API_URL}/runs`, {
    method: "POST",
    headers: headers(token),
    body: JSON.stringify({ input }),
    signal,
  });
  if (!res.ok || !res.body) throw new Error(`Request failed (${res.status})`);
  const reader = res.body.pipeThrough(new TextDecoderStream()).getReader();
  let buffer = "";
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    const parsed = parseSse(buffer + value);
    buffer = parsed.rest;
    parsed.events.forEach(onEvent);
  }
}

export async function cancelRun(token: string, runId: string): Promise<void> {
  await fetch(`${API_URL}/runs/${runId}/cancel`, { method: "POST", headers: headers(token) });
}
