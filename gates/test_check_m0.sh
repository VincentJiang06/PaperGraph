#!/usr/bin/env bash
# check_m0.mjs 的负例套件（red-first）
#
# 最要紧的一条是 R-3：loop 设计给 S0 阶段写的 passing_but_wrong 是
#   「七份文件全部凭推理写成 verdict=resolved（『按代码应该是这样』），一次都没真跑」。
# 排除它的机制是「抽一条重跑、比对 raw_output_sha256」。R-3 就是这条机制的证明——
# 造一份哈希编造的 resolved 记录，断言门判红。这条过不了，S0 的验收判据就是空的。

set -uo pipefail
cd "$(dirname "$0")/.."
SRC="$PWD"
GATE="$SRC/gates/check_m0.mjs"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/.loop/m0"

pass=0
fail=0

assert_exit() {
  local want="$1" desc="$2"
  shift 2
  node "$GATE" --root "$TMP" "$@" >/dev/null 2>&1
  local got=$?
  if [ "$got" -eq "$want" ]; then
    printf 'PASS  %-48s exit=%d\n' "$desc" "$got"
    pass=$((pass + 1))
  else
    printf 'FAIL  %-48s exit=%d 期望 %d\n' "$desc" "$got" "$want"
    fail=$((fail + 1))
  fi
}

