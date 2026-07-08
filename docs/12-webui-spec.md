# 12 WebUI Design Spec

The complete design of the PaperGraph monitor. `docs/07` pins the HTTP surface and `docs/10` §6 pins the v1 scope (five primary views; write actions = queue claim/release + db rebuild only); this doc pins everything else: layout, encoding, tokens, interactions, states, and test hooks. On any WebUI design question, this doc is authoritative — but it may not widen the v1 scope or the API surface (amend docs/10 / docs/07 first).

## 1. Purpose and Principles

The UI answers, within five seconds of opening: *What is open? Who is working on what? What is blocked? What can be committed? What is frozen? Is the index stale?*

```text
P1  Read-mostly mirror. The UI renders canonical state; it is never a mutation
    path around the gates. Its three write actions call the same code paths as
    the CLI and appear in the event log like any actor.
P2  Every pixel traceable. Anything rendered can be clicked through to the raw
    canonical record that produced it (the Record Drawer). No UI-invented state.
P3  Honest staleness. The UI reads the derived DuckDB index; whenever the index
    is stale it says so, loudly, before anything else.
P4  Never color alone. Every state/status encoding pairs color with a glyph or
    text. The palette below is CVD-validated; the pairing rule still holds.
P5  Boring tech. One static page, vanilla JS polling (fetch + setInterval) + vendored
    cytoscape.js. No build step, no npm, no client framework.
```

## 2. App Shell

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ ⚠ INDEX STALE — showing data from 09:41. [Rebuild]          (banner slot) │
├──────────────────────────────────────────────────────────────────────────┤
│ PaperGraph  p4-ldi   Contract ✓v1   MSA 7/9   ● 3 open  ☠ 1 dead   ◐ ⟳  │
├───────────┬──────────────────────────────────────────────┬───────────────┤
│ Overview  │                                              │  Record       │
│ Logic Map │              MAIN CONTENT                    │  Drawer       │
│ Queue     │              (active view)                   │  (slides in   │
│ Evidence  │                                              │   on any id   │
│ Compiler  │                                              │   click)      │
│           │                                              │               │
└───────────┴──────────────────────────────────────────────┴───────────────┘
```

```text
Top bar      project id · contract chip (✓v1 accepted / ✗ draft, critical if
             unaccepted) · MSA progress (n/9 passing) · open-work count ·
             dead-letter count (hidden when 0) · theme toggle · refresh state.
Left nav     the five primary views (docs/10 §6). Events is an auxiliary
             full-page list reached from Overview ("recent events → view all"),
             not a nav item — this is how 07's view list and 10's "five views"
             reconcile.
Banner slot  one banner max, priority order: (1) corruption — any API call
             returning exit-3 semantics locks the UI under a critical banner
             "State corrupted — run `paperproof verify`" until reload;
             (2) stale index — warning banner with [Rebuild] button;
             (3) contract unaccepted — info banner "expansion gated".
             Note: a canonical JSONL corrupted while the index is present reads
             as "stale" (index-backed endpoints never parse JSONL) and escalates
             to the corruption lock on the next rebuild attempt — so "stale" can
             transiently mask "corrupt" until a rebuild is tried.
Routing      hash-based: #/overview #/map #/queue #/evidence #/compiler
             #/events #/record/<id> (drawer deep-link). Filters serialize into
             the hash query so views are shareable.
Polling      vanilla-JS polling (fetch + setInterval) every 5s on the active view only;
             pauses when the tab is hidden; manual ⟳ always available. The
             Logic Map re-fetches on a 15s cycle and diffs before re-layout.
