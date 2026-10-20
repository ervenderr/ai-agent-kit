import type { ToolCard as Card } from "@/lib/types";

export function ToolCardView({ card }: { card: Card }) {
  const pending = card.resultSize === undefined;
  return (
    <details className={`card${card.isError ? " err" : ""}`}>
      <summary>
        {card.name} — {pending ? "running…" : `${card.resultSize} chars, ${card.latencyMs} ms${card.isError ? ", error" : ""}`}
      </summary>
      <pre>{JSON.stringify(card.args, null, 2)}</pre>
      {card.preview && <pre>{card.preview}</pre>}
    </details>
  );
}