# 造一份**合格**的记录集：12 条全 still-blocked（不需要 evidence），加一条真实可重跑的 resolved
seed_valid() {
  rm -f "$TMP/.loop/m0"/*.json
  for id in M0-1 M0-2 M0-2b M0-3a M0-3b M0-3c M0-4 M0-5 M0-6 M0-7 C-12a C-12b; do
    cat > "$TMP/.loop/m0/$id.json" <<EOF
{
  "id": "$id",
  "question": "占位问题：$id 到底在问什么",
  "verdict": "still-blocked",
  "answer": "本机暂不可测",
  "evidence": [],
  "affects": ["00-PREMISE.md §M0"],
  "doc_action": "none",
  "honest_limits": "这是负例套件用的占位记录，本机缺少完成该实测所需的条件，未做任何真实测量。"
}
EOF
  done
}

# 一条真实的 resolved：命令确定性、哈希真算
seed_real_resolved() {
  local out="$TMP/real.txt"
  ( cd "$TMP" && echo "deterministic probe output" ) > "$out" 2>&1
  local h
  h=$(shasum -a 256 "$out" | awk '{print $1}')
  cat > "$TMP/.loop/m0/M0-3a.json" <<EOF
{
  "id": "M0-3a",
  "question": "M1 插件 inject 的确切服务名",
  "verdict": "resolved",
  "answer": "占位：实测得到的服务名",
  "evidence": [
    {
      "command": "echo 'deterministic probe output'",
      "cwd": "~",
      "raw_output_sha256": "$h",
      "excerpt": "deterministic probe output"
    }
  ],
  "affects": ["02-ARCHITECTURE.md §A.3"],
  "doc_action": "none",
  "honest_limits": "占位记录，仅用于验证本门的重跑机制。"
}
EOF
}

echo "check_m0 负例套件"
echo

# 绿样本
seed_valid
seed_real_resolved
assert_exit 0 "绿样本 · 记录齐全 + 一条真实 resolved"

# R-1 · 空集
rm -f "$TMP/.loop/m0"/*.json
assert_exit 2 "红 R-1 · 空集（0 条记录）拒绝给绿灯"

# R-2 · 缺记录
seed_valid; seed_real_resolved
rm -f "$TMP/.loop/m0/M0-5.json"
assert_exit 1 "红 R-2 · 少一条阻塞项记录"

# R-3 · **本套件的核心**：凭推理写 resolved，哈希是编的
#   loop 设计的 passing_but_wrong 就是这一条。
seed_valid
cat > "$TMP/.loop/m0/M0-4.json" <<'EOF'
{
  "id": "M0-4",
  "question": "run_code 是否可达 node:fs",
  "verdict": "resolved",
  "answer": "按代码应该是可达的",
  "evidence": [
    {
      "command": "echo 'deterministic probe output'",
      "cwd": "~",
      "raw_output_sha256": "0000000000000000000000000000000000000000000000000000000000000000",
      "excerpt": "deterministic probe output"
    }
  ],
  "affects": ["01-CONTRACTS.md §0.2"],
  "doc_action": "none",
  "honest_limits": "无"
}
EOF
assert_exit 1 "红 R-3 · resolved 但哈希编造（重跑对不上）"

# R-4 · resolved 却没有 evidence（最赤裸的「凭推理」形态）
seed_valid
cat > "$TMP/.loop/m0/M0-4.json" <<'EOF'
{
  "id": "M0-4",
  "question": "run_code 是否可达 node:fs",
  "verdict": "resolved",
  "answer": "读代码得出：可达",
  "evidence": [],
  "affects": ["01-CONTRACTS.md §0.2"],
  "doc_action": "none",
  "honest_limits": "无"
}
EOF
assert_exit 1 "红 R-4 · resolved 但零 evidence"

# R-5 · design-changed 却没说要改文档
seed_valid; seed_real_resolved
cat > "$TMP/.loop/m0/C-12a.json" <<'EOF'
{
  "id": "C-12a",
  "question": "出厂呈现模式假设是否成立",
  "verdict": "design-changed",
  "answer": "headless bundle 整键替换了 tools 行，native 假设不成立",
  "evidence": [],
  "affects": ["02-ARCHITECTURE.md §C"],
  "doc_action": "none",
  "honest_limits": "无"
}
EOF
assert_exit 1 "红 R-5 · design-changed 但 doc_action 不是 needed"

# R-6 · 记录里留了本机绝对路径（仓库是 public 的）
seed_valid; seed_real_resolved
# 注意：这里**拼**出违规路径，不写字面量。
# 发布前的脱敏脚本会把 `/Users/<name>/` 形态的字面量重写成 `~/`——
# 包括写在负例夹具里的那一个。那会让这个红样本不再含违规内容，门正确放行、测试失败。
# 夹具需要的恰恰是被禁的模式，所以必须躲开脱敏的正则。
node -e '
const f=process.argv[1], j=JSON.parse(require("fs").readFileSync(f,"utf8"));
j.evidence[0].cwd=["", "Users", "someone", "playground", "x"].join("/");
require("fs").writeFileSync(f, JSON.stringify(j,null,1));
' "$TMP/.loop/m0/M0-3a.json"
assert_exit 1 "红 R-6 · 记录含本机绝对路径"

# R-7 · 破坏性命令（不可重跑，raw_output_sha256 失去意义）
seed_valid
cat > "$TMP/.loop/m0/M0-2b.json" <<'EOF'
{
  "id": "M0-2b",
  "question": "多帧 zstd 的实际行为",
  "verdict": "resolved",
  "answer": "占位",
  "evidence": [
    {
      "command": "rm -rf /tmp/probe && zstd -dc x.zst",
      "cwd": "~",
      "raw_output_sha256": "1111111111111111111111111111111111111111111111111111111111111111",
      "excerpt": "占位"
    }
  ],
  "affects": ["02-ARCHITECTURE.md §E"],
  "doc_action": "none",
  "honest_limits": "无"
}
EOF
assert_exit 1 "红 R-7 · 实测命令含破坏性操作"

# R-8 · still-blocked 但没说清缺什么条件（等同于放弃）
seed_valid; seed_real_resolved
node -e '
const f=process.argv[1], j=JSON.parse(require("fs").readFileSync(f,"utf8"));
j.honest_limits="测不了";
require("fs").writeFileSync(f, JSON.stringify(j,null,1));
' "$TMP/.loop/m0/M0-5.json"
assert_exit 1 "红 R-8 · still-blocked 但未说清缺什么条件"

# R-9 · 豁免不能用来洗白整份记录
#   门允许证据显式声明「不可逐字节复现」（LLM 输出、随目录增长的扫描等），
#   而且声明后就不再查它的可跑性——这是一个真实的口子。
#   守住它的是「resolved 必须**至少有一条**真正可复现的证据」：
#   否则重跑验证无事可做，这份 resolved 与凭推理写的没有区别。
seed_valid
cat > "$TMP/.loop/m0/M0-4.json" <<'EOF'
{
  "id": "M0-4",
  "question": "run_code 是否可达 node:fs",
  "verdict": "resolved",
  "answer": "可达",
  "evidence": [
    {
      "command": "某个跑不了的命令 <scratch>/x",
      "cwd": "~",
      "reproducible": false,
      "irreproducible_reason": "夹具在会话临时目录中，已销毁，不可原样重跑",
      "raw_output_sha256": "(不可复现)",
      "excerpt": "看起来很像证据的一段文字"
    },
    {
      "command": "另一个也跑不了的命令",
      "cwd": "~",
      "reproducible": false,
      "irreproducible_reason": "LLM 生成内容，逐字不可复跑比对",
      "raw_output_sha256": "(不可复现)",
      "excerpt": "又一段看起来很像证据的文字"
    }
  ],
  "affects": ["01-CONTRACTS.md §0.2"],
  "doc_action": "none",
  "honest_limits": "无"
}
EOF
assert_exit 1 "红 R-9 · resolved 但全部证据都被豁免"

# ── R3 fix-audit 新增的三条 ─────────────────────────────────────────────
# 这三条对应本轮补上的三个洞。审计逐条实证过它们在修复前是绿的：
# 「12 条记录全部改写成纯编造的 design-changed，门仍 exit 0、8/8 全绿」。

# R-10 · design-changed 也必须有证据
#   原实现只有 resolved 要求 evidence，design-changed 完全豁免。
#   而 design-changed 的语义是「我实测了，且实测推翻了一条设计前提」——
#   它会引发文档改写，承重比 resolved 更大。12 份记录里 6 份落在这个豁免里。
seed_valid
cat > "$TMP/.loop/m0/M0-1.json" <<'EOF'
{
  "id": "M0-1",
  "question": "PDF 抽取库能否拿到颜色/字号/图层",
  "verdict": "design-changed",
  "answer": "拿得到，原前提被推翻",
  "evidence": [],
  "affects": ["01-CONTRACTS.md §7.2.2"],
  "doc_action": "needed —— §7.2.2 的抽取库描述必须改",
  "doc_action_detail": "写得非常详尽，看起来完全像做过实测",
  "honest_limits": "无"
}
EOF
assert_exit 1 "红 R-10 · design-changed 但零 evidence"

# R-11 · 陈旧 output_file 不构成重跑证据
#   攻击：命令必然失败 + output_file 指向一个**早已存在**的文件。
#   门原本会哈希那个陈旧文件、对上、打印「重跑验证 1/1 条哈希对上」并 PASS。
#   守住它的是**事前控制**：跑命令前先把 declared 目标移走。
#   〔R4 修复〕本样本原用 `this-command-does-not-exist-and-will-fail` 作命令，
#   于是它因**退出码断言**先判红——红样本是**过定的**（over-determined），
#   证明的是 R-12 的机制而不是新鲜度。实证：把新鲜度断言整块停用，套件仍 14/0。
#   现改用 `true`（退出 0、无输出），使本样本只能被事前控制抓住。
seed_valid
STALE="$TMP/stale-output.txt"
printf 'pretending to be the measured output\n' > "$STALE"
# 让它显著地「旧」，避免与本次运行的时刻相撞
touch -t 202001010000 "$STALE"
STALE_HASH="$(shasum -a 256 "$STALE" | cut -d' ' -f1)"
cat > "$TMP/.loop/m0/M0-5.json" <<EOF
{
  "id": "M0-5",
  "question": "某个前提是否成立",
  "verdict": "resolved",
  "answer": "成立",
  "evidence": [
    {
      "command": "true",
      "cwd": "~",
      "output_file": "$STALE",
      "raw_output_sha256": "$STALE_HASH",
      "excerpt": "pretending to be the measured output"
    }
  ],
  "affects": ["01-CONTRACTS.md §1.1"],
  "doc_action": "none",
  "honest_limits": "无"
}
EOF
assert_exit 1 "红 R-11 · 陈旧 output_file 冒充重跑（命令成功退出）"

# R-11b · `touch` 绕过（R4 实证的原漏洞）
#   原实现比对 mtime，而 mtime 是**被测方能写的**：command 写成 `touch <陈旧文件>`
#   即可让 2020 年的伪造文件冒充「本次运行产出」，门打印「25/25 哈希对上」并 PASS。
#   教训：任何「事后观察某个属性」的判据，只要那个属性在被测方的写权限内，就不是判据。
seed_valid
STALE2="$TMP/stale2.txt"
printf 'pretending to be the measured output\n' > "$STALE2"
touch -t 202001010000 "$STALE2"
STALE2_HASH="$(shasum -a 256 "$STALE2" | cut -d' ' -f1)"
cat > "$TMP/.loop/m0/M0-5.json" <<EOF
{
  "id": "M0-5",
  "question": "某个前提是否成立",
  "verdict": "resolved",
  "answer": "成立",
  "evidence": [
    {
      "command": "touch \"$STALE2\"",
      "cwd": "~",
      "output_file": "$STALE2",
      "raw_output_sha256": "$STALE2_HASH",
      "excerpt": "pretending to be the measured output"
    }
  ],
  "affects": ["01-CONTRACTS.md §1.1"],
  "doc_action": "none",
  "honest_limits": "无"
}
EOF
assert_exit 1 "红 R-11b · touch 刷新 mtime 冒充本次产出"

# R-13 · 默认必须全跑（夹具必须让「全跑」与「抽一条」可区分）
#   〔R4 修复〕原夹具只造**一条**可重跑证据，于是 rerunnable.length 恒为 1，
#   「全跑」与「抽一条」在夹具上**逐字节等价**——本轮最被强调的那条修复
#   （24/24 vs 1/11）因此完全没有回归保护。实证：把默认改回恒定抽样，套件仍 14/0。
#   本样本造**两条**可重跑证据，第一条真、第二条哈希编造。
#   恒定抽样会选中第一条并放行；全跑必然撞上第二条。
seed_valid
GOOD="$TMP/good.txt"
printf 'deterministic probe output\n' > "$GOOD"
GOOD_HASH="$(shasum -a 256 "$GOOD" | cut -d' ' -f1)"
cat > "$TMP/.loop/m0/M0-3a.json" <<EOF
{
  "id": "M0-3a",
  "question": "两条证据，第二条是编造的",
  "verdict": "resolved",
  "answer": "占位",
  "evidence": [
    {
      "command": "printf 'deterministic probe output\\n'",
      "cwd": "~",
      "raw_output_sha256": "$GOOD_HASH",
      "excerpt": "deterministic probe output"
    },
    {
      "command": "printf 'a different output entirely\\n'",
      "cwd": "~",
      "raw_output_sha256": "0000000000000000000000000000000000000000000000000000000000000000",
      "excerpt": "a different output entirely"
    }
  ],
  "affects": ["02-ARCHITECTURE.md §A.3"],
  "doc_action": "none",
  "honest_limits": "占位"
}
EOF
assert_exit 1 "红 R-13 · 第二条证据哈希编造（恒定抽样会漏掉）"

# R-13b · 同一份记录用 --sample 0 只抽第一条时会放行 —— 证明夹具真的可区分，
#         即 R-13 的红确实来自「全跑」而不是别的原因。
node "$GATE" --root "$TMP" --sample 0 >/dev/null 2>&1
if [ $? -eq 0 ]; then
  printf 'PASS  %-48s exit=0\n' "绿 R-13b · --sample 0 只抽第一条则放行（夹具可区分）"
  pass=$((pass + 1))
else
  printf 'FAIL  %-48s 期望 0\n' "绿 R-13b · --sample 0 只抽第一条则放行（夹具可区分）"
  fail=$((fail + 1))
fi

# R-14 · excerpt 必须真的来自重跑输出
#   〔R4/机器层 P1-7〕此前 excerpt 与 answer 与实测输出**完全无绑定**：
#   把 M0-1 的结论改成与实测**完全相反**、command 与 sha256 一字不动，
#   门打印「PASS，24/24 条哈希对上」，退出码 0。
#   哈希证明的是命令跑过；而记录里唯一被人读、唯一驱动文档改写的那部分不受约束。
#   **R3 把编造从 verdict 层赶走，编造原样搬进了 excerpt 层。**
seed_valid
cat > "$TMP/.loop/m0/M0-3a.json" <<'EOF'
{
  "id": "M0-3a",
  "question": "某个前提是否成立",
  "verdict": "resolved",
  "answer": "成立",
  "evidence": [
    {
      "command": "printf 'deterministic probe output\n'",
      "cwd": "~",
      "raw_output_sha256": "REPLACE_HASH",
      "excerpt": "完全捏造的一行，输出里根本没有"
    }
  ],
  "affects": ["02-ARCHITECTURE.md §A.3"],
  "doc_action": "none",
  "honest_limits": "占位"
}
EOF
GOODH="$(printf 'deterministic probe output\n' | shasum -a 256 | cut -d' ' -f1)"
node -e '
const fs=require("fs");const p=process.argv[1];
fs.writeFileSync(p, fs.readFileSync(p,"utf8").replace("REPLACE_HASH", process.argv[2]));
' "$TMP/.loop/m0/M0-3a.json" "$GOODH"
assert_exit 1 "红 R-14 · 哈希对得上但 excerpt 是捏造的"

# R-14b · excerpt 逐字来自输出时必须放行（防过修：门不能要求 excerpt 等于全部输出）
seed_valid
cat > "$TMP/.loop/m0/M0-3a.json" <<'EOF'
{
  "id": "M0-3a",
  "question": "某个前提是否成立",
  "verdict": "resolved",
  "answer": "成立",
  "evidence": [
    {
      "command": "printf 'line one\nline two\nline three\n'",
      "cwd": "~",
      "raw_output_sha256": "REPLACE_HASH2",
      "excerpt": "line two"
    }
  ],
  "affects": ["02-ARCHITECTURE.md §A.3"],
  "doc_action": "none",
  "honest_limits": "占位"
}
EOF
GOODH2="$(printf 'line one\nline two\nline three\n' | shasum -a 256 | cut -d' ' -f1)"
node -e '
const fs=require("fs");const p=process.argv[1];
fs.writeFileSync(p, fs.readFileSync(p,"utf8").replace("REPLACE_HASH2", process.argv[2]));
' "$TMP/.loop/m0/M0-3a.json" "$GOODH2"
assert_exit 0 "绿 R-14b · excerpt 是输出的真子集则放行"

# R-12 · 命令非零退出却未声明 exit_code
#   原实现把退出码 catch 进 err 后**从未检查**。捕获了异常却不断言，等于没捕获。
#   合法的非零退出（grep 无命中、被测门本就该判红）必须写进记录变成可检验断言。
seed_valid
cat > "$TMP/.loop/m0/M0-6.json" <<'EOF'
{
  "id": "M0-6",
  "question": "某个前提是否成立",
  "verdict": "resolved",
  "answer": "成立",
  "evidence": [
    {
      "command": "printf 'x\\n'; exit 3",
      "cwd": "~",
      "raw_output_sha256": "73cb3858a687a8494ca3323053016282f3dad39d42cf62ca4e79dda2aac7d9ac",
      "excerpt": "x"
    }
  ],
  "affects": ["01-CONTRACTS.md §1.1"],
  "doc_action": "none",
  "honest_limits": "无"
}
EOF
assert_exit 1 "红 R-12 · 命令非零退出却未声明 exit_code"

# R-12b · 声明了正确的 exit_code 就该放行（防止上一条变成「禁止非零退出」的过修）
seed_valid
cat > "$TMP/.loop/m0/M0-6.json" <<'EOF'
{
  "id": "M0-6",
  "question": "某个前提是否成立",
  "verdict": "resolved",
  "answer": "成立",
  "evidence": [
    {
      "command": "printf 'x\\n'; exit 3",
      "cwd": "~",
      "exit_code": 3,
      "raw_output_sha256": "73cb3858a687a8494ca3323053016282f3dad39d42cf62ca4e79dda2aac7d9ac",
      "excerpt": "x"
    }
  ],
  "affects": ["01-CONTRACTS.md §1.1"],
  "doc_action": "none",
  "honest_limits": "无"
}
EOF
assert_exit 0 "绿 R-12b · 非零退出但已声明 exit_code"

echo
echo "$pass 通过 / $fail 失败"
[ "$fail" -eq 0 ]
