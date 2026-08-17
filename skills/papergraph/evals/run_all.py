#!/usr/bin/env python3
"""Stdlib-only contract harness for PaperGraph's deterministic surfaces."""

from __future__ import annotations

import base64
import copy
import json
import math
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable


SKILL_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).resolve().parent / "fixtures"
sys.path.insert(0, str(SKILL_ROOT))

from scripts import ocr_ingest, trigger_policy, validate_eval_bundle, workflow_contract  # noqa: E402


def load(name: str) -> Any:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class ScriptedTransport:
    def __init__(self, *events: Any) -> None:
        self.events = list(events)
        self.calls: list[dict[str, Any]] = []

    def __call__(self, request: dict[str, Any]) -> dict[str, Any]:
        self.calls.append(request)
        event = self.events.pop(0)
        if isinstance(event, BaseException):
            raise event
        return copy.deepcopy(event)


def capture(call: Callable[[], Any]) -> dict[str, Any]:
    try:
        return {"returned": call()}
    except Exception as exc:  # The contract intentionally exposes typed failures.
        return {"error": exc}


def assert_error(outcome: dict[str, Any], *, code: str | None = None, outcome_name: str | None = None) -> None:
    assert "error" in outcome, f"expected contract error, got {outcome!r}"
    error = outcome["error"]
    assert isinstance(error, ocr_ingest.OCRContractError), type(error).__name__
    if code is not None:
        assert error.code == code, (error.code, code)
    if outcome_name is not None:
        assert error.outcome == outcome_name, (error.outcome, outcome_name)


def normalize(envelope: dict[str, Any], run_id: str = "run-a") -> dict[str, Any]:
    return ocr_ingest.normalize_response(
        envelope,
        image_width=2000,
        image_height=1000,
        provider_run_id=run_id,
        source_id="source-fixture",
    )


def test_tc3_exact_body_and_signature() -> None:
    golden = load("tc3_golden.json")
    request = ocr_ingest.prepare_signed_request(
        golden["image_base64"],
        secret_id=golden["secret_id"],
        secret_key=golden["secret_key"],
        timestamp=golden["timestamp"],
    )
    assert request.get("body") == golden["body"].encode("utf-8")
    assert request.get("headers", {}).get("Authorization") == golden["authorization"]
    assert request.get("headers", {}).get("Host") == ocr_ingest.HOST


def test_tc3_mutation_rejected_before_send() -> None:
    golden = load("tc3_golden.json")
    request = ocr_ingest.prepare_signed_request(
        golden["image_base64"], secret_id=golden["secret_id"], secret_key=golden["secret_key"], timestamp=golden["timestamp"]
    )
    transport = ScriptedTransport(load("tencent_success.json"))
    mutated = golden["body"].encode("utf-8")[:-1] + b"!"
    result = capture(lambda: ocr_ingest.transmit_signed_request(request, transport, body=mutated))
    assert_error(result, code="SIGNATURE_MISMATCH")
    assert transport.calls == []


def test_encoded_size_boundaries() -> None:
    accepted = [ocr_ingest.validate_encoded_size(b"A" * n) for n in (9_999_999, 10_000_000)]
    too_large = capture(lambda: ocr_ingest.validate_encoded_size(b"A" * 10_000_001))
    assert accepted == [True, True], accepted
    assert_error(too_large, code="ENCODED_SIZE_LIMIT")


def test_local_preflight_zero_network_and_secret_safe() -> None:
    secret = "SECRET_MUST_NOT_LEAK"
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        empty = root / "empty.png"
        empty.write_bytes(b"")
        unsupported = root / "page.gif"
        unsupported.write_bytes(b"GIF89a")
        valid = root / "page.png"
        valid.write_bytes(base64.b64decode((FIXTURES / "sample_image.b64").read_text().strip()))
        transport = ScriptedTransport(load("tencent_success.json"))
        credentials = {"secret_id": "ID", "secret_key": secret}
        outcomes = [
            capture(lambda: ocr_ingest.request_file(empty, credentials=credentials, transport=transport, timestamp=1)),
            capture(lambda: ocr_ingest.request_file(unsupported, credentials=credentials, transport=transport, timestamp=1)),
            capture(lambda: ocr_ingest.request_file(valid, credentials={}, transport=transport, timestamp=1)),
        ]
    assert all("error" in item for item in outcomes), outcomes
    assert transport.calls == []
    assert secret not in " ".join(str(item) for item in outcomes)