```

## 3. Design Tokens

Defined once as CSS custom properties on `:root`, dark values under
`@media (prefers-color-scheme: dark)` plus a manual `[data-theme]` override.
(Palette validated with the six-checks validator against both surfaces.)

```css
:root {
  --page: #f9f9f7;  --surface: #fcfcfb;  --ink: #0b0b0b;
  --ink-2: #52514e; --muted: #898781;    --grid: #e1e0d9;
  --border: rgba(11,11,11,.10);
  /* lifecycle_state — always paired with its glyph */
  --st-candidate: #898781;  --st-pending: #2a78d6;   --st-active: #0ca30c;
  --st-repair: #eda100;     --st-docs: #4a3aa7;      --st-rejected: #d03b3b;
  --st-parked: #52514e;
  /* work-item status accents (chips) */
  --q-good: #0ca30c; --q-warn: #eda100; --q-serious: #ec835a; --q-crit: #d03b3b;
  --accent: #2a78d6;
}
[data-theme="dark"], @media (prefers-color-scheme: dark) { /* … */
  --page:#0d0d0d; --surface:#1a1a19; --ink:#fff; --ink-2:#c3c2b7;
  --grid:#2c2c2a; --border:rgba(255,255,255,.10);
  --st-pending:#3987e5; --st-active:#008300; --st-repair:#c98500;
  --st-docs:#9085e9;    --q-good:#0ca30c;    --q-warn:#c98500;
}
```

Both state palettes are **validator-verified** (six-checks, categorical mode, against `#fcfcfb` / `#1a1a19`): lightness band, chroma floor, and surface contrast pass; the worst CVD pair (amber↔green, protan ΔE 9.4 light / 10.3 dark) sits in the floor band, which is legal only with secondary encoding — that is exactly why the glyph pairing (P4) is normative, not decorative. Light-mode amber is sub-3:1 on the surface (relief rule): it never appears without its glyph and a text label. Re-run the validator if any value changes.

State → color + glyph (the pairing is normative):

| lifecycle_state | token | glyph | | status (work item) | accent | glyph |
| --- | --- | --- | --- | --- | --- | --- |
| candidate | st-candidate | ◌ | | queued / blocked | muted | ○ / ⊘ |
| pending_proof | st-pending | ◔ | | claimed / running | accent | ◑ |
| active | st-active | ✓ | | validating / validated | accent | ◕ / ✔ |
| needs_repair | st-repair | ⚒ | | committed | q-good | ✓ |
| needs_docs | st-docs | ⌕ | | stale | q-warn | ↻ |
| rejected | st-rejected | ✕ | | failed | q-serious | ! |
| parked | st-parked | ⏸ | | dead | q-crit | ☠ |
| | | | | cancelled | muted | – |

Typography: `system-ui, -apple-system, "Segoe UI", sans-serif` everywhere; `font-variant-numeric: tabular-nums` on count columns, ids, and timestamps. Ids render in the mono stack (`ui-monospace, monospace`) since they are copy targets.

## 4. Global Surfaces

### Record Drawer (the P2 mechanism)

Every id string anywhere in the UI is a `RecordLink` — click opens the right-side drawer (420px, `Esc` closes, deep-linkable):

```text
┌ Drawer ────────────────────────────────┐
│ NODE-003  mechanism · active · strong ❄│   header: id, chips, frozen badge
│ "Collateral calls forced gilt sales…"  │   claim/summary text
│ ▸ Raw JSON (collapsed by default)      │   canonical latest record
│ ▸ History (n versions)                 │   timeline of appended versions
│ ▸ Proof history                        │   per verdict record: form answers
│     PR-014 pass(strong)  [form ▾]      │   as a compact enum grid + verdict
│ ▸ Trace                                │   nodes only: the docs/09 §3 chain
│     FRZ-002 → CD-000031 → PR-014 →     │   as a breadcrumb of RecordLinks
│     DOCSPACK → EU-001 → DOC-001 → raw  │
└────────────────────────────────────────┘
```

Sections render lazily from `/api/record/{id}` and `/api/trace/{node}`. Unknown id → inline "not found in index — index may be stale".

### Empty / error states

Every view defines its empty state (below). API errors render an inline retry card inside the affected container, never a blank pane; the polling loop backs off ×2 per consecutive failure (max 60s).

## 5. Views

### 5.1 Overview (`#/overview`, data: `/api/overview`, `/api/events?limit=10`)

```text
┌ Contract ──────────┐ ┌ MSA Checklist ─────────────┐ ┌ Dead letters ──────┐
│ ✓ accepted v1      │ │ ✓ MSA-1 question+thesis    │ │ WI-000041 ☠ V-PR-06│
│ fixed question …   │ │ ✓ MSA-2 spine edge         │ │ [copy requeue cmd] │
└────────────────────┘ │ ✗ MSA-6 open work on spine │ └────────────────────┘
┌ Queue matrix ──────────────────────────┐ │ …9 rows, each → filtered view │
│            queued claimed valid'd dead │ └────────────────────────────────┘
│ proof         3      2       1     1   │ ┌ Recent events ─────────────────┐
│ docs          1      0       0     0   │ │ 09:41 claim WI-000038 worker-2 │
│ compile       0      0       0     0   │ │ …           [view all →]      │
│ commit(view)  —      —       1     —   │ └────────────────────────────────┘
└────────────────────────────────────────┘
```

