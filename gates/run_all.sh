#!/usr/bin/env bash
# 全部门 + 全部负例套件的单一入口。
#
# loop 设计里 harness_primitives 的第三条：「任何阶段的『做完了吗』都能被一条命令回答」。
# 这就是那条命令。退出码是唯一裁决——不要用管道接它，管道会把退出码换成管道末端的。
#
# 用法:  ./gates/run_all.sh [docs|negative|all|m0|everything|publish]
#
#   docs        文档层三道门（规范源自洽 / [E:] 指针 / 自述数字）
#   negative    负例套件（证明上面那些门会红）
#   all         docs + negative —— **默认**，也是「文档层是否绿」的信号
#   m0          loop 的 S0 阶段验收（M0 阻塞项实测记录）
#   everything  all + m0
#   publish     发布前门
#
# 为什么 m0 不在 all 里：S0 阶段未完成时 check_m0 **应该**是红的（那是它的职责），
# 但那会让 all 永远红，进而让「文档层绿了没」这个信号消失。
# 两个信号要分开——把一个尚未开始的阶段的红，混进一个已经完成的层的绿，是自找的噪声。
#
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

if [ "$SCOPE" = all ] || [ "$SCOPE" = everything ] || [ "$SCOPE" = gc0 ] || [ "$SCOPE" = docs ]; then
  run '规范源自洽门'      node gates/check_contracts.mjs
  run '[E:] 溯源指针门'   node gates/check_pointers.mjs
  run '自述数字门'        node gates/check_doc_metrics.mjs
fi

if [ "$SCOPE" = all ] || [ "$SCOPE" = everything ] || [ "$SCOPE" = s1 ]; then
  # 状态函数 S 的穷举 oracle。约 6 秒，550 万向量。
  # 它是本项目目前最强的一条证据：「S 是全函数」从断言变成了实测。
  run '状态函数 S · 穷举 oracle'   node gates/check_status_exhaustive.mjs
fi

if [ "$SCOPE" = all ] || [ "$SCOPE" = everything ] || [ "$SCOPE" = negative ]; then
  # 负例套件证明上面那些门会红。没有这一段，全绿不构成证据。
  run '负例套件 · 规范源自洽门'    ./gates/test_check_contracts.sh
  run '负例套件 · [E:] 指针门'     ./gates/test_check_pointers.sh
  run '负例套件 · M0 阻塞项门'     ./gates/test_check_m0.sh
fi

if [ "$SCOPE" = m0 ] || [ "$SCOPE" = everything ]; then
  # loop 的 S0 阶段验收。S0 未完成时它**应该**红——那是它在正确工作。
  run 'M0 阻塞项门（loop S0）'     node gates/check_m0.mjs
fi

if [ "$SCOPE" = publish ]; then
  run '发布前门'          node gates/check_publishable.mjs "${2:-.}"
fi

printf '\n════════════════════════════════════\n'
printf '%d/%d 门通过\n' "$((total - failed))" "$total"
[ "$failed" -eq 0 ] || printf '%d 道红\n' "$failed"
exit "$failed"
