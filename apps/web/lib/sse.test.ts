import { describe, expect, it } from "vitest";
import { parseSse } from "./sse";

describe("parseSse", () => {
  it("parses complete events and keeps the partial tail", () => {
    const { events, rest } = parseSse('data: {"type":"text_delta","text":"hi"}\n\ndata: {"type":"fi');
    expect(events).toEqual([{ type: "text_delta", text: "hi" }]);
    expect(rest).toBe('data: {"type":"fi');
  });

  it("joins a tail with the next chunk", () => {
    const first = parseSse('data: {"type":"run","run');
    const second = parseSse(first.rest + '_id":"r1"}\n\n');
    expect(second.events).toEqual([{ type: "run", run_id: "r1" }]);
  });
});
