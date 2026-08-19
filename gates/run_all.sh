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
#   mutants     变异测试（慢；穷举 oracle 加了第三个合取项后约 10+ 分钟）
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
  # 状态函数 S 的穷举 oracle。约 60 秒，2778 万向量（维度增加后规模随之涨，见自述数字门）。
  # 它是本项目目前最强的一条证据：「S 是全函数」从断言变成了实测。
  run '状态函数 S · 穷举 oracle'   node gates/check_status_exhaustive.mjs

  # 分工（R4 后确立）：穷举 oracle 管**性质**，规范符合性门管**映射**，
  # 变异测试**量化两者各自的辨别力**。任何一方单独绿灯都不构成「S 正确」的证据。
  # 实测：扩维让反例**可达**之后，针对新约束的变异体在 oracle 下**仍然全部存活**——
  # 因为删掉那些约束不破坏任何性质。**扩空间是必要条件，不是充分条件。**
  #
  # 〔R3 修复〕穷举 oracle 只断言**性质**（全函数/纯/单调/值域），不断言**映射**。
  # 变异测试实测：它对 15 个抬高状态的变异只击杀 6 个（40%）——删掉 0e 反例检索
  # 否决、清空整张 flag 表、让 K-I 直达 ST-V 全都活着。下面两道门补的正是那条缺口。
  run '规范符合性门（§1.5 黄金映射 + §7.3 绑定）' node gates/check_status_spec.mjs
  # 写者契约门：S 读的每个字段都不能是被检查方能写的（R5 第 5 条预测的守卫）
  run '写者契约门'        node gates/check_writer_contract.mjs
  run '负例套件 · 写者契约门'  bash gates/test_check_writer_contract.sh
  run '供给侧契约门'      node gates/check_supply_contract.mjs
  run '负例套件 · 本轮三道新门'   bash gates/test_new_gates.sh
  run '负例套件 · 供给侧契约门'  bash gates/test_check_supply_contract.sh

  # ── S2 · 产品层 ─────────────────────────────────────────────────────
  run 'profile 门（patch 生效值）'  node gates/check_profile.mjs
  run '取证插件门'        node gates/check_fetch_plugin.mjs
  run '归一化双实现对拍门'  node gates/check_normalize_parity.mjs
  run 'L1-c 极性作用域门'   node gates/check_polarity.mjs
  run 'G-CLUSTER 标定门'    node gates/check_cluster.mjs
  run 'G-CTR-SCAN X-2 门'   node gates/check_ctr_scan.mjs
  run '证据锚点门'          node gates/check_anchor.mjs
  run 'CAS 与证据卡门'      node gates/check_cas.mjs
  run '留存门'            node gates/check_retention.mjs
  run '结构化抓取门'        node gates/check_structured_fetch.mjs
  run '成本核算门'          node gates/check_cost.mjs
  run '归一化一致性门'      node gates/check_normalization.mjs
  run '锚点包含门'          node gates/check_containment.mjs
  run '同源竞争读数门'      node gates/check_frame.mjs
  run 'L1-c 外部标定集'     node tests/external/l1c-external.mjs
  run '外部标定测试(4 话题)' node tests/external/cases.mjs
  run '组稿器门'            node gates/check_composer.mjs
  run '端到端管线门'        node gates/check_pipeline_e2e.mjs
  run '全链路门（抓取→成稿）' node gates/check_full_chain.mjs
  run '编排层门（并行探索）' node gates/check_orchestrator.mjs
  run '顶层研究门'          node gates/check_research.mjs
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

if [ "$SCOPE" = everything ] || [ "$SCOPE" = mutants ]; then
  # 变异测试：唯一能量化「门的辨别力」的机制。故不进 all。
  # 〔运行时间会随 oracle 维度增长〕加 frame_gate_passed 之后向量数翻倍
  # （2778 万 → 5557 万），这一档也随之翻倍。写死一个分钟数会腐，所以只说「慢」。
  run '变异测试（S 的门抓不抓得住错实现）' node gates/check_status_mutants.mjs
fi

if [ "$SCOPE" = publish ]; then
  run '发布前门'          node gates/check_publishable.mjs "${2:-.}"
fi

printf '\n════════════════════════════════════\n'
printf '%d/%d 门通过\n' "$((total - failed))" "$total"

# 落一份统计工件，供自述数字门比对 README 里的「N/N 全绿」。
# 〔为什么要落工件而不是让 doc_metrics 自己数〕数门的方式有很多种
# （数 run 行、数文件、按 scope 过滤），每一种都会和实际跑的那一套漂移。
# 唯一不会漂的是**这次真的跑了几道**——所以由跑的人来记。
if [ "$SCOPE" = all ]; then
  printf '{"scope":"all","total":%d,"passed":%d}\n' "$total" "$((total - failed))" \
    > "$(dirname "$0")/.gate-stats.json"
fi
[ "$failed" -eq 0 ] || printf '%d 道红\n' "$failed"
exit "$failed"
