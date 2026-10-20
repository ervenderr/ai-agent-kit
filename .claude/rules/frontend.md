---
paths:
  - "apps/web/**/*.{ts,tsx}"
---
- Server components by default; `"use client"` only where state or events need it.
- Render model output through a sanitizing markdown renderer, never `dangerouslySetInnerHTML`.
- Typed API client; no secrets in `NEXT_PUBLIC_*`.
- Handle partial and failed streams in UI state.
