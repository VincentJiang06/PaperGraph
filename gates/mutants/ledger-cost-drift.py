#!/usr/bin/env python3
"""变异体：把台账 §S18 成本表里的一个数改掉，模拟「文档抄完之后再没跟着变」。

〔为什么是独立文件而不是一行内联命令〕这条变异要改的字符串里带 `$0.24`。
内联进 test_new_gates.sh 后要穿过 bash 双引号 + eval 两层解析，
`$0` 会在第二层被当成**位置参数**展开——变异静默变成空转，
而套件只会报「门放行了」。本仓库对承重证据的原话是：
**应当是入库的自包含脚本，而不是一条一次性命令。** 这里适用同一条。
"""
import pathlib, sys

p = pathlib.Path('07-ATTACK-LEDGER.md')
t = p.read_text(encoding='utf-8')
old, new = '离峰 · 无缓存 | $0.24', '离峰 · 无缓存 | $0.31'
if old not in t:
    print(f'变异体自检失败：台账里找不到 {old!r}（表被改过？）', file=sys.stderr)
    sys.exit(2)
p.write_text(t.replace(old, new, 1), encoding='utf-8')
