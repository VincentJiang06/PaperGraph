#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
M0-1 复现脚本 · PDF 抽取库能否拿到颜色 / 字号 / 渲染模式 / 不透明度 / 图层

〔为什么存在〕S0 阶段的 M0-1 判定 design-changed，推翻了规划文档里的前提
「大多数 PDF 文本抽取库确实拿不到颜色/字号/图层」。但那次测量的脚本与夹具
生成在会话 scratchpad 下，**从未入库**——于是结论不可复验。R3 fix-audit 的
M0 门在默认全跑后把这件事判红了，这个文件是对它的根治：

  夹具由本文件用**纯 Python** 现场生成（零第三方依赖、无时间戳、字节确定），
  因此任何人在任何机器上都能从仓库本身重跑，不需要任何外部语料。

〔被检验的命题〕
  H0（规划文档原前提）：多数抽取库拿不到颜色/字号/图层。
  若 H0 为真，下表中 color / size / render_mode / opacity / layer 列应全部为 no。
  只要有一个库在某一属性上为 yes，H0 即被证伪——这就是本脚本的判红条件。

〔确定性〕输出按固定顺序排列，不含时间戳/路径/随机数。库版本**计入输出**：
  测量结果本就依赖库版本，版本变了哈希就该变，由人重新裁决，而不是被静默吞掉。
