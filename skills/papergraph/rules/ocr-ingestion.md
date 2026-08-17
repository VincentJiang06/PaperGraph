# OCR ingestion

## Decide whether OCR is needed

Use born-digital text directly. Use OCR only for a local `.png`, `.jpg`, `.jpeg`,
`.bmp`, or `.pdf` source whose text cannot be extracted reliably. PDF ingestion
is one page per request: set `IsPdf=true` and an explicit `PdfPageNumber`
(default 1; PaperGraph policy range 1..10,000). The dimension-safe live probe is
image-only; use offline provider artifacts or pre-rendered pages for normalized
PDF evidence. Never submit an arbitrary remote `ImageUrl`.

## Provider boundary

- Fixed endpoint: `https://ocr.tencentcloudapi.com/`
- Fixed version: `2018-11-19`
- Default action: `GeneralBasicOCR`
- `GeneralAccurateOCR` is allowed only as a separately approved, bounded repair;
  the live probe rejects it.
- Input is local bytes encoded as `ImageBase64`. The encoded payload must be at
  most 10,000,000 bytes.
- Credentials come from process memory/environment and are never written to the
  skill, artifacts, diagnostics, or command arguments. Accepted names are
  `TENCENTCLOUD_SECRET_ID` and `TENCENTCLOUD_SECRET_KEY` (preferred), with
  `TENCENT_SECRET_ID` and `TENCENT_SECRET_KEY` as fallback aliases. If both name
  sets are present, the `TENCENTCLOUD_*` value wins. `--credentials-env-file`
  parses these keys without sourcing or evaluating the file.

`prepare_signed_request` serializes the request body once and signs those exact
bytes. `transmit_signed_request` refuses any changed body before calling the
transport. A provider `Response.Error` remains an error even when HTTP status is
200; preserve its code and request ID.

## Retry and uncertainty

Only an explicit provider throttling/availability code is retryable, and total
attempts are bounded to three. Do not switch actions while retrying. Pre-submit
transport failure is `not_submitted`. A timeout after possible submission is
`outcome_unknown`; do not automatically issue another paid call.

## Normalization

Require a provider request ID, a detections list, finite confidence in 0..100,
and exactly four clockwise, in-bounds, non-self-intersecting polygon points.
Normalize confidence to 0..1 and coordinates to image-relative values. A positive
`ItemPolygon` may replace an empty polygon only at zero provider angle; otherwise
coordinate space is ambiguous and normalization fails.

Sort elements by page position, deduplicate identical observations, preserve
Unicode, and derive each element ID from provider run ID, source ID, and canonical
observation. Replaying the same run is stable; a different provider run produces
disjoint IDs.

## Artifacts and output safety

Replay/live normalization writes atomically:

```text
raw_response.json
source.json
manifest.json
source.txt
```

`source.txt` intentionally contains recognized text for downstream research;
default CLI stdout contains only bounded metadata. Never print credentials,
authorization, request body, or recognized text. If a completed probe returns a
coordinate space incompatible with its local image, archive raw call evidence and
mark normalization deferred; do not repair geometry silently or emit `source.json`.

Live acceptance requires `OCR_LIVE_CONFIRM=ONE_BASIC_CALL`, Basic action, one
local image, `max_attempts=1`, and an output directory outside the skill.