Every count is a link into the Queue view with filters pre-set; every MSA row links to the records it names. Empty state (fresh project): a setup checklist (init ✓ → spec build → accept → expand) with the CLI command for the next step shown copy-ready.

### 5.2 Logic Map (`#/map`, data: `/api/graph?lane=&layer=&state=`)

Cytoscape, breadthfirst layout per lane — lanes as horizontal swimlanes (BFS-MAIN top), layers left→right, `layer` as the level constraint. Deterministic layout: nodes ordered by node_id within a level so re-renders don't shuffle.

Node encoding (shape = node_type, fill = lifecycle_state, always + glyph):

```text
question ⬟ pentagon    thesis ◆ diamond      fact ● circle
mechanism ⬢ hexagon    definition ■ square   alternative ▲ triangle
frozen: double border + ❄ badge   claim_version>1: superscript v2
```

Edge encoding:

```text
supports    solid line, arrowhead →        strength strong: 2px
refutes     st-rejected color + ⊗ midpoint  strength conditional: 2px dashed
depends_on  dotted line, open arrowhead     unassessed: 1px hairline, muted
```

Controls row (one row above the canvas): lane filter, layer range, state multi-select, frozen-only toggle, **spine highlight** toggle (dims everything off-spine to 25% opacity; spine set from `/api/overview` MSA data), search box (id or claim substring — matches pan/flash), export PNG / JSON (client-side from cytoscape), fit/reset.

Interactions: hover → tooltip (id, claim, state, strength — 12px, surface card); click → Record Drawer; legend (states + shapes + edge styles) permanently docked bottom-left, collapsible. Performance target: smooth to 500 nodes; beyond that the UI forces a lane filter.

Empty state: "Graph is empty — commit a layer-0 proposal" + command.

### 5.3 Queue (`#/queue`, data: `/api/queue?queue=&status=`)

Tabs: `proof · docs · critic · compile · commit (derived)`. The `docs` tab groups its members by wave (one collapsible group per WV- id, its members and the wave status shown together — S2, docs/15); the `critic` tab lists critic_queue items (target_type=`wave`). Dead letters, when present, are pinned as a critical-tinted section above the table in every tab (a saturated dead letter shows its `detail.floor_met`).

```text
│ WI-000038  ◑ claimed  PT-EDGE-001-002 → EDGE-001-002  worker-2  ⏱ 11:32  a1 │
│ WI-000039  ⊘ blocked  PT-NODE-007                      —        blocked_by: │
│                                                                  WI-000035  │
columns: id · status chip · task → target (RecordLinks) · agent ·
         lease countdown (mm:ss, turns q-warn under 120s) · attempt ·
         blocked_by chips · actions
```

Actions per row: `Claim` (queued; prompts for agent name, remembered in localStorage) and `Release` (claimed/running) — the only queue writes (docs/10 §6). Dead rows show a copy-ready `paperproof queue requeue WI-…` command instead of a button. Commit tab is read-only (FIFO of validated items) with a copy-ready `commit apply` command per row. Filters serialize to the hash. Empty state per tab: "queue quiet ✓".

### 5.4 Evidence (`#/evidence`, data: `/api/evidence`)

Master-detail. Left: document list (title, source_type badge, citation_key, text-extracted indicator 📄/∅, EU count). Right: the selected document's EvidenceUnits as cards:

```text
┌ EU-001 · quote · supports · p.12 §3.2 ──────────────────────────┐
│ “LDI funds faced collateral calls exceeding their liquid …”     │
│ can cite for   ✓ LDI margin calls created acute liquidity …     │
│ cannot cite for ✕ all de-risking strategies create crises       │
│ bound to: NODE-001, NODE-004        scope: 2022 · UK            │
└──────────────────────────────────────────────────────────────────┘
```

