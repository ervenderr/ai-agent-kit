export type AgentEvent =
  | { type: "run"; run_id: string }
  | { type: "text_delta"; text: string }
  | { type: "tool_call"; id: string; name: string; args: Record<string, unknown> }
  | {
      type: "tool_result";
      id: string;
      name: string;
      result_size: number;
      latency_ms: number;
      is_error: boolean;
      preview: string;
    }
  | { type: "final"; text: string; steps: number; cost_usd: number }
  | { type: "error"; code: string; message: string; steps: number };

export interface ToolCard {
  id: string;
  name: string;
  args: Record<string, unknown>;
  resultSize?: number;
  latencyMs?: number;
  isError?: boolean;
  preview?: string;
}

export type TurnStatus = "streaming" | "done" | "failed" | "stopped" | "interrupted";

export interface Turn {
  input: string;
  runId?: string;
  text: string;
  tools: ToolCard[];
  status: TurnStatus;
  error?: string;
}
