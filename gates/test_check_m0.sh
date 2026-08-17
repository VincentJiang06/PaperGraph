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

echo
echo "$pass 通过 / $fail 失败"
[ "$fail" -eq 0 ]
