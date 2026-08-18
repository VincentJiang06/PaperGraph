#!/usr/bin/env bash
# M0-6 fixture. Measures what DSH actually does when the central rate-limit
# gateway (hosted as an MCP stdio server) is dead, crashes mid-run, or is
# reached from two harness processes at once.
#
# Requires: dsh on PATH, DEEPSEEK_API_KEY set. Makes real LLM calls.
# Uses a throwaway $DSH_HOME so the caller's ~/.dsh is untouched.
# Prints only derived assertions, not model prose, so the output is stable.
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
GW="$HERE/M0-6.fixture.fake-gateway-mcp.mjs"
W=$(mktemp -d); trap 'rm -rf "$W"' EXIT
export DSH_HOME="$W/home"; mkdir -p "$DSH_HOME"
cd "$W" || exit 1

patch() { # $1 mode, $2 failOnStartupError
cat > "$W/patch-$1-$2.yml" <<YAML
- insert:
    - id: mcp-gateway
      name: '@deepseek-ai/dsh-mcp-client'
      config:
        serverName: gw
        transport: stdio
        command: node
        args: ['$GW', '$1']
        failOnStartupError: $2
        reconnect:
          enabled: true
          initialDelayMs: 300
          maxDelayMs: 1200
          maxAttempts: 3
YAML
}
for m in ok die-now die-after; do for f in true false; do patch $m $f; done; done

# scaffold the throwaway headless profile
dsh --profile headless --dump-config >/dev/null 2>&1

echo "== A. gateway healthy =="
dsh --profile headless --patch "$W/patch-ok-true.yml" \
  "Call the gw_fetch tool with url=https://example.com/a . Then reply with exactly the text the tool returned. Do not use any other tool." \
  > "$W/a.out" 2> "$W/a.err"; a=$?
echo "exit=$a  stdout_contains_GATEWAY-OK=$(grep -qc 'GATEWAY-OK' "$W/a.out" >/dev/null && echo yes || echo no)"

echo "== B. gateway dead, failOnStartupError=true =="
dsh --profile headless --patch "$W/patch-die-now-true.yml" "Say OK and stop." > "$W/b.out" 2> "$W/b.err"; b=$?
echo "exit=$b  stdout_bytes=$(wc -c < "$W/b.out" | tr -d ' ')  boot_error_names_mcp_client=$(grep -qc 'initial connection or tool synchronization failed' "$W/b.err" >/dev/null && echo yes || echo no)"

echo "== C. gateway dead, failOnStartupError=false (the DEFAULT) =="
dsh --profile headless --patch "$W/patch-die-now-false.yml" \
  "Fetch https://example.com/a and report its HTTP status line. You must use the gw_fetch gateway tool for all network access." \
  > "$W/c.out" 2> "$W/c.err"; c=$?
echo "exit=$c  stdout_bytes_nonzero=$([ -s "$W/c.out" ] && echo yes || echo no)  gateway_spawn_attempts=$(grep -c 'started' "$W/c.err")"

echo "== D. gateway crashes mid-run (supervised restart) =="
DIE_MS=6000 dsh --profile headless --patch "$W/patch-die-after-false.yml" \
  "Call the gw_fetch tool five times in a row, with url=https://example.com/1 through https://example.com/5, one call at a time. Report verbatim what each of the five calls returned, including any errors. Do not use bash." \
  > "$W/d.out" 2> "$W/d.err"; d=$?
echo "exit=$d  distinct_gateway_pids=$(grep -o 'pid=[0-9]*' "$W/d.err" | sort -u | wc -l | tr -d ' ')  dsh_own_stderr_lines=$(grep -vc 'fake-gateway' "$W/d.err")"

echo "== E. two concurrent harness processes =="
( dsh --profile headless --patch "$W/patch-ok-false.yml" "Call gw_fetch with url=https://example.com/A and reply with exactly its output." > "$W/eA.out" 2>/dev/null ) &
( dsh --profile headless --patch "$W/patch-ok-false.yml" "Call gw_fetch with url=https://example.com/B and reply with exactly its output." > "$W/eB.out" 2>/dev/null ) &
wait
echo "distinct_served_by_pid=$(cat "$W/eA.out" "$W/eB.out" | grep -o 'served_by_pid=[0-9]*' | sort -u | wc -l | tr -d ' ')"
