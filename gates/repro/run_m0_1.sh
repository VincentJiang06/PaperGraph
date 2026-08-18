#!/usr/bin/env bash
# M0-1 复现入口 · 从仓库根目录运行：bash gates/repro/run_m0_1.sh
#
# 〔为什么钉版本〕测量结果依赖抽取库版本。不钉版本，库一升级哈希就漂，
# M0 门会开始产出与结论无关的红——而产出噪声的门会被人学会忽略
# （03-EVIDENCE-ENGINE :63 逐字预言过这个失败模式）。
# 钉死之后，版本升级变成一次**显式的人工裁决**：改这里的 pin，重跑，重录哈希。
set -euo pipefail
cd "$(dirname "$0")/../.."

PIN_PYMUPDF=1.28.2
PIN_PYPDF=6.16.1
PIN_PDFPLUMBER=0.11.10
VENV=.venv-repro

need_bootstrap=1
if [ -x "$VENV/bin/python" ]; then
  if "$VENV/bin/python" - <<PY >/dev/null 2>&1
import pymupdf, pypdf, pdfplumber, sys
sys.exit(0 if (pymupdf.__version__.startswith("$PIN_PYMUPDF")
               and pypdf.__version__ == "$PIN_PYPDF"
               and pdfplumber.__version__ == "$PIN_PDFPLUMBER") else 1)
PY
  then need_bootstrap=0; fi
fi

if [ "$need_bootstrap" = 1 ]; then
  echo "[bootstrap] 建立 $VENV 并安装钉死版本…" >&2
  python3 -m venv "$VENV" >&2
  "$VENV/bin/pip" install -q --disable-pip-version-check \
    "pymupdf==$PIN_PYMUPDF" "pypdf==$PIN_PYPDF" "pdfplumber==$PIN_PDFPLUMBER" >&2
fi

exec "$VENV/bin/python" gates/repro/m0_1_pdf_attributes.py