"""
import hashlib, io, sys, zlib

# ── 一、纯 Python 生成对抗 PDF ──────────────────────────────────────────
# 7 段文本：1 段真可见 + 6 段用不同手法隐藏。每段的 payload 都是唯一字符串，
# 便于在抽取结果里精确判定「这个库有没有把这段读出来」。
RUNS = [
    ("VISIBLE-BLACK-12PT",     "可见对照：黑色 12pt"),
    ("HIDDEN-WHITE-ON-WHITE",  "白底白字"),
    ("HIDDEN-TINY-01PT",       "0.1pt 极小字号"),
    ("HIDDEN-RENDERMODE-3",    "Tr 3 不可见渲染模式"),
    ("HIDDEN-UNDER-RECT",      "被不透明矩形覆盖"),
    ("HIDDEN-OFFPAGE",         "绘制在页面外"),
    ("HIDDEN-OCG-LAYER",       "OCG 可选内容组，默认 OFF"),
]

def build_pdf() -> bytes:
    content = "\n".join([
        # 1 可见黑色 12pt
        "BT /F1 12 Tf 0 0 0 rg 72 720 Td (VISIBLE-BLACK-12PT) Tj ET",
        # 2 白底白字（颜色隐藏）
        "BT /F1 12 Tf 1 1 1 rg 72 700 Td (HIDDEN-WHITE-ON-WHITE) Tj ET",
        # 3 0.1pt（字号隐藏）
        "BT /F1 0.1 Tf 0 0 0 rg 72 680 Td (HIDDEN-TINY-01PT) Tj ET",
        # 4 渲染模式 3 = 既不填充也不描边（渲染模式隐藏）
        "BT /F1 12 Tf 3 Tr 0 0 0 rg 72 660 Td (HIDDEN-RENDERMODE-3) Tj 0 Tr ET",
        # 5 先画字，再用不透明白矩形盖住（z 序隐藏）
        "BT /F1 12 Tf 0 0 0 rg 72 640 Td (HIDDEN-UNDER-RECT) Tj ET",
        "1 1 1 rg 68 634 220 22 re f",
        # 6 页面外（几何隐藏）
        "BT /F1 12 Tf 0 0 0 rg 72 -120 Td (HIDDEN-OFFPAGE) Tj ET",
        # 7 OCG 图层，文档默认 OFF（图层隐藏）
        "/OC /OC1 BDC",
        "BT /F1 12 Tf 0 0 0 rg 72 600 Td (HIDDEN-OCG-LAYER) Tj ET",
        "EMC",
    ]).encode("latin-1")

    objs = {}
    objs[1] = (b"<< /Type /Catalog /Pages 2 0 R /OCProperties << /OCGs [7 0 R] "
               b"/D << /OFF [7 0 R] /Order [7 0 R] >> >> >>")
    objs[2] = b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>"
    objs[3] = (b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources "
               b"<< /Font << /F1 5 0 R >> /Properties << /OC1 7 0 R >> >> /Contents 4 0 R >>")
    objs[4] = b"<< /Length " + str(len(content)).encode() + b" >>\nstream\n" + content + b"\nendstream"
    objs[5] = b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"
    objs[7] = b"<< /Type /OCG /Name (HiddenLayer) >>"

    out = io.BytesIO()
    out.write(b"%PDF-1.7\n%\xe2\xe3\xcf\xd3\n")
    offsets = {}
    for n in sorted(objs):
        offsets[n] = out.tell()
        out.write(str(n).encode() + b" 0 obj\n" + objs[n] + b"\nendobj\n")
    xref_at = out.tell()
    maxobj = max(objs) + 1
    out.write(b"xref\n0 " + str(maxobj).encode() + b"\n")
    out.write(b"0000000000 65535 f \n")
    for n in range(1, maxobj):
        if n in offsets:
            out.write(("%010d 00000 n \n" % offsets[n]).encode())
        else:                      # 6 号对象空缺，占位为 free
            out.write(b"0000000000 65535 f \n")
    # 无 /ID、无 /Info、无时间戳 —— 保证字节确定
    out.write(b"trailer\n<< /Size " + str(maxobj).encode() + b" /Root 1 0 R >>\nstartxref\n"
              + str(xref_at).encode() + b"\n%%EOF\n")
    return out.getvalue()


# ── 二、逐库探测：能拿到哪些属性 ────────────────────────────────────────
# 每个探测器返回 dict：属性名 -> 'yes' / 'no'，外加它读出的 payload 集合。
# 'yes' 的判据是**拿到了可用于判定隐藏的具体数值**，不是「API 里有这个名字」。

def probe_pdftotext(path):
    import subprocess, shutil
    if not shutil.which("pdftotext"):
        return None, set(), "未安装"
    r = subprocess.run(["pdftotext", "-q", path, "-"], capture_output=True)
    txt = r.stdout.decode("utf-8", "replace")
    found = {p for p, _ in RUNS if p in txt}
    # -bbox-layout 也只给几何，不给颜色/渲染模式/图层
    return {"color": "no", "size": "no", "render_mode": "no",
            "opacity": "no", "layer": "no"}, found, "仅纯文本"

def probe_pypdf(path):
    try:
        import pypdf
    except ImportError:
        return None, set(), "未安装"
    rd = pypdf.PdfReader(path)
    txt = rd.pages[0].extract_text() or ""
    found = {p for p, _ in RUNS if p in txt}
    # pypdf 的 visitor_operand_before 能看到原始算子（含 rg / Tf / Tr），
    # 但那是「自己重写一个解释器」，不是抽取 API 给出的属性。
    got = {"color": "no", "size": "no", "render_mode": "no", "opacity": "no", "layer": "no"}
    ops = []
    def visitor(op, args, cm, tm):
        ops.append(bytes(op))
    try:
        rd.pages[0].extract_text(visitor_operand_before=visitor)
        if b"rg" in ops: got["color"] = "raw-op"
        if b"Tf" in ops: got["size"] = "raw-op"
        if b"Tr" in ops: got["render_mode"] = "raw-op"
    except Exception:
        pass
    return got, found, f"版本 {pypdf.__version__}"

def probe_pdfplumber(path):
    try:
        import pdfplumber
    except ImportError:
        return None, set(), "未安装"
    with pdfplumber.open(path) as pdf:
        chars = pdf.pages[0].chars
    txt = "".join(c["text"] for c in chars)
    found = {p for p, _ in RUNS if p.replace("-", "") in txt.replace("-", "")}
    got = {
        "color":       "yes" if any(c.get("non_stroking_color") is not None for c in chars) else "no",
        "size":        "yes" if any("size" in c for c in chars) else "no",
        # pdfplumber 不暴露文本渲染模式与 OCG 归属
        "render_mode": "no",
        "opacity":     "no",
        "layer":       "no",
    }
    import pdfplumber as _p
    return got, found, f"版本 {_p.__version__}"

def probe_pymupdf(path):
    # 用 `pymupdf` 而非旧别名 `fitz`：后者会向 stderr 打弃用警告，
    # 而门把 stderr 一并计入哈希 —— 一条会随库版本漂移的哈希不稳定源。
    try:
        import pymupdf as fitz
    except ImportError:
        try:
            import fitz
        except ImportError:
            return None, set(), "未安装"
    doc = fitz.open(path)
    page = doc[0]
    spans = page.get_texttrace()
    txt = "".join(chr(ch[0]) for sp in spans for ch in sp.get("chars", []))
    found = {p for p, _ in RUNS if p.replace("-", "") in txt.replace("-", "")}
    keys = set().union(*[set(sp.keys()) for sp in spans]) if spans else set()
    got = {
        "color":       "yes" if "color" in keys else "no",
        "size":        "yes" if "size" in keys else "no",
        "render_mode": "yes" if "type" in keys else "no",
        "opacity":     "yes" if ("opacity" in keys or "alpha" in keys) else "no",
        "layer":       "yes" if "layer" in keys else "no",
    }
    ver = getattr(fitz, "__version__", None) or getattr(fitz, "VersionBind", "?")
    doc.close()
    return got, found, f"版本 {ver}"


def main():
    pdf = build_pdf()
    path = "/tmp/m0_1_adversarial.pdf"
    with open(path, "wb") as f:
        f.write(pdf)

    print("M0-1 复现 · PDF 抽取库属性可见性")
    print("=" * 72)
    print(f"夹具：纯 Python 生成，{len(pdf)} 字节，sha256 "
          f"{hashlib.sha256(pdf).hexdigest()}")
    print(f"内容：{len(RUNS)} 段文本 = 1 段可见 + {len(RUNS)-1} 段以不同手法隐藏")
    for p, why in RUNS:
        print(f"  · {p:<24} {why}")
    print()

    ATTRS = ["color", "size", "render_mode", "opacity", "layer"]
    probes = [("pdftotext", probe_pdftotext), ("pypdf", probe_pypdf),
              ("pdfplumber", probe_pdfplumber), ("PyMuPDF", probe_pymupdf)]

    print(f"{'库':<12} {'color':<8} {'size':<8} {'rendermode':<12} {'opacity':<9} {'layer':<7} 备注")
    print("-" * 72)
    yes_cells = []
    rows = []
    for name, fn in probes:
        got, found, note = fn(path)
        if got is None:
            print(f"{name:<12} {'—':<8} {'—':<8} {'—':<12} {'—':<9} {'—':<7} {note}")
            rows.append((name, None, found, note))
            continue
        cells = [got[a] for a in ATTRS]
        for a, v in zip(ATTRS, cells):
            if v == "yes":
                yes_cells.append(f"{name}.{a}")
        print(f"{name:<12} {cells[0]:<8} {cells[1]:<8} {cells[2]:<12} {cells[3]:<9} {cells[4]:<7} {note}")
        rows.append((name, got, found, note))

    print()
    print("各库读出的 payload（隐藏段被读出 = 该库看得见「不可见文本」）")
    print("-" * 72)
    for name, got, found, note in rows:
        if got is None:
            continue
        vis = "VISIBLE-BLACK-12PT" in found
        hid = sorted(p for p in found if p.startswith("HIDDEN"))
        print(f"{name:<12} 可见段 {'读到' if vis else '未读到'}；隐藏段读出 {len(hid)}/{len(RUNS)-1} 段")
        for h in hid:
            print(f"             + {h}")

    print()
    print("=" * 72)
    print("判定")
    print("-" * 72)
    print("H0（规划文档原前提）：大多数 PDF 文本抽取库拿不到颜色/字号/图层。")
    if yes_cells:
        print(f"H0 被证伪。以下 {len(yes_cells)} 个 (库, 属性) 组合直接给出可判定隐藏的数值：")
        for c in sorted(yes_cells):
            print(f"  · {c}")
        print()
        print("后果：以 H0 为前提的设计（把「隐藏文本检测」列为不可实现、")
        print("      或降级为 known limitation 写进文档）失去依据，必须改为 fail-closed 实现。")
        rc = 0
    else:
        print("H0 未被证伪：没有任何库给出可判定隐藏的属性数值。")
        print("（若本行出现，说明环境里能装的库全部缺席——这不是 H0 成立的证据，")
        print("  而是本次测量无效。请检查上表『未安装』标记。）")
        rc = 1
    return rc

if __name__ == "__main__":
    sys.exit(main())