def test_http_200_provider_error_preserved() -> None:
    transport = ScriptedTransport(load("tencent_provider_error.json"))
    result = capture(lambda: ocr_ingest.request_ocr("QUJD", secret_id="ID", secret_key="KEY", timestamp=1, transport=transport))
    assert_error(result, code="InvalidParameterValue.InvalidImageContent")
    assert result["error"].request_id == "fixture-provider-error-001"


def test_retryable_limit_then_basic_success() -> None:
    transport = ScriptedTransport(load("tencent_rate_limit_error.json"), load("tencent_success.json"))
    result = ocr_ingest.request_ocr(
        "QUJD", secret_id="ID", secret_key="KEY", timestamp=1, transport=transport, max_attempts=2, sleep=lambda _: None
    )
    assert result.get("request_id") == "fixture-basic-success-001"
    assert len(transport.calls) == 2
    assert {call["headers"]["X-TC-Action"] for call in transport.calls} == {ocr_ingest.BASIC_ACTION}


def test_pre_send_failure_classified() -> None:
    transport = ScriptedTransport(ocr_ingest.TransportFailure("dns failure", submitted=False))
    result = capture(lambda: ocr_ingest.request_ocr("QUJD", secret_id="ID", secret_key="KEY", timestamp=1, transport=transport))
    assert_error(result, outcome_name="not_submitted")


def test_post_submit_timeout_unknown_no_retry() -> None:
    transport = ScriptedTransport(ocr_ingest.TransportFailure("read timeout", submitted=True), load("tencent_success.json"))
    result = capture(
        lambda: ocr_ingest.request_ocr("QUJD", secret_id="ID", secret_key="KEY", timestamp=1, transport=transport, max_attempts=2)
    )
    assert_error(result, outcome_name="outcome_unknown")
    assert len(transport.calls) == 1


def test_malformed_fields_fail_closed() -> None:
    outcomes = [(case["field"], capture(lambda case=case: normalize(case["envelope"]))) for case in load("malformed_cases.json")]
    assert all("error" in result and field in str(result["error"]) for field, result in outcomes), outcomes
    nonfinite = load("tencent_success.json")
    nonfinite["Response"]["TextDetections"][0]["Confidence"] = math.inf
    result = capture(lambda: normalize(nonfinite))
    assert "error" in result and "Confidence" in str(result["error"]), result


def test_invalid_geometry_rejected() -> None:
    outcomes = []
    for case in load("invalid_geometry_cases.json"):
        envelope = load("tencent_success.json")
        envelope["Response"]["TextDetections"] = [{"DetectedText": case["name"], "Confidence": 90, "Polygon": case["polygon"]}]
        outcomes.append(capture(lambda envelope=envelope: ocr_ingest.normalize_response(envelope, image_width=100, image_height=100, provider_run_id="run-a", source_id="src")))
    assert all("error" in item and "Polygon" in str(item["error"]) for item in outcomes), outcomes


def test_item_polygon_fallback_clockwise() -> None:
    result = normalize(load("tencent_fallback.json"))
    assert len(result.get("elements", [])) == 1, result
    polygon = result["elements"][0]["polygon_norm"]
    assert polygon == [[0.045, 0.1], [0.245, 0.1], [0.245, 0.15], [0.045, 0.15]], polygon


def test_nonzero_angle_fallback_rejected() -> None:
    result = capture(lambda: normalize(load("tencent_nonzero_angle_missing_polygon.json")))
    assert "error" in result and "coordinate" in str(result["error"]).lower(), result


