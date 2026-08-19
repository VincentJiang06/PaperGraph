#!/usr/bin/env python3
"""变异体：把 `and` 的逐边界切分退回「整段全有全无」（J-6 的原形态）。"""
import pathlib, re, sys
p = pathlib.Path('src/gates/g-frame.mjs')
t = p.read_text(encoding='utf-8')
old = """  const splitAnd = seg => {
    const parts = seg.split(/\\sand\\s|\\s与\\s/)
    if (parts.length < 2) return [seg]
    const out = [parts[0]]
    for (let i = 1; i < parts.length; i++) {
      if (hasNum(parts[i - 1]) && hasNum(parts[i])) out.push(parts[i])
      else out[out.length - 1] += ' and ' + parts[i]
    }
    return out
  }"""
new = """  const splitAnd = seg => {
    const parts = seg.split(/\\sand\\s|\\s与\\s/)
    return parts.length > 1 && parts.every(hasNum) ? parts : [seg]
  }"""
if old not in t:
    print('变异体自检失败：找不到 splitAnd 的当前实现', file=sys.stderr); sys.exit(2)
p.write_text(t.replace(old, new, 1), encoding='utf-8')
