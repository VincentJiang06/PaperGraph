#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
M0-2 复现脚本 · §1.2.2 归一化算法不保子串

〔为什么存在〕S0 的 M0-2 判定 design-changed，推翻了「quote_faithful 可 100% 兑现」
这条产品承诺，并驱动 §1.2.2 的中文规则从「按整串是否含 CJK 分支」改写为
「凡与 CJK 相邻的空白一律删除、不按语言分支」（见 01-CONTRACTS §1.2.2.0）。
原测量的 repro_norm_bugs.py 自称「两条缺陷的最小自包含复现」，但它生成在会话
scratchpad 下、从未入库，随会话销毁。本文件是对它的重建。

〔被检验的命题〕
  H1：§1.2.2 的**原**中文规则保证「原始子串 ⇒ 归一化后仍是子串」。
  若 H1 为真，下表 as_written 列不应出现 FAIL。
  出现任一 FAIL 即证伪 H1 —— 即「100% 兑现」在算法层面就不成立，
  与抽取管线质量无关。

〔零依赖〕纯标准库，无第三方语料，无网络，字节确定。
"""
import re, sys, unicodedata

CJK = r'㐀-䶿一-鿿豈-﫿　-〿＀-￯'
CJK_RE = re.compile(f'[{CJK}]')

IDENTITY = lambda x: x

def base_normalize(s: str) -> str:
    """§1.2.2 的公共前段：NFKC → 统一引号/破折号/省略号 → 折叠空白。"""
    s = unicodedata.normalize('NFKC', s)
    for a, b in [('“', '"'), ('”', '"'), ('‘', "'"), ('’', "'"),
                 ('—', '-'), ('–', '-'), ('…', '...')]:
        s = s.replace(a, b)
    return re.sub(r'\s+', ' ', s).strip()

def zh_rule_original(s: str) -> str:
    """〔已被证伪〕原规则：**按整串是否含 CJK** 决定要不要整串去空白。"""
    s = base_normalize(s)
    if CJK_RE.search(s):          # ← 这一行就是缺陷的全部
        s = re.sub(r'\s+', '', s)
    return s

def zh_rule_fixed(s: str) -> str:
    """〔现规范〕凡与 CJK 字符相邻的空白一律删除，**不按语言分支**。"""
    s = base_normalize(s)
    s = re.sub(f'(?<=[{CJK}])\\s+', '', s)   # CJK 之后的空白
    s = re.sub(f'\\s+(?=[{CJK}])', '', s)    # CJK 之前的空白
    return s

def dehyphenate(s: str) -> str:
    """PDF 专项：跨行连字符还原。**上下文相关重写** —— 这正是 BUG 2 的根源。"""
    return re.sub(r'(\w)-\s*\n\s*(\w)', r'\1\2', s)

# ── 用例 ────────────────────────────────────────────────────────────────
# 每条：(编号, 说明, 快照文本, 引语, 走连字符还原, 期望(raw, as_written, fixed))
#
# 〔期望值从哪来〕全部是 S0 记录 .loop/m0/M0-2.json 的逐字结论。本脚本因此
# 不是「跑完看看输出」，而是一条**回归断言**：任何一格偏离期望即退出 1。
# 特别注意 BUG-2 的期望是 (True, False, False) —— 原记录明写「两种规则都
# pass=False」，即**现行 §1.2.2 并没有修好跨行连字符这一条**。把它写成期望
# 而不是悄悄改成 PASS，是为了让这条已知未修项在门里始终可见。
CASES = [
    ("BUG-1", "中文文档里的纯英文引语（原规则非对称：快照侧去空白、引语侧保留）",
     "本文提出的方法 optimal transport 在数据集上取得了最好效果。",
     "optimal transport", False, (True, False, True)),

    ("BUG-1b", "同上，引语含多个空格时失配更明显",
     "我们在 machine reading comprehension 任务上做了评测。",
     "machine reading comprehension", False, (True, False, True)),

    # 关键：引语**截断在还原窗口内**（止于连字符），不含还原所需的后半词。
    # 于是还原规则在快照侧生效（Rus- + sian → Russian）、在引语侧不生效
    # （其后无词字符可匹配），连字符被留下 —— 两种规则都必然失配。
    # 〔自我更正〕初版把引语写成 "Rus-\nsian"（含后半词），两侧都被还原，
    # 于是通过 —— 那是原缺陷的一个更弱的改写版，不是复现。
    ("BUG-2", "跨行连字符还原窗口内被截断的引语（止于连字符）",
     "We evaluate on German, Arabic, Rus-\nsian and Chinese corpora.",
     "German, Arabic, Rus-\n", True, (True, False, False)),

    ("ZH-OK", "纯中文引语（两种规则都该通过，用作对照）",
     "本文提出的方法在数据集上取得了最好效果。",
     "在数据集上取得了最好效果", False, (True, True, True)),

    ("EN-GUARD", "纯英文文档里的英文引语 —— 修复不得误伤（防止「一律删空白」的过修）",
     "We report the rate of convergence for each optimizer.",
     "the rate of convergence", False, (True, True, True)),

    ("MIX-GUARD", "中英混排里含内部空格的英文引语，修复后必须仍能命中",
     "如表 3 所示，the rate of convergence 明显优于基线。",
     "the rate of convergence", False, (True, False, True)),
]

def check(snapshot, quote, rule, use_dehyph):
    # raw 基线的定义是「完全不归一化」——跨行连字符还原属于 §1.2.2 的 PDF 专项
    # 归一化，因此**不**施加于 raw。〔自我更正〕初版把还原也套在 raw 上，
    # 于是 BUG-2 的 raw 显示 FAIL，与 S0 记录的 `raw substring=True` 不符。
    if use_dehyph and rule is not IDENTITY:
        snapshot, quote = dehyphenate(snapshot), dehyphenate(quote)
    return rule(quote) in rule(snapshot)

def main():
    print("M0-2 复现 · §1.2.2 归一化是否保子串")
    print("=" * 78)
    print("raw        = 未归一化时，引语是否为快照的逐字子串（基线，应为 True）")
    print("as_written = 套上**原** §1.2.2 中文规则后是否仍命中")
    print("fixed      = 套上**现** §1.2.2（相邻-CJK 去空白，不分支）后是否仍命中")
    print()
    print(f"{'用例':<10} {'raw':<7} {'as_written':<12} {'fixed':<8} 说明")
    print("-" * 78)

    broke_h1, deviations, known_unfixed = [], [], []
    for cid, desc, snap, q, deh, exp in CASES:
        got = (check(snap, q, IDENTITY, deh),
               check(snap, q, zh_rule_original, deh),
               check(snap, q, zh_rule_fixed, deh))
        raw, old, new = got
        if raw and not old:
            broke_h1.append(cid)
        if raw and not new:
            known_unfixed.append(cid)
        if got != exp:
            deviations.append((cid, exp, got))
        f = lambda b: "PASS" if b else "FAIL"
        mark = "" if got == exp else "  ← 偏离 S0 期望 " + str(exp)
        print(f"{cid:<10} {f(raw):<7} {f(old):<12} {f(new):<8} {desc}{mark}")

    print()
    print("失配细节（原规则判 FAIL 的用例，逐字展开）")
    print("-" * 78)
    for cid, desc, snap, q, deh, exp in CASES:
        s2, q2 = (dehyphenate(snap), dehyphenate(q)) if deh else (snap, q)
        if q in snap and zh_rule_original(q2) not in zh_rule_original(s2):
            print(f"[{cid}]")
            print(f"  snapshot 原文  = {snap!r}")
            print(f"  quote    原文  = {q!r}")
            print(f"  快照 归一化后  = {zh_rule_original(s2)!r}")
            print(f"  引语 归一化后  = {zh_rule_original(q2)!r}")
            print(f"  → 快照侧被整串去空白，引语侧未被去（引语不含 CJK）——结构性不可能命中")
            print()

    print("=" * 78)
    print("判定")
    print("-" * 78)
    print("H1（原 §1.2.2）：归一化保子串，故 quote_faithful 可 100% 兑现。")
    if broke_h1:
        print(f"H1 被证伪。{len(broke_h1)} 条用例在未归一化时是逐字子串，"
              f"套上原规则后失配：{', '.join(broke_h1)}")
        print("根因：中文专项规则**按整串是否含 CJK 分支**，因此对")
        print("      「含 CJK 的快照 + 不含 CJK 的引语」这一组合是非对称的——")
        print("      快照侧被整串去空白，引语侧原样保留，永远不可能命中。")
        print("      这与抽取管线质量无关，是算法本身不保子串。")
    else:
        print("H1 未被证伪 —— 与 S0 记录不符，需要人工复查本脚本是否忠实实现了原规则。")
    print()
    if known_unfixed:
        print(f"**现行 §1.2.2 仍未修好**：{', '.join(known_unfixed)}")
        print("  BUG-2（跨行连字符还原窗口内被截断的引语）是 S0 记录里就已认账的未修项：")
        print("  还原是上下文相关重写，快照侧生效而引语侧不生效，两侧必然分叉。")
        print("  它不进入 fail，但必须在每次运行里可见 —— 一条被静默掉的已知缺陷")
        print("  会在下一次重构里被当成「本来就该这样」。")
    else:
        print("现 §1.2.2 在全部用例上恢复命中。")
    print("EN-GUARD / MIX-GUARD 证明修复没有误伤英文内部空格。")
    print()
    if deviations:
        print(f"FAIL：{len(deviations)} 格偏离 S0 记录的期望值 —— 本脚本或 §1.2.2 有一方变了。")
        for cid, exp, got in deviations:
            print(f"  {cid}: 期望 {exp} 实测 {got}")
        return 1
    print(f"PASS：{len(CASES)} 条用例 × 3 格全部与 .loop/m0/M0-2.json 的记录一致。")
    return 0 if broke_h1 else 1

if __name__ == "__main__":
    sys.exit(main())