def test_unicode_order_ids_metamorphic_idempotency() -> None:
    first = normalize(load("tencent_unicode_a.json"), "run-a")
    replay = normalize(load("tencent_unicode_a.json"), "run-a")
    shuffled = normalize(load("tencent_unicode_b.json"), "run-a")
    assert isinstance(first.get("elements"), list), first
    assert [e["text"] for e in first["elements"]] == ["证据链📚", "研究🧪"]
    assert first == replay == shuffled
    assert len({e["id"] for e in first["elements"]}) == len(first["elements"])


def test_cross_run_ids_disjoint() -> None:
    a = normalize(load("tencent_success.json"), "run-a")
    b = normalize(load("tencent_success.json"), "run-b")
    ids_a = {item["id"] for item in a.get("elements", [])}
    ids_b = {item["id"] for item in b.get("elements", [])}
    assert ids_a and ids_b and ids_a.isdisjoint(ids_b), (ids_a, ids_b)


def test_confidence_boundaries() -> None:
    envelope = load("tencent_success.json")
    envelope["Response"]["TextDetections"] = envelope["Response"]["TextDetections"][:2]
    envelope["Response"]["TextDetections"][0]["Confidence"] = 0
    envelope["Response"]["TextDetections"][1]["Confidence"] = 100
    result = normalize(envelope)
    assert [e["confidence"] for e in result.get("elements", [])] == [0.0, 1.0]
    envelope["Response"]["TextDetections"][0]["Confidence"] = -1
    assert "error" in capture(lambda: normalize(envelope))


def test_offline_replay_atomic_idempotent_no_secrets() -> None:
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "replay"
        command = [sys.executable, str(SKILL_ROOT / "scripts" / "ocr_ingest.py"), "replay", "--response", str(FIXTURES / "tencent_success.json"), "--output-dir", str(out), "--image-width", "2000", "--image-height", "1000", "--provider-run-id", "run-replay", "--source-id", "source-replay"]
        first = subprocess.run(command, text=True, capture_output=True, check=False)
        required = [out / name for name in ("raw_response.json", "source.json", "manifest.json", "source.txt")]
        assert first.returncode == 0 and all(path.is_file() for path in required), (first.returncode, required, first.stdout)
        before = {path.name: path.read_bytes() for path in required}
        second = subprocess.run(command, text=True, capture_output=True, check=False)
        after = {path.name: path.read_bytes() for path in required}
        assert before == after and second.returncode == 0
        combined = first.stdout + second.stdout + "".join(data.decode("utf-8") for data in after.values())
        assert "AKIDEXAMPLE" not in combined and "Gu5t9x" not in combined
        assert not list(out.rglob("*.tmp"))


def test_live_probe_refusal_zero_calls() -> None:
    with tempfile.TemporaryDirectory() as td:
        image = Path(td) / "page.png"
        image.write_bytes(base64.b64decode((FIXTURES / "sample_image.b64").read_text().strip()))
        transport = ScriptedTransport(load("tencent_success.json"))
        common = dict(image_path=image, output_dir=Path(td) / "out", credentials={"secret_id": "ID", "secret_key": "KEY"}, transport=transport, timestamp=1)
        accurate = capture(lambda: ocr_ingest.run_live_probe(action=ocr_ingest.ACCURATE_ACTION, confirmation="ONE_BASIC_CALL", **common))
        unconfirmed = capture(lambda: ocr_ingest.run_live_probe(action=ocr_ingest.BASIC_ACTION, confirmation=None, **common))
    assert "error" in accurate and "error" in unconfirmed and transport.calls == [], (accurate, unconfirmed, transport.calls)


def test_live_probe_one_authorized_basic_call() -> None:
    with tempfile.TemporaryDirectory() as td:
        image = Path(td) / "page.png"
        image.write_bytes(base64.b64decode((FIXTURES / "sample_image.b64").read_text().strip()))
        transport = ScriptedTransport(load("tencent_success.json"))
        result = ocr_ingest.run_live_probe(image, Path(td) / "out", action=ocr_ingest.BASIC_ACTION, confirmation="ONE_BASIC_CALL", credentials={"secret_id": "ID", "secret_key": "KEY"}, transport=transport, timestamp=1)
    assert len(transport.calls) == 1 and result.get("request_id") == "fixture-basic-success-001", (transport.calls, result)


