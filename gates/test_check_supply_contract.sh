#!/usr/bin/env bash
# 供给侧契约门的**负例套件** —— 把 R6 那一版的代码形态原样复原，逐条要求判红。
#
# 〔为什么必须有这个文件〕本仓库的头号教训：**门必须先证明会红才算数**（已三次栽在这上面）。
# check_supply_contract 是为 R6 的三条 P1 造的，而 R6 的三条 P1 是在 22 道门全绿时
# 被外部审计找到的——也就是说「跑了绿」这件事在这个仓库里已经被证明说明不了任何东西。
#
# 做法：把 src/ 复制一份，逐条把修复**倒回去**，然后要求门在那份副本上判红，
# 且判红的理由是**它自己声称的那条**（只看退出码会把崩溃当成拦截，R3 栽过一次）。
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(dirname "$HERE")"
pass=0; fail=0
ok()  { pass=$((pass+1)); echo "PASS  $1"; }
no()  { fail=$((fail+1)); echo "FAIL  $1"; }

# $1=编号 $2=说明 $3=期望在输出里出现的理由 $4...=对副本施加的 sed/perl 命令
red_case() {
  local id="$1" desc="$2" want="$3"; shift 3
  local tmp; tmp="$(mktemp -d)"
  cp -R "$REPO/src" "$tmp/src"; cp -R "$REPO/gates" "$tmp/gates"
  cp -R "$REPO/packages" "$tmp/packages" 2>/dev/null || true
  ( cd "$tmp" && eval "$@" )
  local out ec
  out="$(cd "$tmp" && node gates/check_supply_contract.mjs --root "$tmp" 2>&1)"; ec=$?
  if [ "$ec" -eq 0 ]; then
    no "$id · $desc —— 门放行了（exit 0）"
  elif ! grep -q "$want" <<<"$out"; then
    no "$id · $desc —— 判红了，但理由不是「$want」"
    sed 's/^/        /' <<<"$out" | grep -E '^\s+FAIL' | head -3
  else
    ok "$id · $desc  exit=$ec"
  fi
  rm -rf "$tmp"
}

echo "供给侧契约门 · 负例套件"
echo

# ── R6-01 · `__` 前缀后门 ────────────────────────────────────────────────
red_case "红 R-1" "run.mjs 读 \`__\` 前缀字段（R6-01 原形态）" "__\` 前缀字段" \
  "perl -0pi -e 's/const idxs = c\.evidence_index \?\? \[\]/const idxs = c.__evidence_index ?? []/' src/run.mjs"

# ── R6-01b · 去掉污染检查 ────────────────────────────────────────────────
red_case "红 R-2" "run.mjs 不再检查 producer 污染" "未在读取前检查 producer 污染" \
  "perl -0pi -e 's/^.*assertNoProducerContamination\(c,.*\$//m' src/run.mjs"

# ── R6-02 · fail-open 缺省 / 字面量 true ─────────────────────────────────
red_case "红 R-3" "research.mjs 把把关谓词写成字面量 true（R6-02 原形态）" "R6-02 的形态" \
  "perl -0pi -e 's/const ctx = buildGateCtx\(\{/const ctx = { rerun_gate_passed: true, question_frozen: true }; const _c = buildGateCtx({/' src/research.mjs"

# ── R6-03 · payload 后展开 ───────────────────────────────────────────────
red_case "红 R-4" "run.mjs 让 payload 后展开遮蔽门字段（R6-03 原形态）" "R6-03 的形态" \
  "perl -0pi -e 's/sealStatus\(r\.statusRecord, submission\.payload \?\? \{\}\)/{ ...r.statusRecord, ...submission.payload }/' src/run.mjs"

# ── A-1 · 绕过唯一入口 ───────────────────────────────────────────────────
red_case "红 R-5" "调用 runClaim 但自己造 ctx" "绕过供给侧唯一入口" \
  "perl -0pi -e 's/buildGateCtx\(\{/mkCtxInline({/g' src/run.mjs"

# ── B 层 · 行为倒回：把四个谓词改回 fail-open ────────────────────────────
red_case "红 R-6" "gate-ctx 的把关谓词改回 fail-open 缺省（行为层）" "R6 反例路径仍然走得通" \
  "perl -0pi -e 's/\? rerunGate\(root, submission\.rerun_spec\)/? { pass: true, reasons: [], params: {} }/' src/gate-ctx.mjs" \
  "&& perl -0pi -e 's/\? freezeGate\(frozen, submission, evidence\.map\(e => e\.fetch\?\.retrievedAt\)\)/? { pass: true, reasons: [], params: {} }/' src/gate-ctx.mjs"

# ── B 层 · 多证据完整性倒回（R6-08） ─────────────────────────────────────
red_case "红 R-7" "source_integrity 只核第一条证据（R6-08 原形态）" "R6 反例路径仍然走得通" \
  "perl -0pi -e 's/for \(const \{ ref \} of evidence\) \{/for (const { ref } of evidence.slice(0, 1)) {/' src/gate-ctx.mjs"

# ── B 层 · 簇归并倒回（R6-05） ───────────────────────────────────────────
red_case "红 R-8" "不把内容哈希递给 G-CLUSTER（R6-05 原形态）" "R6 反例路径仍然走得通" \
  "perl -0pi -e 's/object_sha256: cards\[i\]\.object_sha256,//' src/run.mjs"

# ── 绿样本：未改动的树必须放行 ───────────────────────────────────────────
# 〔缺了这条，一个恒判红的门也能让上面 8 条全绿〕
out="$(node "$HERE/check_supply_contract.mjs" --root "$REPO" 2>&1)"; ec=$?
if [ "$ec" -ne 0 ]; then no "绿 G-1 · 未改动的树被误判红 exit=$ec"; else ok "绿 G-1 · 未改动的树放行 exit=0"; fi

echo
echo "$pass 通过 / $fail 失败"
[ "$fail" -eq 0 ]
