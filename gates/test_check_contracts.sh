#!/usr/bin/env bash
# check_contracts.mjs 的负例套件（red-first）
#
# 一道从没红过的门不算证明有效——它可能因为定位不到分节标题而静默全绿。
# 本套件对每一类缺陷各造一个红样本，断言门**确实判红且退出码为 1**。
#
# 纪律：走真实入口（直接调门的 CLI，不 import 内部函数），用退出码判定。
# 一手教训 [E: GROUND-TRUTH-CORRECTIONS.md#C1]：前代 rigor 门只比对 metric 文件，
# 伪造一个 metric、无 dvc.yaml、无 transform、无原始数据 → exit 0 PASS。
# 文档宣称「门重执行」是假的。负例套件就是防这个的。

set -uo pipefail
cd "$(dirname "$0")/.."

GATE="gates/check_contracts.mjs"
SRC="01-CONTRACTS.md"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

pass=0
fail=0

# assert_exit <期望码> <说明> <文件>
assert_exit() {
  local want="$1" desc="$2" file="$3"
  node "$GATE" "$file" >/dev/null 2>&1
  local got=$?
  if [ "$got" -eq "$want" ]; then
    printf 'PASS  %-42s exit=%d\n' "$desc" "$got"
    pass=$((pass + 1))
  else
    printf 'FAIL  %-42s exit=%d 期望 %d\n' "$desc" "$got" "$want"
    fail=$((fail + 1))
  fi
}

echo "check_contracts 负例套件"
echo

# 绿样本：活文档必须过。若这条红了，后面的红样本全部无意义。
assert_exit 0 "绿样本 · 活文档" "$SRC"

# R-1 · 第七个状态值（V7.10）
#   规划文档里写出枚举外的状态符号，实现者会把它当真。
sed 's/ST-U/ST-W/g' "$SRC" > "$TMP/r1.md"
assert_exit 1 "红 R-1 · 引入第七个状态值 ST-W" "$TMP/r1.md"

# R-2 · flag 有词表无作用（V7.9 方向一）
#   一条 flag 被定义却没人消费 = 它永远不进判定，即 F-规则-2 说的「只打印不判定」。
grep -v '^| F-09 `preprint-only` | `step-down`' "$SRC" > "$TMP/r2.md"
assert_exit 1 "红 R-2 · F-09 从作用表消失" "$TMP/r2.md"

# R-3 · flag 被消费两遍（V7.9 方向二）—— 这是 C-1 的真实形态
#   F-14 曾同时被 S 2b 与 §7.3 降档表消费，两次条件不同，导致 ST-V 全局不可达。
awk '/^\| F-15 `ugc-source` \| `step-down`/{print; print} 1' "$SRC" > "$TMP/r3.md"
assert_exit 1 "红 R-3 · F-15 在作用表内重复" "$TMP/r3.md"

# R-4 · 作用表提到词表里不存在的 flag（V7.9 方向三）
sed 's/^| F-13 `unstable-decomposition` | `ceiling`/| F-99 `ghost-flag` | `ceiling`/' "$SRC" > "$TMP/r4.md"
assert_exit 1 "红 R-4 · 作用表出现词表外的 F-99" "$TMP/r4.md"

# R-5 · 聚合字段复活（V1.5）
#   「N 条断言已 verified」是把可信度产品变成计分板的第一步。
sed 's/^\*\*§0.1 产品是可信度/`pass_rate`: 交付物顶部的总体通过率\n\n**§0.1 产品是可信度/' "$SRC" > "$TMP/r5.md"
assert_exit 1 "红 R-5 · pass_rate 被定义为字段" "$TMP/r5.md"

# R-6 · 门自身被掏空（自指检查）
#   若有人删掉 §7.3 分节标题，定位就会失败。门必须报错，不能静默全绿。
sed 's/^### §7.3 flags/### 七点三 flags/' "$SRC" > "$TMP/r6.md"
assert_exit 1 "红 R-6 · §7.3 标题被改导致定位失败" "$TMP/r6.md"

echo
echo "$pass 通过 / $fail 失败"
[ "$fail" -eq 0 ]