`can/cannot_cite_for` render as good/critical-tinted boundary lists (with ✓/✕ glyphs). "Bound to" backlinks are computed from node `evidence_bindings` (index join). Toolbar: search (matcher-backed via `/api/evidence?q=` passthrough of `docs search`), direction filter, **orphans** toggle (EUs bound to nothing). A **Coverage** panel (data: `/api/coverage` — part of docs/07's amended HTTP surface) shows the S4 ledger line for a selected fact/mechanism node — angles, rounds, saturated flag, floor met — read-only, the same data as `docs coverage`. Empty state: "no documents — `paperproof docs ingest <file>`".

### 5.5 Compiler (`#/compiler`, data: `/api/compiler`)

```text
┌ Hero ─────────────────────────────────────────────┐
│  WRITING READY: NO   (dry run CDR-002 · GS-000012)│  good-green YES / muted NO
│  3 gaps open                                      │
└───────────────────────────────────────────────────┘
Gaps table      kind badge · target (RecordLink) · note · open item (WI link)
Section plan    section_id · role · node chips (RecordLinks)
Draft map       when present: per-section claim/evidence counts
Prose           tabs per ingested section; annotations rendered as inline chips
                — (claim: NODE-001) → state-tinted chip, (cite: EU-001) → accent
                chip; both are RecordLinks. Raw markdown toggle.
Audit           latest report: passed banner or findings table
                (kind badge · location · target · detail)
```

Empty state ladder: "no dry run yet" → "gaps open (n)" → "ready — draft map next" → prose tabs.

### 5.6 Events (`#/events`, auxiliary, data: `/api/events?after=`)

Reverse-chron table: time · op badge · work item (RecordLink) · from→to status · actor · detail (failed_rules render as critical chips). Filters: op, actor, work item. Infinite scroll by `after=QE-…` cursor. Reached from Overview; also linked from any status chip's tooltip ("show this item's events").

## 6. Component Inventory

All components are plain HTML + CSS classes + small JS behaviors (no framework). Contract = markup shape + data attributes; docs/11 M4 tests target `data-testid`.

```text
RecordLink      <a data-testid="rl" data-id>  mono id, opens drawer
StateChip       <span data-state>             glyph + label + tint (table §3)
StatusChip      <span data-status>            work-item variant
CountCard       Overview matrix cell          number (tabular-nums) + link
LeaseCountdown  <time data-expires>           mm:ss, ticks client-side
BlockedByChips  chip list of RecordLinks
GapBadge        <span data-gap-kind>          the 5 kinds, warning-tinted
BoundaryList    can/cannot_cite_for block     ✓/✕ rows
JsonView        collapsed <pre>, copy button
Timeline        version history rows
Banner          data-priority corruption|stale|contract
Legend          Logic Map dock
CopyCmd         <code> + copy button          the "UI suggests, CLI acts" device
```

`CopyCmd` is a deliberate design device: wherever the UI shows work it is not allowed to do (requeue, commit apply, unfreeze), it shows the exact CLI command copy-ready instead of a button — the gate discipline stays visible.

## 7. Accessibility and Quality Bar

```text
Contrast: body text ≥ 4.5:1; chip text uses ink tokens, never the tint color.
Never color-alone (P4): state = color + glyph everywhere, incl. the Logic Map.
Keyboard: left-nav 1–5, / focuses search, Esc closes drawer, Enter opens the
  focused RecordLink. Focus rings visible (2px accent).
Dark mode: selected tokens (§3), not an inversion; both modes CVD-validated.
No horizontal page scroll at ≥1024px; tables scroll inside their own container.
The six Overview questions must each be answerable without scrolling at 1280×800.
```

## 8. v1 Boundary and Later

```text
v1 (matches docs/10 §6)   everything in §2–§7 above; writes = claim, release,
                          db rebuild; no auth (localhost tool).
v1.1 candidates           requeue/unfreeze buttons (behind a confirm modal),
                          diff view between two snapshots, DocsRequest browser,
                          audit finding → one-click compile_queue routing.
v2 candidates             multi-project switcher, live SSE instead of polling,
                          advisor share links (read-only export bundle),
                          draft-vs-graph side-by-side reading mode.
```

## 9. Test Hooks (docs/11 M4)

```text
Endpoint tests    FastAPI TestClient over every /api route incl. filter params;
                  overview payload must answer the six questions from one call.
DOM smoke         static page served; data-testid presence for: banner slot,
                  five nav items, queue table, drawer skeleton.
Six-questions     an S7-shaped project fixture → /api/overview asserts: open
                  count, per-agent claims, blocked count, validated count,
                  frozen count, stale_index flag — the UI renders these fields
                  verbatim, so the API test is the behavior test.
Stale banner      touch a JSONL after db rebuild → /api/overview stale_index
                  =true → banner testid present in rendered page.
```