def copy_bundle(destination: Path) -> None:
    shutil.copytree(FIXTURES / "eval_bundle_complete", destination)


def test_eval_missing_each_required_input_never_ship() -> None:
    files = ["d1_answer_key.json", "d2_steelmans.json", "d3_adversary.json", "d4b_claim_audit.json", "d5_referees.json"]
    verdicts = []
    with tempfile.TemporaryDirectory() as td:
        for index, missing in enumerate(files):
            bundle = Path(td) / str(index)
            copy_bundle(bundle)
            (bundle / missing).unlink()
            verdicts.append(validate_eval_bundle.validate_bundle(bundle).get("verdict"))
    assert all(value in {"INCOMPLETE", "REVISE"} for value in verdicts), verdicts


def test_eval_referees_and_honesty_fail_closed() -> None:
    verdicts = []
    with tempfile.TemporaryDirectory() as td:
        few = Path(td) / "few"
        copy_bundle(few)
        data = json.loads((few / "d5_referees.json").read_text())
        data["referees"] = data["referees"][:2]
        (few / "d5_referees.json").write_text(json.dumps(data))
        verdicts.append(validate_eval_bundle.validate_bundle(few).get("verdict"))
        honesty = Path(td) / "honesty"
        copy_bundle(honesty)
        data = json.loads((honesty / "d4b_claim_audit.json").read_text())
        data["honesty_flags"] = ["unsupported causal claim"]
        (honesty / "d4b_claim_audit.json").write_text(json.dumps(data))
        verdicts.append(validate_eval_bundle.validate_bundle(honesty).get("verdict"))
    assert verdicts == ["REVISE", "REVISE"], verdicts


def test_eval_complete_ship_deterministic() -> None:
    first = validate_eval_bundle.validate_bundle(FIXTURES / "eval_bundle_complete")
    second = validate_eval_bundle.validate_bundle(FIXTURES / "eval_bundle_complete")
    assert first.get("verdict") == "SHIP" and first.get("complete") is True, first
    assert first == second


def test_trigger_adjacent_negatives() -> None:
    cases = [case for case in load("../cases.json") if not case["expected_activation"]]
    results = [trigger_policy.classify_request(case["prompt"]) for case in cases]
    assert all(result.get("activate") is False and result.get("route") == "narrower_tool" for result in results), results


def test_trigger_positive_full_workflow() -> None:
    cases = [case for case in load("../cases.json") if case["expected_activation"]]
    results = [trigger_policy.classify_request(case["prompt"]) for case in cases]
    required = {"ocr", "parallel_author_wave", "held_out_eval"}
    assert all(result.get("activate") is True and result.get("route") == "papergraph" and required <= set(result.get("phases", [])) for result in results), results


def test_offline_end_to_end_smoke() -> None:
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "run"
        result = workflow_contract.run_offline_smoke(topic="Urban heat adaptation", response_path=FIXTURES / "tencent_success.json", eval_bundle_dir=FIXTURES / "eval_bundle_complete", output_dir=out, image_width=2000, image_height=1000, provider_run_id="smoke-run", source_id="smoke-source", gate_runner=lambda _: {"divergence": "PASS", "rigor": "PASS"})
        required = {"paper.md", "positions.md", "claims.tsv", "gate_report.md", "eval_verdict.json", "sources/source.json"}
        present = {str(path.relative_to(out)) for path in out.rglob("*") if path.is_file()} if out.exists() else set()
    assert result.get("verdict") == "SHIP" and result.get("gate_results") == {"divergence": "PASS", "rigor": "PASS"}, result
    assert required <= present, (required, present)


