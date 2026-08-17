#!/usr/bin/env python3
"""Tencent OCR ingestion with fail-closed normalization and replay artifacts."""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import hashlib
import hmac
import json
import math
import os
import re
import socket
import struct
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable, Mapping


HOST = "ocr.tencentcloudapi.com"
ENDPOINT = f"https://{HOST}/"
API_VERSION = "2018-11-19"
BASIC_ACTION = "GeneralBasicOCR"
ACCURATE_ACTION = "GeneralAccurateOCR"
MAX_ENCODED_BYTES = 10_000_000
MAX_PDF_PAGE_NUMBER = 10_000
SCHEMA_VERSION = "papergraph-ocr-source/1.0"

_CONTENT_TYPE = "application/json; charset=utf-8"
_SERVICE = "ocr"
_ALLOWED_ACTIONS = {BASIC_ACTION, ACCURATE_ACTION}
_ALLOWED_SUFFIXES = {".png", ".jpg", ".jpeg", ".bmp", ".pdf"}
_RETRYABLE_PROVIDER_CODES = {
    "RequestLimitExceeded",
    "RequestLimitExceeded.UinLimitExceeded",
    "RequestLimitExceeded.GlobalRegionUinLimitExceeded",
    "ResourceUnavailable",
}


class OCRContractError(RuntimeError):
    """Public OCR failure carrying provider-safe diagnostics."""

    def __init__(
        self,
        message: str,
        *,
        code: str,
        request_id: str | None = None,
        outcome: str = "failed",
    ) -> None:
        super().__init__(message)
        self.code = code
        self.request_id = request_id
        self.outcome = outcome


class TransportFailure(RuntimeError):
    """Transport failure annotated with whether request submission may have occurred."""

    def __init__(self, message: str, *, submitted: bool) -> None:
        super().__init__(message)
        self.submitted = submitted


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _hmac_sha256(key: bytes, message: str) -> bytes:
    return hmac.new(key, message.encode("utf-8"), hashlib.sha256).digest()


