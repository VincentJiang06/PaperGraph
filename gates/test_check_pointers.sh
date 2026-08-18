#!/usr/bin/env bash
# check_pointers.mjs 的负例套件（red-first）
#
# 这道门本身就是因为上一道门（check_contracts 的 D-1）被证明空心才存在的。
# 所以它自己更没有资格只靠"跑出来是绿的"来证明有效。
# 全部红样本在 ROOT 的临时副本上造，不动真实文件。

set -uo pipefail
cd "$(dirname "$0")/.."
SRC="$PWD"

GATE="$SRC/gates/check_pointers.mjs"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# 只复制门需要读的东西
mkdir -p "$TMP/research" "$TMP/.attack"
cp ./*.md "$TMP/" 2>/dev/null
cp -R research/v2 "$TMP/research/"
cp .attack/pointer-debt.json "$TMP/.attack/"
# 门现在还会检查 [E:] 指向的**仓库内文件**是否存在（S0 实测记录 .loop/m0/*.json、
# 复现脚本 gates/repro/*）。夹具不带上它们，绿样本会因为「文件不存在」误红。
mkdir -p "$TMP/.loop/m0" "$TMP/gates/repro"
cp .loop/m0/*.json "$TMP/.loop/m0/" 2>/dev/null
cp gates/repro/* "$TMP/gates/repro/" 2>/dev/null

pass=0
fail=0

assert_exit() {
  local want="$1" desc="$2"
  node "$GATE" --root "$TMP" >/dev/null 2>&1
  local got=$?
  if [ "$got" -eq "$want" ]; then
    printf 'PASS  %-46s exit=%d\n' "$desc" "$got"
    pass=$((pass + 1))
  else
    printf 'FAIL  %-46s exit=%d 期望 %d\n' "$desc" "$got" "$want"
    fail=$((fail + 1))
  fi
}

restore() { cp "$SRC/$1" "$TMP/$1"; cp "$SRC/.attack/pointer-debt.json" "$TMP/.attack/"; }

echo "check_pointers 负例套件"
echo

# 绿样本：真实状态必须过。这条红了后面全部无意义。
assert_exit 0 "绿样本 · 当前树"

# R-1 · 新增指向不存在语料文件的指针
#   这正是旧 D-1 放过的那一类：[E: 我瞎编的.md#锚] 当时能过。
printf '\n垃圾行 [E: 完全不存在的文件.md#随便一个锚]\n' >> "$TMP/01-CONTRACTS.md"
assert_exit 1 "红 R-1 · 指针指向不存在的语料文件"
restore 01-CONTRACTS.md

# R-2 · 新增锚点找不到的指针（文件真实存在）
printf '\n垃圾行 [E: ext-evaluation.md#这个锚肯定不存在ZZZ]\n' >> "$TMP/01-CONTRACTS.md"
assert_exit 1 "红 R-2 · 锚点在真实文件里找不到"
restore 01-CONTRACTS.md

# R-3 · 棘轮反向：欠债还清却没销账
#   登记表若不同步就会腐 —— 一手教训 D3（前代攻击台账自身出现截断与重复）。
node -e '
const f=process.argv[1], j=JSON.parse(require("fs").readFileSync(f,"utf8"));
j.pointers["05-TESTING.md\t绝不会出现的目标.md#绝不会出现的锚"]=1; j.distinct=Object.keys(j.pointers).length;
require("fs").writeFileSync(f, JSON.stringify(j,null,1));
' "$TMP/.attack/pointer-debt.json"
assert_exit 1 "红 R-3 · 欠债登记表有已还清项未销账"
restore 01-CONTRACTS.md

# R-4 · 把 00-PREMISE 的裁决当证据引用
#   00-PREMISE 自陈「本文件是审计记录，不是证据源」。
printf '\n垃圾行 [E: 00-PREMISE.md#B1 裁决]\n' >> "$TMP/05-TESTING.md"
assert_exit 1 "红 R-4 · 把 00-PREMISE 裁决当证据引用"
restore 05-TESTING.md

# R-5 · 门自身被掏空：欠债表消失时必须报错，不能静默全绿
rm -f "$TMP/.attack/pointer-debt.json"
assert_exit 1 "红 R-5 · 欠债登记表缺失"
cp "$SRC/.attack/pointer-debt.json" "$TMP/.attack/"

# R-6 · 位置性锚不得被算作可解析
printf '\n垃圾行 [E: ext-evaluation.md#核验表末行]\n' >> "$TMP/01-CONTRACTS.md"
assert_exit 1 "红 R-6 · 位置性锚（随编辑漂移）"
restore 01-CONTRACTS.md

# ── R3 fix-audit 新增：棘轮键变宽后的三条 ────────────────────────────────
# 审计原文：「棘轮的键只由 (目标, 锚) 构成，**不含出处文档**……已登记 109 个
# 坏 pair 就是 109 张免死金牌：任何数量的**全新伪造引用**只要复用其中之一，
# 门恒绿。」下面三条各自钉死修复的一个面。

restore_tree() {
  rm -f "$TMP"/*.md
  cp "$SRC"/*.md "$TMP/" 2>/dev/null
  cp "$SRC/.attack/pointer-debt.json" "$TMP/.attack/"
}

# 取一条真实的已登记欠债（格式 `<出处文档>\t<目标>#<锚>`）
KNOWN_PAIR="$(node -e '
const d = require("'"$SRC"'/.attack/pointer-debt.json");
const k = Object.keys(d.pointers)[0];
process.stdout.write(k.split("\t")[1]);
')"

# R-8 · 在**另一份文档**里复用一条已登记的坏指针 → 必须红
#   这是免死金牌攻击的最小形态。旧键下它恒绿。
restore_tree
printf '\n伪造一条引用 [E: %s]。\n' "$KNOWN_PAIR" >> "$TMP/05-TESTING.md"
assert_exit 1 "红 R-8 · 在别的文档里复用已登记坏指针"

# R-9 · 在**同一份文档**里增加已登记坏指针的出现次数 → 必须红
#   多重集这一半：种类没变，次数变了。旧键（集合）下它同样恒绿。
restore_tree
DEBT_DOC="$(node -e '
const d = require("'"$SRC"'/.attack/pointer-debt.json");
process.stdout.write(Object.keys(d.pointers)[0].split("\t")[0]);
')"
printf '\n再引一次同一条 [E: %s]。\n' "$KNOWN_PAIR" >> "$TMP/$DEBT_DOC"
assert_exit 1 "红 R-9 · 同一文档内坏指针出现次数上升"

# R-10 · 少一个 .md 后缀的伪造引用 → 必须红
#   审计原文：「D-1 放过的是 [E: 我瞎编的.md#不存在的锚]；新门放过的是
#   [E: 我瞎编的#不存在的锚]（少一个 .md 后缀即可）。」
#   R-1 只覆盖了有 .md 后缀的那一半。
restore_tree
printf '\n伪造一条无后缀引用 [E: 00-PREMISE#根本不存在的锚点XYZ]。\n' >> "$TMP/05-TESTING.md"
assert_exit 1 "红 R-10 · 无 .md 后缀的伪造引用（原静默丢弃）"

# R-11 · 旧格式（数组）的欠债登记表必须被拒
#   防止有人把登记表回滚成旧格式来重新拿到免死金牌。
restore_tree
node -e '
const fs = require("fs");
const p = "'"$TMP"'/.attack/pointer-debt.json";
const d = JSON.parse(fs.readFileSync(p, "utf8"));
d.pointers = Object.keys(d.pointers).map(k => k.split("\t")[1]);
fs.writeFileSync(p, JSON.stringify(d, null, 1));
'
assert_exit 1 "红 R-11 · 欠债登记表回滚为旧的无出处格式"

restore_tree

# R-7 · 空集闸（vacuous truth）
#   扫到 0 个指针时必须以 exit 2 报错，不能因为「空集上两条棘轮断言都成立」而给绿灯。
#   实证来源：本仓库路径含空格（"Paper Graph"），`new URL(...).pathname` 把它编码成 %20，
#   门读不到任何文件、可解析率打印成 NaN%、然后全绿。这是这道门自己犯过的空心失败。
node "$GATE" --root /tmp >/dev/null 2>&1
got=$?
if [ "$got" -eq 2 ]; then
  printf 'PASS  %-46s exit=%d\n' "红 R-7 · 空集（0 个指针）拒绝给绿灯" "$got"
  pass=$((pass + 1))
else
  printf 'FAIL  %-46s exit=%d 期望 2\n' "红 R-7 · 空集（0 个指针）拒绝给绿灯" "$got"
  fail=$((fail + 1))
fi

echo
echo "$pass 通过 / $fail 失败"
[ "$fail" -eq 0 ]
