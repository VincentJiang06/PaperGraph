#!/usr/bin/env python3
"""High-signal offline security lint for the shipped skill surface."""

from __future__ import annotations

import re
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {".py", ".md", ".json", ".txt", ".tsv"}
FAKE_VECTOR = SKILL_ROOT / "evals" / "fixtures" / "tc3_golden.json"


def main() -> int:
    failures: list[str] = []
    secret_patterns = [
        re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
        re.compile(r"AKIA[0-9A-Z]{16}"),
        re.compile(r"AKID[A-Za-z0-9]{28,}"),
        re.compile(r"ghp_[A-Za-z0-9]{30,}"),
        re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    ]
    script_injection = re.compile(r"shell\s*=\s*True|os\.system\s*\(|subprocess\.(?:Popen|run|call)\([^\n]*shell\s*=", re.MULTILINE)
    interactive = re.compile(r"\b(?:input|getpass)\s*\(")
    url = re.compile(r"https://([A-Za-z0-9.-]+)")

    for path in sorted(SKILL_ROOT.rglob("*")):
        if not path.is_file() or path.suffix not in TEXT_SUFFIXES:
            continue
        if ".skill-engineer" in path.parts or ".skill-guidance" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        if path != FAKE_VECTOR and any(pattern.search(text) for pattern in secret_patterns):
            failures.append(f"secret-pattern:{path.relative_to(SKILL_ROOT)}")
        if path.suffix == ".py":
            if script_injection.search(text):
                failures.append(f"shell-interpolation:{path.relative_to(SKILL_ROOT)}")
            if interactive.search(text):
                failures.append(f"interactive-prompt:{path.relative_to(SKILL_ROOT)}")
            if re.search(r"print\([^\n]*(?:secret_key|Authorization|recognized_text)", text, re.IGNORECASE):
                failures.append(f"sensitive-print:{path.relative_to(SKILL_ROOT)}")
            for host in url.findall(text):
                if host != "ocr.tencentcloudapi.com":
                    failures.append(f"undeclared-network-host:{host}:{path.relative_to(SKILL_ROOT)}")

    if failures:
        for failure in failures:
            print(f"FAIL {failure}")
        print("RESULT FAIL")
        return 1
    print("PASS no_hardcoded_secrets")
    print("PASS no_raw_shell_interpolation")
    print("PASS no_interactive_scripts")
    print("PASS no_sensitive_default_print")
    print("PASS network_host_fixed_to_ocr_tencentcloudapi_com")
    print("ALLOWLIST evals/fixtures/tc3_golden.json official_fake_tc3_vector")
    print("RESULT PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