def _require_nonempty(value: str, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise OCRContractError(f"{field} is required", code="MISSING_CREDENTIAL", outcome="not_submitted")
    return value


def validate_encoded_size(encoded: bytes) -> bool:
    """Accept the conservative provider boundary and reject before network access."""

    if not isinstance(encoded, bytes):
        raise OCRContractError("encoded payload must be bytes", code="INVALID_ENCODED_PAYLOAD", outcome="not_submitted")
    if len(encoded) > MAX_ENCODED_BYTES:
        raise OCRContractError(
            f"encoded payload exceeds {MAX_ENCODED_BYTES} bytes",
            code="ENCODED_SIZE_LIMIT",
            outcome="not_submitted",
        )
    return True


def prepare_signed_request(
    image_base64: str,
    *,
    secret_id: str,
    secret_key: str,
    timestamp: int,
    action: str = BASIC_ACTION,
    is_pdf: bool = False,
    pdf_page_number: int = 1,
) -> dict[str, Any]:
    """Build one TC3-HMAC-SHA256 request; ``body`` is the exact signed byte string."""

    _require_nonempty(secret_id, "secret_id")
    _require_nonempty(secret_key, "secret_key")
    if action not in _ALLOWED_ACTIONS:
        raise OCRContractError("unsupported OCR action", code="UNSUPPORTED_ACTION", outcome="not_submitted")
    if not isinstance(image_base64, str) or not image_base64:
        raise OCRContractError("ImageBase64 is required", code="EMPTY_IMAGE", outcome="not_submitted")

    if isinstance(pdf_page_number, bool) or not isinstance(pdf_page_number, int) or not 1 <= pdf_page_number <= MAX_PDF_PAGE_NUMBER:
        raise OCRContractError(
            f"pdf_page_number must be between 1 and {MAX_PDF_PAGE_NUMBER}",
            code="INVALID_PDF_PAGE",
            outcome="not_submitted",
        )
    payload: dict[str, Any] = {"ImageBase64": image_base64}
    if is_pdf:
        payload["IsPdf"] = True
        payload["PdfPageNumber"] = pdf_page_number
    elif pdf_page_number != 1:
        raise OCRContractError(
            "pdf_page_number applies only to PDF input",
            code="INVALID_PDF_PAGE",
            outcome="not_submitted",
        )
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    validate_encoded_size(image_base64.encode("ascii"))
    payload_hash = _sha256(body)
    canonical_headers = f"content-type:{_CONTENT_TYPE}\nhost:{HOST}\n"
    signed_headers = "content-type;host"
    canonical_request = "\n".join(
        ["POST", "/", "", canonical_headers, signed_headers, payload_hash]
    )
    date = dt.datetime.fromtimestamp(int(timestamp), tz=dt.timezone.utc).strftime("%Y-%m-%d")
    credential_scope = f"{date}/{_SERVICE}/tc3_request"
    string_to_sign = "\n".join(
        ["TC3-HMAC-SHA256", str(int(timestamp)), credential_scope, _sha256(canonical_request.encode("utf-8"))]
    )
    secret_date = _hmac_sha256(("TC3" + secret_key).encode("utf-8"), date)
    secret_service = _hmac_sha256(secret_date, _SERVICE)
    secret_signing = _hmac_sha256(secret_service, "tc3_request")
    signature = hmac.new(secret_signing, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()
    authorization = (
        f"TC3-HMAC-SHA256 Credential={secret_id}/{credential_scope}, "
        f"SignedHeaders={signed_headers}, Signature={signature}"
    )
    return {
        "url": ENDPOINT,
        "method": "POST",
        "body": body,
        "body_sha256": payload_hash,
        "headers": {
            "Authorization": authorization,
            "Content-Type": _CONTENT_TYPE,
            "Host": HOST,
            "X-TC-Action": action,
            "X-TC-Timestamp": str(int(timestamp)),
            "X-TC-Version": API_VERSION,
        },
    }


def transmit_signed_request(
    request: Mapping[str, Any],
    transport: Callable[[Mapping[str, Any]], Mapping[str, Any]],
    *,
    body: bytes | None = None,
) -> dict[str, Any]:
    """Transmit only the exact bytes covered by the request signature."""

    signed_body = request.get("body")
    transmitted_body = signed_body if body is None else body
    expected_hash = request.get("body_sha256")
    if not isinstance(signed_body, bytes) or not isinstance(transmitted_body, bytes):
        raise OCRContractError("signed request body is invalid", code="INVALID_SIGNED_REQUEST", outcome="not_submitted")
    if transmitted_body != signed_body or expected_hash != _sha256(transmitted_body):
        raise OCRContractError(
            "transmitted body differs from signed body",
            code="SIGNATURE_MISMATCH",
            outcome="not_submitted",
        )
    outbound = dict(request)
    outbound["body"] = transmitted_body
    response = transport(outbound)
    if not isinstance(response, Mapping):
        raise OCRContractError("provider response must be an object", code="MALFORMED_RESPONSE")
    return dict(response)


def request_ocr(
    image_base64: str,
    *,
    secret_id: str,
    secret_key: str,
    timestamp: int,
    transport: Callable[[Mapping[str, Any]], Mapping[str, Any]],
    action: str = BASIC_ACTION,
    max_attempts: int = 1,
    sleep: Callable[[float], None] | None = None,
    is_pdf: bool = False,
    pdf_page_number: int = 1,
) -> dict[str, Any]:
    """Submit OCR with retries limited to explicit provider throttling errors."""

    _require_nonempty(secret_id, "secret_id")
    _require_nonempty(secret_key, "secret_key")
    if not isinstance(max_attempts, int) or not 1 <= max_attempts <= 3:
        raise OCRContractError("max_attempts must be between 1 and 3", code="INVALID_MAX_ATTEMPTS", outcome="not_submitted")
    validate_encoded_size(image_base64.encode("ascii"))
    sleeper = sleep or time.sleep

    for attempt in range(1, max_attempts + 1):
        signed = prepare_signed_request(
            image_base64,
            secret_id=secret_id,
            secret_key=secret_key,
            timestamp=timestamp,
            action=action,
            is_pdf=is_pdf,
            pdf_page_number=pdf_page_number,
        )
        try:
            envelope = transmit_signed_request(signed, transport)
        except TransportFailure as exc:
            outcome = "outcome_unknown" if exc.submitted else "not_submitted"
            raise OCRContractError("OCR transport failed", code="TRANSPORT_FAILURE", outcome=outcome) from exc

        response = envelope.get("Response")
        if not isinstance(response, Mapping):
            raise OCRContractError("Response is missing or malformed", code="MALFORMED_RESPONSE")
        request_id = response.get("RequestId") if isinstance(response.get("RequestId"), str) else None
        provider_error = response.get("Error")
        if provider_error is not None:
            if not isinstance(provider_error, Mapping) or not isinstance(provider_error.get("Code"), str):
                raise OCRContractError("Response.Error is malformed", code="MALFORMED_RESPONSE", request_id=request_id)
            code = provider_error["Code"]
            if code in _RETRYABLE_PROVIDER_CODES and attempt < max_attempts:
                sleeper(min(0.25 * attempt, 0.5))
                continue
            raise OCRContractError(
                "Tencent OCR provider rejected the request",
                code=code,
                request_id=request_id,
                outcome="provider_error",
            )
        if not request_id:
            raise OCRContractError("Response.RequestId is missing", code="MALFORMED_RESPONSE")
        return {
            "request_id": request_id,
            "action": action,
            "attempts": attempt,
            "envelope": envelope,
        }

    raise OCRContractError("retry budget exhausted", code="RETRY_EXHAUSTED", outcome="provider_error")


def _read_local_file(path: str | Path) -> tuple[Path, bytes]:
    local = Path(path)
    if not local.is_file():
        raise OCRContractError("local source file does not exist", code="FILE_NOT_FOUND", outcome="not_submitted")
    if local.suffix.lower() not in _ALLOWED_SUFFIXES:
        raise OCRContractError("unsupported local source type", code="UNSUPPORTED_MIME", outcome="not_submitted")
    data = local.read_bytes()
    if not data:
        raise OCRContractError("local source file is empty", code="EMPTY_IMAGE", outcome="not_submitted")
    return local, data


def request_file(
    path: str | Path,
    *,
    credentials: Mapping[str, str],
    transport: Callable[[Mapping[str, Any]], Mapping[str, Any]],
    timestamp: int,
    max_attempts: int = 1,
    action: str = BASIC_ACTION,
    pdf_page_number: int = 1,
) -> dict[str, Any]:
    """Read and submit one supported local file as ImageBase64."""

    local, data = _read_local_file(path)
    secret_id = credentials.get("secret_id", "")
    secret_key = credentials.get("secret_key", "")
    _require_nonempty(secret_id, "secret_id")
    _require_nonempty(secret_key, "secret_key")
    encoded = base64.b64encode(data)
    validate_encoded_size(encoded)
    return request_ocr(
        encoded.decode("ascii"),
        secret_id=secret_id,
        secret_key=secret_key,
        timestamp=timestamp,
        transport=transport,
        action=action,
        max_attempts=max_attempts,
        is_pdf=local.suffix.lower() == ".pdf",
        pdf_page_number=pdf_page_number,
    )


def _finite_number(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise OCRContractError(f"{field} must be a finite number", code="MALFORMED_RESPONSE")
    return float(value)


def _segments_intersect(a: tuple[float, float], b: tuple[float, float], c: tuple[float, float], d: tuple[float, float]) -> bool:
    def orient(p: tuple[float, float], q: tuple[float, float], r: tuple[float, float]) -> float:
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])

    return orient(a, b, c) * orient(a, b, d) < 0 and orient(c, d, a) * orient(c, d, b) < 0


def _normalize_polygon(
    polygon: Any,
    *,
    image_width: int,
    image_height: int,
) -> list[list[float]]:
    if not isinstance(polygon, list) or len(polygon) != 4:
        raise OCRContractError("Polygon must contain exactly four points", code="INVALID_GEOMETRY")
    points: list[tuple[float, float]] = []
    for index, point in enumerate(polygon):
        if not isinstance(point, Mapping):
            raise OCRContractError(f"Polygon[{index}] must be an object", code="INVALID_GEOMETRY")
        x = _finite_number(point.get("X"), f"Polygon[{index}].X")
        y = _finite_number(point.get("Y"), f"Polygon[{index}].Y")
        if not 0 <= x <= image_width or not 0 <= y <= image_height:
            raise OCRContractError(f"Polygon[{index}] is out of image bounds", code="INVALID_GEOMETRY")
        points.append((x, y))

    if _segments_intersect(points[0], points[1], points[2], points[3]) or _segments_intersect(points[1], points[2], points[3], points[0]):
        raise OCRContractError("Polygon self-intersects", code="INVALID_GEOMETRY")
    twice_area = sum(
        points[i][0] * points[(i + 1) % 4][1] - points[(i + 1) % 4][0] * points[i][1]
        for i in range(4)
    )
    if twice_area <= 0:
        raise OCRContractError("Polygon must be non-zero and clockwise in image coordinates", code="INVALID_GEOMETRY")
    return [[round(x / image_width, 12), round(y / image_height, 12)] for x, y in points]


def _item_polygon_as_points(item: Any) -> list[dict[str, float]]:
    if not isinstance(item, Mapping):
        raise OCRContractError("ItemPolygon is required when Polygon is empty", code="INVALID_GEOMETRY")
    x = _finite_number(item.get("X"), "ItemPolygon.X")
    y = _finite_number(item.get("Y"), "ItemPolygon.Y")
    width = _finite_number(item.get("Width"), "ItemPolygon.Width")
    height = _finite_number(item.get("Height"), "ItemPolygon.Height")
    if width <= 0 or height <= 0:
        raise OCRContractError("ItemPolygon dimensions must be positive", code="INVALID_GEOMETRY")
    return [
        {"X": x, "Y": y},
        {"X": x + width, "Y": y},
        {"X": x + width, "Y": y + height},
        {"X": x, "Y": y + height},
    ]


def normalize_response(
    envelope: Mapping[str, Any],
    *,
    image_width: int,
    image_height: int,
    provider_run_id: str,
    source_id: str,
) -> dict[str, Any]:
    """Normalize one provider envelope into a strict, replay-stable source artifact."""

    if not isinstance(image_width, int) or image_width <= 0 or not isinstance(image_height, int) or image_height <= 0:
        raise OCRContractError("image dimensions must be positive integers", code="INVALID_IMAGE_DIMENSIONS")
    if not provider_run_id or not source_id:
        raise OCRContractError("provider_run_id and source_id are required", code="INVALID_IDENTIFIER")
    response = envelope.get("Response") if isinstance(envelope, Mapping) else None
    if not isinstance(response, Mapping):
        raise OCRContractError("Response is missing or malformed", code="MALFORMED_RESPONSE")
    if response.get("Error") is not None:
        provider_error = response.get("Error")
        code = provider_error.get("Code") if isinstance(provider_error, Mapping) else "MALFORMED_RESPONSE"
        request_id = response.get("RequestId") if isinstance(response.get("RequestId"), str) else None
        raise OCRContractError("provider error cannot be normalized", code=str(code), request_id=request_id)
    detections = response.get("TextDetections")
    if not isinstance(detections, list):
        raise OCRContractError("TextDetections must be a list", code="MALFORMED_RESPONSE")
    request_id = response.get("RequestId")
    if not isinstance(request_id, str) or not request_id:
        raise OCRContractError("RequestId must be a non-empty string", code="MALFORMED_RESPONSE")
    angle = _finite_number(response.get("Angle", 0.0), "Angle")

    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, detection in enumerate(detections):
        if not isinstance(detection, Mapping):
            raise OCRContractError(f"TextDetections[{index}] must be an object", code="MALFORMED_RESPONSE")
        text = detection.get("DetectedText")
        if not isinstance(text, str):
            raise OCRContractError(f"TextDetections[{index}].DetectedText must be a string", code="MALFORMED_RESPONSE")
        confidence_raw = _finite_number(detection.get("Confidence"), "Confidence")
        if not 0 <= confidence_raw <= 100:
            raise OCRContractError("Confidence must be between 0 and 100", code="MALFORMED_RESPONSE")
        polygon = detection.get("Polygon")
        if not polygon:
            if angle != 0:
                raise OCRContractError(
                    "Polygon fallback has ambiguous coordinate space at nonzero angle",
                    code="INVALID_GEOMETRY",
                )
            polygon = _item_polygon_as_points(detection.get("ItemPolygon"))
        polygon_norm = _normalize_polygon(polygon, image_width=image_width, image_height=image_height)
        confidence = round(confidence_raw / 100.0, 12)
        identity = json.dumps(
            {"text": text, "confidence": confidence, "polygon_norm": polygon_norm},
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        if identity in seen:
            continue
        seen.add(identity)
        element_id = "ocr-" + hashlib.sha256(
            f"{provider_run_id}\0{source_id}\0{identity}".encode("utf-8")
        ).hexdigest()[:24]
        normalized.append(
            {"id": element_id, "text": text, "confidence": confidence, "polygon_norm": polygon_norm}
        )

    normalized.sort(
        key=lambda element: (
            min(point[1] for point in element["polygon_norm"]),
            min(point[0] for point in element["polygon_norm"]),
            element["text"],
            element["id"],
        )
    )
    normalized_observation = {
        "request_id": request_id,
        "language": response.get("Language") if isinstance(response.get("Language"), str) else None,
        "angle": angle,
        "elements": normalized,
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "source_id": source_id,
        "provider_run_id": provider_run_id,
        "image": {"width": image_width, "height": image_height},
        "provider": {
            "name": "tencent-ocr",
            "action": str(envelope.get("_papergraph_action", BASIC_ACTION)),
            "api_version": API_VERSION,
            "request_id": request_id,
            "language": response.get("Language") if isinstance(response.get("Language"), str) else None,
            "angle": angle,
        },
        "normalized_observation_sha256": _sha256(
            json.dumps(
                normalized_observation,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ),
        "elements": normalized,
    }


def _canonical_json(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def _write_artifact_bundle(
    envelope: Mapping[str, Any],
    output_dir: str | Path,
    *,
    image_width: int,
    image_height: int,
    provider_run_id: str,
    source_id: str,
) -> dict[str, Any]:
    output = Path(output_dir)
    source = normalize_response(
        envelope,
        image_width=image_width,
        image_height=image_height,
        provider_run_id=provider_run_id,
        source_id=source_id,
    )
    raw_bytes = _canonical_json(envelope)
    source_bytes = _canonical_json(source)
    text_bytes = ("\n".join(element["text"] for element in source["elements"]) + ("\n" if source["elements"] else "")).encode("utf-8")
    manifest = {
        "schema_version": "papergraph-ocr-manifest/1.0",
        "source_id": source_id,
        "provider_run_id": provider_run_id,
        "request_id": source["provider"]["request_id"],
        "line_count": len(source["elements"]),
        "artifacts": {
            "raw_response.json": _sha256(raw_bytes),
            "source.json": _sha256(source_bytes),
            "source.txt": _sha256(text_bytes),
        },
    }
    for name, data in (
        ("raw_response.json", raw_bytes),
        ("source.json", source_bytes),
        ("source.txt", text_bytes),
        ("manifest.json", _canonical_json(manifest)),
    ):
        _atomic_write(output / name, data)
    return {"source": source, "manifest": manifest}


def replay_response(
    response_path: str | Path,
    output_dir: str | Path,
    *,
    image_width: int,
    image_height: int,
    provider_run_id: str,
    source_id: str,
) -> dict[str, Any]:
    """Replay an archived response without network access."""

    try:
        envelope = json.loads(Path(response_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise OCRContractError("response archive is unreadable JSON", code="INVALID_REPLAY_INPUT", outcome="not_submitted") from exc
    if not isinstance(envelope, Mapping):
        raise OCRContractError("response archive must contain an object", code="INVALID_REPLAY_INPUT", outcome="not_submitted")
    return _write_artifact_bundle(
        envelope,
        output_dir,
        image_width=image_width,
        image_height=image_height,
        provider_run_id=provider_run_id,
        source_id=source_id,
    )


def _image_dimensions(path: Path, data: bytes) -> tuple[int, int]:
    suffix = path.suffix.lower()
    if suffix == ".png" and data[:8] == b"\x89PNG\r\n\x1a\n" and len(data) >= 24:
        return struct.unpack(">II", data[16:24])
    if suffix == ".bmp" and data[:2] == b"BM" and len(data) >= 26:
        width, height = struct.unpack("<ii", data[18:26])
        return abs(width), abs(height)
    if suffix in {".jpg", ".jpeg"} and data[:2] == b"\xff\xd8":
        offset = 2
        while offset + 9 < len(data):
            if data[offset] != 0xFF:
                offset += 1
                continue
            marker = data[offset + 1]
            if marker in {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}:
                height, width = struct.unpack(">HH", data[offset + 5 : offset + 9])
                return width, height
            if marker in {0xD8, 0xD9}:
                offset += 2
                continue
            length = struct.unpack(">H", data[offset + 2 : offset + 4])[0]
            if length < 2:
                break
            offset += 2 + length
    raise OCRContractError(
        "image dimensions could not be read locally; render PDF pages or use replay with explicit dimensions",
        code="IMAGE_DIMENSIONS_UNAVAILABLE",
        outcome="not_submitted",
    )


def run_live_probe(
    image_path: str | Path,
    output_dir: str | Path,
    *,
    action: str,
    confirmation: str | None,
    credentials: Mapping[str, str],
    transport: Callable[[Mapping[str, Any]], Mapping[str, Any]],
    timestamp: int,
) -> dict[str, Any]:
    """Run exactly one confirmed GeneralBasicOCR request and archive safe evidence."""

    if confirmation != "ONE_BASIC_CALL":
        raise OCRContractError("live probe confirmation is required", code="LIVE_CONFIRMATION_REQUIRED", outcome="not_submitted")
    if action != BASIC_ACTION:
        raise OCRContractError("live probe permits GeneralBasicOCR only", code="LIVE_BASIC_ONLY", outcome="not_submitted")
    local, data = _read_local_file(image_path)
    if local.suffix.lower() == ".pdf":
        raise OCRContractError("live probe requires a dimension-readable image, not PDF", code="LIVE_IMAGE_ONLY", outcome="not_submitted")
    width, height = _image_dimensions(local, data)
    started = time.monotonic()
    result = request_file(
        local,
        credentials=credentials,
        transport=transport,
        timestamp=timestamp,
        max_attempts=1,
        action=BASIC_ACTION,
    )
    latency_ms = round((time.monotonic() - started) * 1000, 3)
    envelope = dict(result["envelope"])
    envelope["_papergraph_action"] = BASIC_ACTION
    request_id = result["request_id"]
    source_id = "source-" + _sha256(data)[:20]
    provider_run_id = "tencent-basic-" + request_id
    try:
        bundle = _write_artifact_bundle(
            envelope,
            output_dir,
            image_width=width,
            image_height=height,
            provider_run_id=provider_run_id,
            source_id=source_id,
        )
    except OCRContractError as exc:
        if exc.code != "INVALID_GEOMETRY":
            raise
        # An injected/offline transport can return coordinates from a canvas
        # unrelated to its tiny placeholder image. Preserve the paid-call
        # evidence, but never repair or accept those coordinates as normalized.
        raw_bytes = _canonical_json(envelope)
        deferred_manifest = {
            "schema_version": "papergraph-ocr-probe/1.0",
            "source_id": source_id,
            "provider_run_id": provider_run_id,
            "request_id": request_id,
            "normalization_status": "deferred_invalid_geometry",
            "raw_response_sha256": _sha256(raw_bytes),
        }
        _atomic_write(Path(output_dir) / "raw_response.json", raw_bytes)
        _atomic_write(Path(output_dir) / "manifest.json", _canonical_json(deferred_manifest))
        return {
            "status": "normalization_deferred",
            "action": BASIC_ACTION,
            "request_id": request_id,
            "calls_made": 1,
            "latency_ms": latency_ms,
            "encoded_bytes": len(base64.b64encode(data)),
            "line_count": None,
            "provider_run_id": provider_run_id,
            "source_id": source_id,
            "output_dir": str(Path(output_dir).resolve()),
        }
    return {
        "status": "ok",
        "action": BASIC_ACTION,
        "request_id": request_id,
        "calls_made": 1,
        "latency_ms": latency_ms,
        "encoded_bytes": len(base64.b64encode(data)),
        "line_count": bundle["manifest"]["line_count"],
        "provider_run_id": provider_run_id,
        "source_id": source_id,
        "output_dir": str(Path(output_dir).resolve()),
    }


def _urllib_transport(request_data: Mapping[str, Any]) -> dict[str, Any]:
    headers = request_data.get("headers")
    body = request_data.get("body")
    if not isinstance(headers, Mapping) or not isinstance(body, bytes):
        raise TransportFailure("invalid local request", submitted=False)
    request = urllib.request.Request(
        str(request_data.get("url", ENDPOINT)),
        data=body,
        headers={str(key): str(value) for key, value in headers.items()},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = response.read()
    except socket.timeout as exc:
        raise TransportFailure("read timeout", submitted=True) from exc
    except urllib.error.HTTPError as exc:
        payload = exc.read()
    except urllib.error.URLError as exc:
        if isinstance(exc.reason, socket.timeout):
            raise TransportFailure("read timeout", submitted=True) from exc
        raise TransportFailure("connection failed before confirmed submission", submitted=False) from exc
    try:
        decoded = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise TransportFailure("provider returned invalid JSON", submitted=True) from exc
    if not isinstance(decoded, dict):
        raise TransportFailure("provider returned a non-object JSON value", submitted=True)
    return decoded


def _credentials_from_environment(environment: Mapping[str, str] | None = None) -> dict[str, str]:
    """Read Tencent's canonical names first, with shorter aliases as fallback."""

    values = os.environ if environment is None else environment
    secret_id = values["TENCENTCLOUD_SECRET_ID"] if "TENCENTCLOUD_SECRET_ID" in values else values.get("TENCENT_SECRET_ID", "")
    secret_key = values["TENCENTCLOUD_SECRET_KEY"] if "TENCENTCLOUD_SECRET_KEY" in values else values.get("TENCENT_SECRET_KEY", "")
    return {
        "secret_id": secret_id,
        "secret_key": secret_key,
    }


def _credentials_from_dotenv(path: str | Path) -> dict[str, str]:
    """Parse credential keys from a dotenv file without evaluating shell syntax."""

    wanted = {
        "TENCENTCLOUD_SECRET_ID",
        "TENCENTCLOUD_SECRET_KEY",
        "TENCENT_SECRET_ID",
        "TENCENT_SECRET_KEY",
    }
    parsed: dict[str, str] = {}
    try:
        lines = Path(path).read_text(encoding="utf-8-sig").splitlines()
    except OSError as exc:
        raise OCRContractError("credential env file is unreadable", code="DOTENV_UNREADABLE", outcome="not_submitted") from exc
    for line_number, raw in enumerate(lines, 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        if "=" not in line:
            raise OCRContractError(
                f"credential env file has malformed line {line_number}",
                code="DOTENV_MALFORMED",
                outcome="not_submitted",
            )
        key, value = line.split("=", 1)
        key = key.strip()
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
            raise OCRContractError(
                f"credential env file has invalid key at line {line_number}",
                code="DOTENV_MALFORMED",
                outcome="not_submitted",
            )
        if key not in wanted:
            continue
        if key in parsed:
            raise OCRContractError(
                f"credential env file repeats {key}",
                code="DOTENV_DUPLICATE_KEY",
                outcome="not_submitted",
            )
        value = value.strip()
        if value[:1] in {"'", '"'}:
            quote = value[0]
            if len(value) < 2 or value[-1] != quote:
                raise OCRContractError(
                    f"credential env file has unmatched quote at line {line_number}",
                    code="DOTENV_MALFORMED",
                    outcome="not_submitted",
                )
            value = value[1:-1]
        elif any(character.isspace() for character in value):
            raise OCRContractError(
                f"credential env file has unquoted whitespace at line {line_number}",
                code="DOTENV_MALFORMED",
                outcome="not_submitted",
            )
        parsed[key] = value
    return _credentials_from_environment(parsed)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="PaperGraph OCR ingestion")
    subparsers = parser.add_subparsers(dest="command", required=True)
    replay = subparsers.add_parser("replay", help="normalize an archived Tencent response")
    replay.add_argument("--response", required=True)
    replay.add_argument("--output-dir", required=True)
    replay.add_argument("--image-width", required=True, type=int)
    replay.add_argument("--image-height", required=True, type=int)
    replay.add_argument("--provider-run-id", required=True)
    replay.add_argument("--source-id", required=True)
    live = subparsers.add_parser("live-probe", help="run one confirmed GeneralBasicOCR request")
    live.add_argument("--image", required=True)
    live.add_argument("--output-dir", required=True)
    live.add_argument("--action", default=BASIC_ACTION, choices=sorted(_ALLOWED_ACTIONS))
    live.add_argument(
        "--credentials-env-file",
        help="strict dotenv file; TENCENTCLOUD_* names take precedence over TENCENT_* aliases",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "replay":
            result = replay_response(
                args.response,
                args.output_dir,
                image_width=args.image_width,
                image_height=args.image_height,
                provider_run_id=args.provider_run_id,
                source_id=args.source_id,
            )
            summary = {
                "status": "ok",
                "mode": "replay",
                "request_id": result["manifest"]["request_id"],
                "line_count": result["manifest"]["line_count"],
                "output_dir": str(Path(args.output_dir).resolve()),
            }
        else:
            summary = run_live_probe(
                args.image,
                args.output_dir,
                action=args.action,
                confirmation=os.environ.get("OCR_LIVE_CONFIRM"),
                credentials=(
                    _credentials_from_dotenv(args.credentials_env_file)
                    if args.credentials_env_file
                    else _credentials_from_environment()
                ),
                transport=_urllib_transport,
                timestamp=int(time.time()),
            )
    except OCRContractError as exc:
        print(
            json.dumps(
                {"status": "error", "code": exc.code, "outcome": exc.outcome, "request_id": exc.request_id},
                sort_keys=True,
            ),
            file=os.sys.stderr,
        )
        return 2
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
