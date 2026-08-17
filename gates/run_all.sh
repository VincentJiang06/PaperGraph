#!/usr/bin/env bash
# 全部门 + 全部负例套件的单一入口。
#
# loop 设计里 harness_primitives 的第三条：「任何阶段的『做完了吗』都能被一条命令回答」。
# 这就是那条命令。退出码是唯一裁决——不要用管道接它，管道会把退出码换成管道末端的。
#
# 用法:  ./gates/run_all.sh [gc0|docs|negative|all]
# 退出码: 0 = 全绿，非零 = 红的门数

set -uo pipefail
cd "$(dirname "$0")/.."

SCOPE="${1:-all}"
failed=0
total=0

run() {
  local desc="$1"; shift
  total=$((total + 1))
  printf '\n━━ %s\n' "$desc"
  if "$@"; then
    return 0
  else
    failed=$((failed + 1))
    printf '   ↑ 红\n'
    return 1
  fi
}

if [ "$SCOPE" = all ] || [ "$SCOPE" = gc0 ] || [ "$SCOPE" = docs ]; then
  run '规范源自洽门'      node gates/check_contracts.mjs
  run '[E:] 溯源指针门'   node gates/check_pointers.mjs
  run '自述数字门'        node gates/check_doc_metrics.mjs
fi

if [ "$SCOPE" = all ] || [ "$SCOPE" = negative ]; then
  # 负例套件证明上面那些门会红。没有这一段，全绿不构成证据。
  run '负例套件 · 规范源自洽门'    ./gates/test_check_contracts.sh
  run '负例套件 · [E:] 指针门'     ./gates/test_check_pointers.sh
fi

if [ "$SCOPE" = publish ]; then
  run '发布前门'          node gates/check_publishable.mjs "${2:-.}"
fi

printf '\n════════════════════════════════════\n'
printf '%d/%d 门通过\n' "$((total - failed))" "$total"
[ "$failed" -eq 0 ] || printf '%d 道红\n' "$failed"
exit "$failed"
