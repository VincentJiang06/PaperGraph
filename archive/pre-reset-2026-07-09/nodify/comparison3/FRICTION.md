# nd friction surfaced by the aggressive-eval pilot (T1 tree, Opus, 2026-07-09)

The pilot built a clean aggressive tree (7 vp / 14 claims / 8 adversarial / 12 DOC /
`nd check` 0-0 / grounding 1.0) but surfaced 5 `nd` friction points. None blocking; all
worked around. Candidate roadmap items.

1. **Budget flag/key mismatch (FIXED in skill+prompt).** Docs said `--budget depth=k
   width=k open_claims=k`; nd wants **one `--budget k=v` per key** and keys are
   `max_depth/max_children/max_open_claims` (session.v1 schema). Fixed the skill,
   PROMPT_tree, and this run's dispatch. *Roadmap:* accept doc-named aliases, or make the
   error name the legal keys.

2. **No in-CLI root reset / "first add = root".** Root is fixed at init (from
   `--question`); the first `nd add` is the sole root viewpoint; a second root-add errors
   `root already exists`, and the root is non-revisable. The pilot mis-scoped its first
   add and had to `rm -rf sessions/cmp` + re-init. *Roadmap:* `init`/`add` output should
   hint "first add = root question"; consider a guarded `nd reset-root`.

3. **Claims can't be added directly under a viewpoint.** `nd add --kind claim` under a
   viewpoint errors `children of a viewpoint are viewpoints`; correct path is
   add-viewpoint-then-`nd promote`. Documented in the skill now; *roadmap:* say so in
   `add --help`.

4. **`nd tree` omits `orientation`** (and synthesis/promotion fields), so adversarial
   coverage is invisible from `tree` alone — only via `nd show`. Easy to misread as "no
   adversarial branches." *Roadmap:* surface an orientation marker in `tree`.

5. **Ingest success envelope shape.** doc_id was not where the author parsed it
   (`data.doc.doc_id` / `data.doc_id` both None though ingest succeeded); had to recover
   via `nd docs for-node`. *Roadmap:* document the exact ingest success envelope (and/or
   put doc_id at a stable top-level path).

## Added by the 5-topic scale-up (2026-07-09)

6. **`nd docs for-node <id>` returns empty even when bindings exist** (flagged
   independently by 2 cold-resume probers on 2 different sessions). The doc→node linkage
   is actually present — in the synthesis `based_on.evidence` arrays and the `bindings`
   field of `docs/index.jsonl` — but the `for-node` binding table surfaces nothing, so a
   fresh agent relying on `for-node` for provenance would wrongly conclude a node is
   unsourced. Provenance is fully recoverable via `nd show` / the docs index. *Roadmap:*
   fix `for-node` to read the same binding source, or document that it's not the
   provenance path.

Also (harness, already fixed): `dossier.py` treated evidence `url` as required; when an
author left `url:null` and pointed by `doc_id`, evidence rendered blank (T2 tree lost all
45 evidence URLs) — now resolved via the docs index (`doc_id → url/title`).
Note: the aggressive skill's budget-key fix held — all 4 new tree authors used
`--budget max_depth/max_children/max_open_claims` correctly with no budget friction.
