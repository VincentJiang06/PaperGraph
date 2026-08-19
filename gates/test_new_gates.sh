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
  cp "$REPO/07-ATTACK-LEDGER.md" "$tmp/" 2>/dev/null || true
  # 〔F-4 教训〕变异如果一个字符都没改到（正则转义写错、perl 没匹配上），
  # 门当然还是绿的，而套件只会报「门放行了」—— 把**空变异**读成**空心门**。
  # 两者的修法完全相反，所以先证明变异真的落到了文件上。
  local before after
  before="$(cd "$tmp" && find . -type f -exec shasum {} + | shasum)"
  ( cd "$tmp" && eval "$@" )
  after="$(cd "$tmp" && find . -type f -exec shasum {} + | shasum)"
  if [ "$before" = "$after" ]; then
    no "$id · $desc —— **变异是空的**：树未发生任何改动（不是门的问题）"
    rm -rf "$tmp"; return
  fi
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
red_case "F-1" "去掉 discriminator 属实校验：只要给了就放行" \
  gates/check_frame.mjs "不符" \
  "perl -0pi -e 's/if \\(!aMasked\\.includes\\(d\\) && !a\\.includes\\(d\\)\\) \\{/if (false) {/' src/gates/g-frame.mjs"

red_case "F-5" "去掉「discriminator 不得重说指标名」这一条" \
  gates/check_frame.mjs "不符" \
  "perl -0pi -e 's/const echoes = mt\\.find/const echoes = false \\&\\& mt.find/' src/gates/g-frame.mjs"

red_case "F-2" "兄弟读数范围退回整篇正文（全文快照上必然误伤）" \
  gates/check_frame.mjs "不符" \
  "perl -0pi -e 's/const window = containingSentence\\(b, a\\)/const window = b/' src/gates/g-frame.mjs"

# 〔F-3 换过一次〕原变异是「and 一律切开」，在加入**数字角色排除**之后
# 它不再造成可观测差异——切出来的半句没有效应量，本来就不算兄弟读数。
# 一个不再鉴别任何东西的红样本是空心的，换成两条真正会红的。
red_case "F-3" '数字角色排除被撤掉（研究数/p值/I² 又变成竞争读数）' \
  gates/check_frame.mjs "不符" \
  "perl -0pi -e 's/ROLE_EXCLUDE\\.some\\(r =>/false \\&\\& ROLE_EXCLUDE.some(r =>/' src/gates/g-frame.mjs"

red_case "F-4" '不带括号的置信区间不再屏蔽（区间上下界变成竞争读数）' \
  gates/check_frame.mjs "不符" \
  "python3 -c \"import pathlib;p=pathlib.Path('src/gates/g-frame.mjs');s=p.read_text(encoding='utf-8');s=s.replace(chr(92)+'bCI',chr(92)+'bZZZNOMATCH');p.write_text(s,encoding='utf-8')\""

red_case "F-6" '标识符里的数字又变回读数（CA 19-9 被当成两个数）' \
  gates/check_frame.mjs "不符" \
  "perl -0pi -e 's/if \\(looksLikeIdentifier\\(before, m\\[0\\], after\\)\\) continue/if (false) continue/' src/gates/g-frame.mjs"

red_case "F-7" '标识符只排掉左半截（CA 19-|9| 的 9 仍算读数）' \
  gates/check_frame.mjs "不符" \
  "perl -0pi -e 's{/\\[A-Za-z\\]\\\\s\\*\\[\\\\d\\.\\]\\+-\\\$/\\.test\\(before\\) \\|\\|}{false ||}' src/gates/g-frame.mjs"

# ── 留出集二逼出来的四条（§S23） ─────────────────────────────────────────
red_case "F-8" 'and 的切分退回「整段全有全无」（J-6 原形态）' \
  gates/check_frame.mjs "不符" \
  "python3 gates/mutants/frame-and-split-allornothing.py"

red_case "F-9" '科学计数法不再当作一个 token（10 与 8 变成两个读数）' \
  gates/check_frame.mjs "不符" \
  "perl -0pi -e 's/  SCI_NOTATION,\n//' src/gates/g-frame.mjs"

red_case "F-10" '千分位逗号不再保护（1,079 被切成 1 与 079）' \
  gates/check_frame.mjs "不符" \
  "perl -0pi -e 's/protectThousands\\(masked\\)/masked/' src/gates/g-frame.mjs"

red_case "F-11" '英文数词的计数用法守卫被撤（散文里的数词也算读数）' \
  gates/check_frame.mjs "不符" \
  "perl -0pi -e 's/if \\(EN_WORD_NUM\\.test\\(m\\[0\\]\\) &&/if (false \\&\\&/' src/gates/g-frame.mjs"

red_case "F-12" '角色排除退回「必须前缀 from / n =」（pooled three cohorts 漏网）' \
  gates/check_frame.mjs "不符" \
  "perl -0pi -e 's/\\{ why: .研究数\\/样本量., re: \\/\\(\\?:\\)\\//{ why: \\x27研究数\\/样本量\\x27, re: \\/\\\\bfrom\\\\s+\\\$\\//' src/gates/g-frame.mjs"

red_case "F-13" '载荷不再豁免角色排除（载荷是样本数时门看不到数）' \
  gates/check_frame.mjs "不符" \
  "perl -0pi -e 's/const myNums = numbersIn\\(mine, pv\\)/const myNums = numbersIn(mine)/' src/gates/g-frame.mjs"

red_case "C-4" '减号变体不再统一（上标负号 vs 连字符，J-3 原形态）' \
  gates/check_containment.mjs "不符" \
  "perl -0pi -e 's/const unifyMinus = .*/const unifyMinus = t => t/' src/gates/g-containment.mjs"

red_case "C-5" '科学计数法指数的空格不再折叠（10- 8 vs 10-8）' \
  gates/check_containment.mjs "不符" \
  "perl -0pi -e 's/const tightenExponent = .*/const tightenExponent = t => t/' src/gates/g-containment.mjs"

# ── 成本门 · 台账数字与实测的绑定（§S21） ────────────────────────────────
# 这道门守的是本仓库栽过五次的那一类：**抄进文档的数字**。
# 它必须对两个方向都敏感 —— 文档被改，和被抄的那个量本身被改。
red_case "K-1" '台账里的成本数被改（文档漂移）' \
  gates/check_cost.mjs "台账已过期" \
  "python3 gates/mutants/ledger-cost-drift.py"

red_case "K-2" '读全文的输入量退回写死的 22K（实测被绕过）' \
  gates/check_cost.mjs "台账已过期" \
  "python3 -c \"import pathlib,re;p=pathlib.Path('tests/external/cost-model.mjs');t=p.read_text();n=re.sub(r'const READ_IN = .*','const READ_IN = 22 * 1024',t,count=1);assert n!=t;p.write_text(n)\""

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
