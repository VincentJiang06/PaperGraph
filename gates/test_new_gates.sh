#!/usr/bin/env bash
# 本轮（E1 外部标定测试）新增三道门的**负例套件**。
#
# 〔为什么必须有这个文件 · 自攻发现〕开发那三道门时，我用一次性命令验过红样本：
#   `T=$(mktemp -d); cp -R src gates "$T/"; perl -0pi -e '...' ...; node ...`
# 跑完就没了。而 S0 阶段这个仓库自己得出的结论原话是：
#   **承重证据应当是入库的自包含脚本，而不是一条一次性命令加一个哈希。**
# 也就是说，我对自己的新门做了这个项目明令不做的事——而且做了三次。
#
# 做法与 test_check_supply_contract.sh 相同：复制一份树，把修复倒回去，
# 要求门判红，**且判红的理由是它自己声称的那条**
# （只看退出码会把崩溃当成拦截，R3 栽过一次）。
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(dirname "$HERE")"
pass=0; fail=0
ok() { pass=$((pass+1)); echo "PASS  $1"; }
no() { fail=$((fail+1)); echo "FAIL  $1"; }

# $1=编号 $2=说明 $3=要跑的门 $4=期望理由 $5...=施加的变异
red_case() {
  local id="$1" desc="$2" gate="$3" want="$4"; shift 4
  local tmp; tmp="$(mktemp -d)"
  cp -R "$REPO/src" "$tmp/src"; cp -R "$REPO/gates" "$tmp/gates"
  cp -R "$REPO/tests" "$tmp/tests" 2>/dev/null || true
  cp -R "$REPO/packages" "$tmp/packages" 2>/dev/null || true
  cp "$REPO/01-CONTRACTS.md" "$tmp/" 2>/dev/null || true
  ( cd "$tmp" && eval "$@" )
  local out ec
  out="$(cd "$tmp" && node "$gate" 2>&1)"; ec=$?
  if [ "$ec" -eq 0 ]; then
    no "$id · $desc —— 门放行了（exit 0）"
  elif ! grep -q "$want" <<<"$out"; then
    no "$id · $desc —— 判红了，但理由不是「$want」"
    grep -E '^FAIL' <<<"$out" | head -2 | sed 's/^/        /'
  else
    ok "$id · $desc  exit=$ec"
  fi
  rm -rf "$tmp"
}

echo "本轮新增三道门 · 负例套件"
echo

# ── 归一化一致性门（E-3 → T4-1 那个复发机制） ────────────────────────────
red_case "N-1" "撤掉 numericForm 的 NFKC（T4-1 原形态）" \
  gates/check_normalization.mjs "全角与半角形态得到不同判定" \
  "perl -0pi -e \"s/String\\(s\\)\\.normalize\\('NFKC'\\)/String(s)/\" src/gates/g-containment.mjs"

red_case "N-2" "撤掉组稿器的 NFKC（E-3 原形态）" \
  gates/check_normalization.mjs "全角与半角形态得到不同判定" \
  "perl -0pi -e \"s/String\\(skeleton\\)\\.normalize\\('NFKC'\\)/String(skeleton)/\" src/composer.mjs"

# ── 同源竞争读数门（T2-4） ───────────────────────────────────────────────
red_case "F-1" "去掉 discriminator 校验：只要给了就放行" \
  gates/check_frame.mjs "不符" \
  "perl -0pi -e 's/if \\(!mine\\.includes\\(d\\)\\) \\{/if (false) {/' src/gates/g-frame.mjs"

red_case "F-2" "兄弟读数范围退回整篇正文（全文快照上必然误伤）" \
  gates/check_frame.mjs "不符" \
  "perl -0pi -e 's/const window = containingSentence\\(b, a\\)/const window = b/' src/gates/g-frame.mjs"

red_case "F-3" 'and 一律切开（名词短语内部的 and 被误切）' \
  gates/check_frame.mjs "不符" \
  "perl -0pi -e 's/parts\\.every\\(hasNum\\)/true/' src/gates/g-frame.mjs"

# ── 锚点包含门（T2-1/T2-2 + 子串陷阱） ───────────────────────────────────
red_case "C-1" "退回裸 includes（数值等价与词干全丢）" \
  gates/check_containment.mjs "不符" \
  "perl -0pi -e 's/if \\(containsWithNumberBoundary\\(anchor, val\\)\\)/if (anchor.includes(val))/' src/gates/g-containment.mjs" \
  "&& perl -0pi -e 's/if \\(type === .value. \\|\\| type === .comparator.\\) \\{/if (false) {/' src/gates/g-containment.mjs" \
  "&& perl -0pi -e \"s/if \\(type === 'entity'\\) \\{/if (false) {/\" src/gates/g-containment.mjs"

red_case "C-2" '数字按子串比（3 命中锚句里的 36）' \
  gates/check_containment.mjs "不符" \
  "perl -0pi -e 's/return new RegExp\\(NUM_EDGE \\+ esc\\(needle\\) \\+ NUM_EDGE_R\\)\\.test\\(hay\\)/return hay.includes(needle)/' src/gates/g-containment.mjs"

red_case "C-3" "metric/sample 槽也放松（T2-3 的判据被拆掉）" \
  gates/check_containment.mjs "不符" \
  "perl -0pi -e \"s/if \\(type === 'entity'\\) \\{/if (true) {/\" src/gates/g-containment.mjs"

# ── 绿控：未改动的树必须全部放行 ─────────────────────────────────────────
for g in check_normalization check_frame check_containment; do
  if ( cd "$REPO" && node "gates/$g.mjs" >/dev/null 2>&1 ); then
    ok "绿 G · $g 在未改动的树上放行 exit=0"
  else
    no "绿 G · $g 在未改动的树上判红了（红样本可能是被别的原因触发的）"
  fi
done

echo
echo "$pass 通过 / $fail 失败"
[ "$fail" -eq 0 ]
