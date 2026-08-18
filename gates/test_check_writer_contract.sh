#!/usr/bin/env bash
# check_writer_contract.mjs 的负例套件（red-first）
#
# 这道门守的是 R5 第 5 条预测：六个纯自报谓词一条 deny 规则都没有，
# 第一次真实 run 压倒性 not_covered 之后，最省力的出口就是把它们默认写 true。
# 因此它自己更没有资格只靠「跑出来是绿的」来证明有效。
set -uo pipefail
cd "$(dirname "$0")/.."
SRC="$PWD"
GATE="$SRC/gates/check_writer_contract.mjs"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/gates" "$TMP/src"
pass=0; fail=0

seed() {
  cp "$SRC/gates/check_writer_contract.mjs" "$TMP/gates/"
  cp "$SRC/src/writer-contract.mjs" "$SRC/src/status.mjs" "$TMP/src/"
  cp "$SRC/01-CONTRACTS.md" "$TMP/"
}
assert_exit() {
  local want="$1" desc="$2"
  node "$GATE" --root "$TMP" >/dev/null 2>&1
  local got=$?
  if [ "$got" -eq "$want" ]; then printf 'PASS  %-52s exit=%d\n' "$desc" "$got"; pass=$((pass+1))
  else printf 'FAIL  %-52s exit=%d 期望 %d\n' "$desc" "$got" "$want"; fail=$((fail+1)); fi
}

echo "check_writer_contract 负例套件"; echo
seed; assert_exit 0 "绿样本 · 当前树"

# R-1 · S 读一个没有主人的字段 → 必须红
seed
python3 - "$TMP/src/status.mjs" <<'PY'
import sys
p=sys.argv[1]; s=open(p,encoding='utf-8').read()
s=s.replace("  const trace = []", "  const trace = []\n  if (c.brand_new_unowned_field) { /* 新读了一个没配主人的字段 */ }",1)
open(p,'w',encoding='utf-8').write(s)
PY
assert_exit 1 "红 R-1 · S 新读一个 §4 里没有主人的字段"

# R-2 · 把一个 S 读的门字段改判给 producer → 必须红（R5 第 5 条的正面形状）
seed
python3 - "$TMP/src/writer-contract.mjs" <<'PY'
import sys
p=sys.argv[1]; s=open(p,encoding='utf-8').read()
s=s.replace("  polarity_scope_passed: WRITER.GATE,", "  polarity_scope_passed: WRITER.PRODUCER,")
open(p,'w',encoding='utf-8').write(s)
PY
assert_exit 1 "红 R-2 · 把 polarity_scope_passed 改判给 producer"

# R-3 · deny 规则从白名单退化成放行 → 必须红
seed
python3 - "$TMP/src/writer-contract.mjs" <<'PY'
import sys
p=sys.argv[1]; s=open(p,encoding='utf-8').read()
s=s.replace("  const offending = Object.keys(payload).filter(k => !allowed.has(k))",
            "  const offending = []")
open(p,'w',encoding='utf-8').write(s)
PY
assert_exit 1 "红 R-3 · deny 规则不再拒绝任何越权字段"

# R-4 · W-04 行漏掉一个门字段 → 必须红
seed
python3 - "$TMP/01-CONTRACTS.md" <<'PY'
import sys
p=sys.argv[1]; L=open(p,encoding='utf-8').read().split('\n')
for i,l in enumerate(L):
    if l.startswith('| W-04 |'):
        L[i]=l.replace('`polarity_scope_passed`','').replace('**``**','')
        break
open(p,'w',encoding='utf-8').write('\n'.join(L))
PY
assert_exit 1 "红 R-4 · W-04 行漏掉 polarity_scope_passed"

# R-5 · 某个 kind 的把关谓词改成 producer 可写 → 例外论证塌 → 必须红
seed
python3 - "$TMP/src/writer-contract.mjs" <<'PY'
import sys
p=sys.argv[1]; s=open(p,encoding='utf-8').read()
s=s.replace("  rerun_gate_passed: WRITER.GATE,", "  rerun_gate_passed: WRITER.PRODUCER,")
open(p,'w',encoding='utf-8').write(s)
PY
assert_exit 1 "红 R-5 · K-D 的把关谓词变成 producer 可写"

# R-6 · 提取不到读集（空集）→ 必须拒绝给绿灯，退出码 2
seed
printf 'export const ST = {}\nexport function S(){ return {status:"x",trace:[]} }\n' > "$TMP/src/status.mjs"
assert_exit 2 "红 R-6 · 从 S 提取到的读集为空（拒绝空集绿灯）"

echo
echo "$pass 通过 / $fail 失败"
[ "$fail" -eq 0 ]