CASES: list[tuple[str, Callable[[], None]]] = [
    ("tc3_exact_body_and_signature", test_tc3_exact_body_and_signature),
    ("tc3_mutation_rejected_before_send", test_tc3_mutation_rejected_before_send),
    ("encoded_size_boundaries", test_encoded_size_boundaries),
    ("local_preflight_zero_network_and_secret_safe", test_local_preflight_zero_network_and_secret_safe),
    ("http_200_provider_error_preserved", test_http_200_provider_error_preserved),
    ("retryable_limit_then_basic_success", test_retryable_limit_then_basic_success),
    ("pre_send_failure_classified", test_pre_send_failure_classified),
    ("post_submit_timeout_unknown_no_retry", test_post_submit_timeout_unknown_no_retry),
    ("malformed_fields_fail_closed", test_malformed_fields_fail_closed),
    ("invalid_geometry_rejected", test_invalid_geometry_rejected),
    ("item_polygon_fallback_clockwise", test_item_polygon_fallback_clockwise),
    ("nonzero_angle_fallback_rejected", test_nonzero_angle_fallback_rejected),
    ("unicode_order_ids_metamorphic_idempotency", test_unicode_order_ids_metamorphic_idempotency),
    ("cross_run_ids_disjoint", test_cross_run_ids_disjoint),
    ("confidence_boundaries", test_confidence_boundaries),
    ("offline_replay_atomic_idempotent_no_secrets", test_offline_replay_atomic_idempotent_no_secrets),
    ("live_probe_refusal_zero_calls", test_live_probe_refusal_zero_calls),
    ("live_probe_one_authorized_basic_call", test_live_probe_one_authorized_basic_call),
    ("eval_missing_each_required_input_never_ship", test_eval_missing_each_required_input_never_ship),
    ("eval_referees_and_honesty_fail_closed", test_eval_referees_and_honesty_fail_closed),
    ("eval_complete_ship_deterministic", test_eval_complete_ship_deterministic),
    ("trigger_adjacent_negatives", test_trigger_adjacent_negatives),
    ("trigger_positive_full_workflow", test_trigger_positive_full_workflow),
    ("offline_end_to_end_smoke", test_offline_end_to_end_smoke),
]


CHECKLIST_COVERAGE = {
    1: "tc3_exact_body_and_signature", 2: "tc3_mutation_rejected_before_send", 3: "encoded_size_boundaries",
    4: "local_preflight_zero_network_and_secret_safe", 5: "http_200_provider_error_preserved",
    6: "retryable_limit_then_basic_success", 7: "post_submit_timeout_unknown_no_retry",
    8: "malformed_fields_fail_closed", 9: "invalid_geometry_rejected", 10: "item_polygon_fallback_clockwise",
    11: "nonzero_angle_fallback_rejected", 12: "unicode_order_ids_metamorphic_idempotency",
    13: "cross_run_ids_disjoint", 14: "offline_replay_atomic_idempotent_no_secrets",
    15: "live_probe_refusal_zero_calls", 16: "eval_missing_each_required_input_never_ship",
    17: "eval_referees_and_honesty_fail_closed", 18: "eval_complete_ship_deterministic",
    19: "trigger_adjacent_negatives", 20: "trigger_positive_full_workflow",
}


def main() -> int:
    known = {case_id for case_id, _ in CASES}
    assert len(CHECKLIST_COVERAGE) == 20 and set(CHECKLIST_COVERAGE.values()) <= known
    passed = 0
    for case_id, test in CASES:
        try:
            test()
        except Exception as exc:
            message = " ".join(str(exc).split()) or type(exc).__name__
            print(f"FAIL {case_id}: {type(exc).__name__}: {message}")
        else:
            passed += 1
            print(f"PASS {case_id}")
    print(f"CHECKLIST_EDGES {len(CHECKLIST_COVERAGE)}")
    print(f"RESULT {passed}/{len(CASES)} passed")
    return 0 if passed == len(CASES) else 1


if __name__ == "__main__":
    raise SystemExit(main())
