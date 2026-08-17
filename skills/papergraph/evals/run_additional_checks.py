#!/usr/bin/env python3
"""Offline compatibility checks added after the immutable 24-case RED baseline."""

from __future__ import annotations

import base64
import json
import sys
import tempfile
from pathlib import Path
from typing import Any


SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT))

from scripts import ocr_ingest  # noqa: E402


class RecordingTransport:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def __call__(self, request: dict[str, Any]) -> dict[str, Any]:
        self.calls.append(request)
        return {"Response": {"TextDetections": [], "Angle": 0, "RequestId": "offline-pdf-request"}}


def test_credentials_precedence_and_zero_leak() -> None:
    primary_id = "PRIMARY_ID_DO_NOT_PRINT"
    primary_key = "PRIMARY_KEY_DO_NOT_PRINT"
    alias_id = "ALIAS_ID_DO_NOT_PRINT"
    alias_key = "ALIAS_KEY_DO_NOT_PRINT"
    selected = ocr_ingest._credentials_from_environment(
        {
            "TENCENTCLOUD_SECRET_ID": primary_id,
            "TENCENTCLOUD_SECRET_KEY": primary_key,
            "TENCENT_SECRET_ID": alias_id,
            "TENCENT_SECRET_KEY": alias_key,
        }
    )
    assert selected == {"secret_id": primary_id, "secret_key": primary_key}
    fallback = ocr_ingest._credentials_from_environment(
        {"TENCENT_SECRET_ID": alias_id, "TENCENT_SECRET_KEY": alias_key}
    )
    assert fallback == {"secret_id": alias_id, "secret_key": alias_key}
    with tempfile.TemporaryDirectory() as td:
        env_path = Path(td) / ".env"
        env_path.write_text(
            "IGNORED=value\n"
            f"TENCENT_SECRET_ID={alias_id}\n"
            f"TENCENT_SECRET_KEY={alias_key}\n"
            f"TENCENTCLOUD_SECRET_ID={primary_id}\n"
            f"TENCENTCLOUD_SECRET_KEY={primary_key}\n",
            encoding="utf-8",
        )
        parsed = ocr_ingest._credentials_from_dotenv(env_path)
    assert parsed == selected


def test_pdf_exact_body_and_mutation_guard() -> None:
    pdf_bytes = b"%PDF-1.4\n% offline contract fixture\n%%EOF\n"
    encoded = base64.b64encode(pdf_bytes).decode("ascii")
    transport = RecordingTransport()
    with tempfile.TemporaryDirectory() as td:
        pdf = Path(td) / "paper.pdf"
        pdf.write_bytes(pdf_bytes)
        result = ocr_ingest.request_file(
            pdf,
            credentials={"secret_id": "ID", "secret_key": "KEY"},
            transport=transport,
            timestamp=1,
            pdf_page_number=3,
        )
    expected = json.dumps(
        {"ImageBase64": encoded, "IsPdf": True, "PdfPageNumber": 3},
        separators=(",", ":"),
    ).encode("utf-8")
    assert result["request_id"] == "offline-pdf-request"
    assert len(transport.calls) == 1 and transport.calls[0]["body"] == expected

    signed = ocr_ingest.prepare_signed_request(
        encoded,
        secret_id="ID",
        secret_key="KEY",
        timestamp=1,
        is_pdf=True,
        pdf_page_number=3,
    )
    mutation_transport = RecordingTransport()
    try:
        ocr_ingest.transmit_signed_request(signed, mutation_transport, body=expected[:-1] + b"!")
    except ocr_ingest.OCRContractError as exc:
        assert exc.code == "SIGNATURE_MISMATCH"
    else:
        raise AssertionError("mutated PDF body was accepted")
    assert mutation_transport.calls == []


def main() -> int:
    cases = [
        ("credentials_precedence_and_zero_leak", test_credentials_precedence_and_zero_leak),
        ("pdf_exact_body_and_mutation_guard", test_pdf_exact_body_and_mutation_guard),
    ]
    failures = 0
    for case_id, test in cases:
        try:
            test()
        except Exception as exc:
            failures += 1
            print(f"FAIL {case_id}: {type(exc).__name__}")
        else:
            print(f"PASS {case_id}")
    print(f"RESULT {len(cases) - failures}/{len(cases)} passed")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
