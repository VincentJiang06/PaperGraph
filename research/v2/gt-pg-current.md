# GT — 前代系统 Paper Graph（post-reset 现状）一手真值

> 调研方法：**只读代码与工件本体**。项目根 `<repo>`（含空格）。
> 所有结论均给出 primary-source 文件路径 + 行号 + 逐字引文；凡我能执行验证的洞，
> 都在沙箱里**实跑复现**并附上真实输出（见 F-13/F-14/F-15）。
> 项目自身的 README/CHANGELOG/DESIGN 在本文中被当作**待核的二手声明**，与代码冲突处以代码为准。
> 读取日期：2026-08-17。仓库工作树状态：post-reset（2026-07-09 重置），最后活跃时间 2026-07-10。

---

## 结论摘要

1. **post-reset 系统只有 4 个可执行件**：`gates/rigor_gate.py`(196 行)、`gates/divergence_gate.py`(139 行)、
   `eval/harness.py`(222 行)、`eval/selftest.py`(51 行)——**合计 608 行**（`wc -l` 实测）。
   其余全部是 markdown 契约与 4 个真实 run 的产出。这个"极小控制面"本身是值得逐字继承的判断。

2. **文件契约（claims.tsv / positions.md / transforms / metrics / sources / dvc 接线）是这个系统最值钱的资产**，
   4 个跨领域 run + 1 个 smoke run 证明它跑得通、可跨学科（劳动经济/中世纪史/流行病学/能源物理）。
   7 列 TSV 表头在 5 个 run 中**逐字节一致**（md5 `1c2f0af6698d7b59366e1e2bc3d4067e`），
   契约稳定性是实测的而非声称的。

3. **但两个门 + eval harness 的代码几乎都是 fail-open 的，且我逐条实跑复现了**：
   - **rigor 门**：`dvc repro` 失败 / 根本没有 dvc.yaml / 没有 transform 脚本 / 没有原始数据，
     只要手写一个 `metrics/<cid>.json`，门就报 **`PASS ✅` 且 exit 0**。整个"可重跑"承诺可被一个 JSON 文件绕过。
   - **divergence 门**：一个 250 字符段落里塞 `[P1][P2][P3][P4][P5][OBJ]` → coverage 100%、engagement 100%、PASS。
     200 字符门槛是**按段落算、被所有 tag 共享**，不是 per-tag。
   - **eval harness**：`eval/verdicts/<slug>.json` 缺失时，D2/D3/D4b/D5 四个维度的 kill-criterion **全部静默跳过**，
     直接判 **SHIP**。`runs/black-death` 的 SHIP 就是这样来的——它**从未跑过任何主观面板**。

4. **量化过拟合的那个著名结论需要修正得更狠**：二手文档说"4/4 自家双门全绿，独立 eval 3/4 REVISE"。
   一手核对后应为：**4/4 双门全绿；独立 eval 3 个 REVISE + 1 个 fail-open 的假 SHIP；
   真正跑完 D1–D5 完整面板的只有 1 个（nuclear-safety），结论是 REVISE。
   即 0/4 真正拿到过发布裁决。**

5. **唯一正确的 fail-closed 范本 `skills/papergraph/scripts/validate_eval_bundle.py` 确实存在、确实正确、
   且确实从未接进 `eval/`**。grep 全仓：`eval/` 与 `gates/` 下**零引用**。它的五文件 bundle 契约
   （`d1_answer_key.json`/`d2_steelmans.json`/`d3_adversary.json`/`d4b_claim_audit.json`/`d5_referees.json`）
   与主 eval 实际消费的单文件 `eval/verdicts/<slug>.json` **完全不兼容**——同一契约裂成了两个权威，
   而跑的那个是错的那个。

6. **第三种 claim kind（逻辑推断）不是"没实现"，是"会被现有门主动判死"**：
   `gates/rigor_gate.py:152-153` 对任何非 data/source 的 kind 直接 `ok=False`，
   会把 reproduce-rate 拉到 100% 以下 → 门 FAIL。v2 必须把它设计成**第三条验证通道**，
   而它缺的东西（前提闭包、warrant 声明、结论强度不超前提、独立再推导 + 反例构造）
   在这个系统里一件都没有。nuclear-safety 的 D3 发现本质上就是一次**未被任何门捕获的推断失效**。

---

## 逐条事实

### A 组 — 文件契约（这部分值得原样继承）

**F-01 · claims.tsv 是 7 列 tab 分隔，表头逐字节固定**

一手来源 `gates/rigor.md:16-19`：

```
## The ledger — `runs/<slug>/claims.tsv` (tab-separated)
claim_id  kind  claim_text  value  raw_ref  transform_or_source  reproduced
```

实测：5 个 run（`_smoke`/`ai-employment`/`alcohol-jcurve`/`black-death`/`nuclear-safety`）的
表头行 md5 全部为 `1c2f0af6698d7b59366e1e2bc3d4067e`；所有数据行 `NF==7`，无一破格。

各列语义（`gates/rigor.md:20-32` 逐字）：
- `kind=data`：`value` = 论文写的数字（如 `4.8`/`16.3%`/`239`）；`raw_ref` = `data/…` 下的路径；
  `transform_or_source` = `transforms/<claim_id>.py`，"a deterministic, no-network script that
  reads the raw data and **writes `metrics/<claim_id>.json` = `{"value": <v>}`** as its product"。
- `kind=source`：`value` = **逐字引文**（源文本的精确子串）；`raw_ref` = 源 URL；
  `transform_or_source` = `sources/<claim_id>.txt`。
- `reproduced`：`gates/rigor.md:32` — "leave `?`; the gate is the record"。

**F-02 · 但 7 列里有 3 列门代码根本不读**

`gates/rigor_gate.py` 全文只消费 `col["claim_id"]`、`col["kind"]`、`col["value"]`，
以及**仅在 `--verify-sources` 分支下**的 `col["raw_ref"]`（:179）。

- `transform_or_source` — **零引用**。门在 :88 和 :123 里**硬编码**路径
  `run/"metrics"/f"{cid}.json"` 与 `run/"sources"/f"{cid}.txt"`，从不校验台账声明的路径是否就是它检查的那个文件。
- `raw_ref`（data 类）— 从不与 `dvc.yaml` 的 `deps` 比对。台账写 `data/foo.csv` 而 transform 实际读 `data/bar.csv`，门完全看不见。
- `reproduced` — 门既不读也不回写。文档说"门的输出才是记录"，代码层面这一列是**死列**。

> 设计含义：v2 的 `status` 列若要成立，必须由门**物理写入**，否则重蹈"声明了权威、代码没实现"的覆辙。

**F-03 · positions.md 的块格式（divergence 门解析的唯一结构）**

一手来源 `gates/divergence.md:13-25`：

```
## P1: <short position name>
holder: <who actually holds it — school/author/camp>
claim: <the position's core claim, one sentence, its strongest form>
rests_on: <the evidence or value it stands on>

## STRONGEST-OBJECTION
claim: <the single strongest objection to THIS paper's thesis>
rests_on: <what would have to be true for the thesis to be wrong>
```

代码实际只认两条正则（`gates/divergence_gate.py:47-48`）：

```python
ids = re.findall(r"(?m)^##\s+(P\d+)\s*:", md)
has_obj = bool(re.search(r"(?m)^##\s+STRONGEST-OBJECTION\b", md))
```

即 **`holder:` / `claim:` / `rests_on:` 三个字段门一个都不检查**——它们只是给 advocate 子代理读的散文。
一个只有 `## P1:` 标题、下面全空的 positions.md 照样解析成功。

**F-04 · paper.md 的信号格式**

`gates/divergence.md:31-38`：行内 `[P1]`…`[Pn]` 标记真实交锋处、`[OBJ]` 标记回应最强反驳、
可选 `## Excluded` 段落列出"有理由的排除"（`- [P4] out of scope because …`）。
另有一行 `field-weight: humanities|mixed|science`（`WORKFLOW.md:46-47` 要求"exactly one … line at the
top of `paper.md`"）。

实测 4 个 run 的 paper.md 头部均含 `thesis:` 多行块 + 一行 `field-weight:`；
nuclear-safety 声明 `science`，black-death 声明 `humanities`，另两个 `mixed`。

**F-05 · transform / metric / source 约定**

- transform 是**无网络、确定性、repo-root 相对路径**的独立脚本。真实样本
  `runs/nuclear-safety/transforms/c3.py`（一个派生比值）核心 3 行：
  ```python
  rates = {r["Entity"]: float(r[COL]) for r in csv.DictReader(f)}
  value = round(rates["Coal"] / rates["Nuclear"])
  (RUN / "metrics" / "c3.json").write_text(json.dumps({"value": value}) + "\n")
  ```
  产物固定为 `{"value": <v>}` 单键 JSON（实测 5 个 metrics 文件全为该形态，如 `{"value": 0.03}`）。
- source 是保存下来的纯文本片段（`sources/<cid>.txt`，实测 483B–1773B 不等）。

**F-06 · dvc 接线（每个 data claim 一个 stage，stage 名 == claim_id）**

一手来源 `runs/nuclear-safety/dvc.yaml`（5 个 stage，共享同一份原始数据）：

```yaml
stages:
  c1:
    wdir: ../..                                   # 从 repo root 跑，data/ 路径才解析得了
    cmd: python3 runs/nuclear-safety/transforms/c1.py
    deps:
      - runs/nuclear-safety/transforms/c1.py      # 脚本 md5 → dvc.lock
      - data/energy/death_rates_per_twh.csv       # 原始数据 md5 → dvc.lock
    metrics:
      - runs/nuclear-safety/metrics/c1.json:
          cache: false                            # 保持明文可读
```

`dvc.lock` 记录三段 md5（dep 数据 / dep 脚本 / out metric），门把它渲染成 `gate_report.md` 里的
`provenance: data/energy/death_rates_per_twh.csv@0d7cc1ed; runs/nuclear-safety/transforms/c1.py@9e1f224a`。
**纯人文 run 无 data claim 时不需要 dvc.yaml**（`gates/rigor.md:49-50`），实测
`runs/black-death` 与 `runs/alcohol-jcurve` 确实没有 dvc.yaml/dvc.lock/transforms/metrics（目录为空）。

`.dvc/config` 全部内容只有 `[core] analytics = false`——**没有 remote，没有 `dvc add`**，
`gates/rigor.md:70-73` 明确说数据版本化"deferred, not required"。所以 DVC 在这里**只被用作
"强制重执行 + md5 台账"**，没用它的存储/缓存/远端能力。

---

### B 组 — 门代码实际检查什么 vs 文档宣称什么（逐条 fail-open，含 file:line）

#### rigor 门

**F-07 · 【致命】`dvc repro` 的成败完全不进入退出码**

`gates/rigor_gate.py:189` 是唯一的退出语句：

```python
sys.exit(0 if rate == 1.0 else 1)
```

`repro_ok`（:140-142 得到）只被用来往报告里打字（:159-164），**从不参与判定**。
而 `check_data`（:86-97）直接从磁盘读 `metrics/<cid>.json`（:76-83），不校验这个文件是谁产生的、什么时候产生的。

推论：**陈旧的、手写的、伪造的 metric 文件与真跑出来的 metric 文件对门而言完全等价。**

`gates/rigor.md:5` 宣称："The gate **re-executes** — it does not trust prose."
代码层面这句话只在 `dvc repro` 真的被调用且真的成功时成立，而门不检查这一点。

**F-08 · 没有 dvc.yaml 时，data claim 静默退化为"读磁盘上的 metric"**

`gates/rigor_gate.py:47-48`：

```python
if not dvcyaml.is_file():
    return None, "no dvc.yaml (no kind=data claims to reproduce)"
```

返回 `None`（不是 `False`）。:160 的 `'ok' if repro_ok else 'FAILED'` 会把 `None` 渲染成 `FAILED`，
报告上写着 FAILED，退出码却是 0。注释文本本身也是错的——有 data claim 却没 dvc.yaml 时，
它仍然说"no kind=data claims to reproduce"。

**F-09 · 台账里有 data claim 但 dvc.yaml 里没有对应 stage → 门无感**

门唯一的近似检查在 :89：`f"no metric metrics/{cid}.json (is there a dvc stage '{cid}'?)"`——
**只有 metric 文件不存在时才报错**。门从不枚举 `dvc.yaml` 的 stage 集合与 data claim 集合做集合相等校验。

**F-10 · provenance 缺失是静默软失败**

`gates/rigor_gate.py:59-73` `load_provenance`：`dvc.lock` 不存在 → 返回 `{}`；
`import yaml` 失败 → `except: return {}`。结果是报告里那行 `provenance: …` 直接消失，
**没有任何 FAIL、没有任何警告**。可追溯性（可回溯，项目的两大目标之一）是"能显示就显示，不能就算了"。

**F-11 · source 类只对"作者自己保存的那份文本"做子串比对**

`gates/rigor_gate.py:122-127`：

```python
src = run / "sources" / f"{cid}.txt"
if not src.is_file(): return False, f"no source sources/{cid}.txt", ""
ok = norm(quote) in norm(src.read_text(encoding="utf-8", errors="replace"))
```

`norm` 只做空白折叠 + 小写（:35-36）。**没有任何东西把 `sources/<cid>.txt` 绑定到 `raw_ref` 的 URL**。
作者（或子代理）可以直接把想要的引文写进 txt 里。

`--verify-sources`（:173-181）确实会去 fetch URL 校验，但 :15-18 的 docstring 逐字声明它
"**NON-fatal**… It never changes the pass/fail verdict"。实测代码也确实如此——它只往报告里加 ✅/⚠️。
`CHANGELOG.md:45-46` 记录了实跑结果："black-death's 3 quotes confirmed at their live URLs;
nuclear's 2 flagged ⚠️ (JS/blocked)"——**已知样本确认率 3/5 = 60%**。
即联网核验在真实网络条件下有相当比例无法确认，这是把它设成非致命的现实原因，
也是 v2 必须提前设计好的问题（抓取时刻落 CAS 快照，而不是事后实时 refetch）。

**F-12 · 数值比对：1% 相对容差 + "取字符串里第一个数字"**

`gates/rigor_gate.py:92`：`ok = abs(pv - cv) <= max(abs(cv) * 0.01, 1e-9)`；
`as_num`（:39-41）用 `NUM = re.compile(r"-?\d+(?:\.\d+)?")` 的 `search` **取第一个匹配**。
所以 `value` 写成 `"1970-2020 均值 4.8"` 会被解析成 `1970`。**单位完全不参与比对**
（`0.03 deaths/TWh` 与 `0.03 g/kWh` 对门等价）。

**F-13 · 【实跑复现】伪造数字 + 无 dvc + 无 transform + 无原始数据 → PASS ✅ exit 0**

沙箱构造：只有 `claims.tsv`（1 行 `kind=data`，`value=999.0`，`raw_ref=data/nonexistent.csv`）
与手写的 `metrics/c1.json = {"value": 999.0}`。无 dvc.yaml、无 transforms/、无该数据文件。
用**仓库里未经修改的门脚本**跑：

````text
## RIGOR gate

dvc repro: **FAILED** (re-executed all data transforms from raw data)

```
no dvc.yaml (no kind=data claims to reproduce)
```

reproduce-rate: **1/1 = 100%**  PASS ✅

- ✅ `c1` (data): claimed 999.0 vs produced 999.0
### EXIT CODE = 0
````

报告上白纸黑字写着 `dvc repro: FAILED`，同一份报告下面写着 `PASS ✅`，退出码 0。
**这就是 F-07 的完整证据。**

#### divergence 门

**F-14 · 【实跑复现】一个段落塞满所有 tag → 100%/100%/PASS**

`gates/divergence_gate.py:39-42` 的 `_prose_len` 先剥掉**所有** `[P\d+|OBJ]` tag，再量**整段**长度；
`engaged_ids`（:66-74）对每个 tag 独立判定"它所在的段落是否 ≥200 字符"。
即 **200 字符的预算被同段内所有 tag 共享，且段落内容与 tag 指向的立场毫无关联要求。**

沙箱构造：positions.md 有 P1–P5 + STRONGEST-OBJECTION；paper.md 正文只有一段
`[P1] [P2] [P3] [P4] [P5] [OBJ] <250 字符 lorem ipsum>`。实跑输出：

```
field-weight: **science** (engagement threshold K=50%)
coverage: **5/5 = 100%** (engaged or consciously excluded)
engagement: **5/5 = 100%** OK
strongest-objection engaged: **yes ✅**
verdict: **PASS ✅**
### EXIT CODE = 0
```

`CHANGELOG.md:37-41` 记录这个 200 字符段落规则是为了修"按行算导致 namedrop 过关"的洞
（"a bare namedrop cleared the 40-char bar"）。**修法只把攻击成本从 40 字符抬到 200 字符，
并未改变"字符数≠论证"这一根本错误。**

**F-15 · 【实跑复现】只有 1 个立场的 positions.md 照样 PASS**

`gates/divergence.md:26-27` 逐字规则："Rules: ≥ 3 real positions that genuinely disagree
(not three flavors of one view)."

代码里**没有任何地方实现这条**。`gates/divergence_gate.py:96-99` 只有：

```python
ids, has_obj = parse_positions(pos_md)
if not ids:
    print("positions.md has no P-blocks"); sys.exit(2)
```

沙箱实跑（positions.md 只有 P1 + OBJ，paper.md 一段 260 字符）：

```
field-weight: **humanities** (engagement threshold K=80%)
coverage: **1/1 = 100%**
engagement: **1/1 = 100%** OK
verdict: **PASS ✅**
### EXIT CODE = 0
```

**分母由被检方定义，且下限不被强制。**"少画一个立场"是最省力也最有效的过门手段。

**F-16 · 立场块少一个冒号 = 该立场从分母里消失**

`:47` 的正则要求 `^##\s+(P\d+)\s*:`。写成 `## P4 反对派`（无冒号）则该块**不被解析**，
`total` 减一，coverage/engagement 双双升高。**从地图上"删掉"一个不利立场不需要删文字，只需删一个标点。**

**F-17 · 【尺子在被告手里】K 阈值由 paper.md 自己声明**

`gates/divergence_gate.py:110`：`weight = field_weight(paper_md)` ← 参数是**论文本身**，不是 positions.md，
不是配置文件。`field_weight`（:82-84）正则 `field[-_ ]?weight\s*[:=]\s*(humanities|mixed|science)`，
默认 `mixed`。`K_BY_WEIGHT = {"humanities": 0.8, "mixed": 0.6, "science": 0.5}`（:23）。

生产实例：`runs/nuclear-safety/paper.md` 第 7 行写 `field-weight: science` → K=0.5，
实测 engagement 6/7=86% 过关。作者只要在自己的论文里改一个词就能把及格线从 80% 降到 50%。

**F-18 · `[OBJ]` 只检查"存在于某个 ≥200 字符段落"，不检查它回应的是不是那条反驳**

`:77-79` `objection_engaged` 只做 `any(_prose_len(...) >= 200 for m in re.finditer(r"\[OBJ\]", md))`。
positions.md 里 STRONGEST-OBJECTION 块的 `claim:` 与 `rests_on:` 内容**从不被读取**。

**F-19 · `## Excluded` 的"理由"门槛是 8 个字符**

`:61`：`if hit and len(re.sub(r"\[P\d+\]", "", line).strip(" -\t")) >= 8`。
另外 `:101-102` 把 excluded span 定义为 `(m.start(), len(paper_md))`——**从 `## Excluded` 标题一直到文件末尾**。
若 Excluded 段落被放在文中间，其后所有 `[Pi]` tag 的 engagement 会被静默忽略。

---

### C 组 — eval harness 的打分/聚合与 fail-open

**F-20 · D1 只是关键词筛（screen），且只会向上救、不会向下扣**

`eval/harness.py:51-63` `coverage()`：每个 answer-key 立场取其 `key_terms`，
只要**任一 term 作为子串出现在任一 ≥200 字符段落里**，就算 engaged。

```python
hit = next((t for t in terms if any(t in lp for lp in low_paras)), None)
```

实测 nuclear-safety 的 8/8 命中理由（`eval/reports/nuclear-safety.md:14-21`）分别是
`"deaths per twh"` / `"gco2eq/kwh"` / `"kharecha"` / `"fukushima"` / `"proliferation"` /
`"lcoe"` / `"jacobson"` / `"variable renewables"`——**大量是单个专名或缩写**。
参考文献段落里出现一次姓氏即可满足。

`reconcile()`（:88-98）只做 **RESCUE**：D2 判 ≥1 的 screen-miss 被救回；
**D2 判为稻草人（0 分）的 screen-hit 从不被扣掉**。所以 D1 的假阳性永远不会被纠正。

**铁证**：nuclear-safety D1 screen = **8/8 = 100%**，同一批工件里 D2 给出 `K8: 0`（稻草人）、
`K5/K6/K7: 1`。机械筛说"全覆盖"，对抗性辩护人说"其中一个是稻草人"。两个数字同时印在
`eval/reports/nuclear-safety.md` 上，而 coverage 那一行仍然是 100%。

**F-21 · 【致命】面板文件缺失 = 四个 kill-criterion 全部静默跳过 = SHIP**

`eval/harness.py:82-85`：

```python
def load_verdicts(paper: str) -> dict:
    f = ROOT / "eval" / "verdicts" / f"{paper}.json"
    return json.loads(f.read_text()) if f.is_file() else {}
```

`verdict()`（:101-119）的每一条主观 kill 都是**条件式**而非全集式：

```python
if v.get("steelman_min") is not None and v["steelman_min"] < 1:      # :111
if v.get("objection_robust") is False:                                # :113
if v.get("claim_coverage") is not None and v["claim_coverage"] < 1.0: # :115
if v.get("referee_verdict") == "reject":                              # :117
```

我用仓库里未修改的 `harness` 模块直接实跑 `verdict()`：

| 输入 | 返回 |
|---|---|
| `v={}`（verdicts 文件不存在），coverage 满，repro=1.0 | `('SHIP', [])` |
| `repro=None`（rigor 门崩溃/输出无法解析），`v={}` | `('SHIP', [])` |
| `referee_verdict="major-revision"`，其余缺失 | `('SHIP', [])` |
| `honesty_flags` 有 5 条 + `uncited_load_bearing` 有 1 条，其余全绿 | `('SHIP', [])` |
| `steelman_by_pos={K1:1,K2:1,K3:1}`（均值 1.0 < EVAL.md 要求的 1.5），min=1 | `('SHIP', [])` |

并实测 `harness.load_verdicts("black-death") -> {}`。

**这就是 `eval/scoreboard.tsv` 第 2 行 `black-death … ? ? ? ? SHIP` 的来源。**

**F-22 · rigor 门崩溃 → repro=None → D4 静默消失**

`eval/harness.py:66-79` `reproduce_rate` 通过 subprocess 调门脚本，再用正则从 stdout 抓数：

```python
m = re.search(r"reproduce-rate:\s*\*\*(\d+)/(\d+)", out.stdout)
if not m:
    return None, "could not parse rigor gate output"
```

任何异常/超时/格式变化都返回 `None`，而 :109 的 `if repro is not None and repro < 1.0`
让 `None` 直接跳过。**"数字不可复现"这条最硬的客观 kill，在门崩溃时反而消失了。**
（附带：这是一个**跨进程 stdout 正则耦合**——门的报告文案一改，eval 的 D4 就静默失效。）

**F-23 · EVAL.md 写的 SHIP 条件与代码实现的 SHIP 条件不是同一件事**

`eval/EVAL.md:159-161` 逐字：

> **SHIP** iff: no kill-criterion tripped, `independent-coverage = 1.0`, mean steelman-fidelity
> ≥ 1.5, objection robust, `claim-coverage = 1.0` with zero unresolved honesty flags, and referee
> modal verdict ∈ {accept, major-revision-with-score ≥ band}.

代码对照：

| EVAL.md 条件 | harness.py 实现 | 结论 |
|---|---|---|
| mean steelman ≥ 1.5 | 只有 `steelman_min < 1`（:111），**均值从未计算** | 未实现 |
| zero unresolved honesty flags | `honesty_flags` 只在 :165-166 被打印，**从不进 verdict** | 未实现 |
| referee ∈ {accept, major-revision-with-score ≥ band} | 只有 `== "reject"` 才 FAIL（:117），**band 从未定义/实现** | 未实现 |
| independent-coverage = 1.0 | 经 `reconcile` 后的 unrescued 判定（:104-108） | 已实现 |
| claim-coverage = 1.0 | :115，但 `None` 跳过 | 部分实现 |

**F-24 · answer key 与被评论文之间没有任何绑定校验**

`eval/harness.py:127`：`key = json.loads(Path(key_path).read_text())` —— `--key` 是自由参数。
拿 black-death 的 key 去评 nuclear-safety 不会有任何报错。
`EVAL_VERSION = "0.3.0"` 是硬编码字符串（:31），**没有 harness 自身或 answer key 的内容哈希**
进入 scoreboard。`eval/EVAL.md:12-34` 那份措辞极强的 "Isolation Contract"
（两轨道、两 CHANGELOG、绝不为放行而软化）**100% 是散文承诺，零机械强制**。

**F-25 · answer key 里近半数内容是死数据**

grep `eval/*.py gates/*.py`：`benchmark_claims`、`sources_fetched`、每个立场的 `source_url`
**没有任何代码读取**。nuclear-safety 的 key 里 6 条 `benchmark_claims`（含 OWID/IPCC/Lazard 真实数字）
和 9 条 `sources_fetched` 纯属装饰——它们本可以是"独立于作者台账的对照基准"，但没有消费方。

**F-26 · protocol.md 声明的面板 JSON schema 与 harness 实际消费的字段对不上**

`eval/protocol.md:36-39` 声明：

```json
{ "steelman_min":…, "steelman_by_pos":…, "objection_robust":…, "stronger_objection":…,
  "claim_coverage":…, "honesty_flags":…, "referee_verdict":…, "referee_scores": {"...":0-5} }
```

而 `eval/harness.py:169` 读的是 `v.get("referee_panel", [])`，:161-163 读的是
`total_empirical` / `ledgered` / `uncited_load_bearing`——**这四个字段 protocol.md 里一个都没有**；
protocol.md 声明的 `referee_scores` 代码里**从不使用**。真实工件
`eval/verdicts/nuclear-safety.json` 用的是 harness 的那套。**接口文档与实现分叉。**

**F-27 · selftest 没有一条负例覆盖"面板缺失不得 SHIP"**

`eval/selftest.py` 8 条断言全部通过（我实跑确认 `SELFTEST: PASS`）。
但看 :37-48，每条 `verdict()` 断言都**显式传入了要测的那个字段**。
没有任何一条断言形如"传 `{}` 必须 REVISE"。**自测把 fail-open 路径整个漏掉了**，
这也正是它能长期绿着的原因。

**F-28 · eval 会改写被评对象**

`eval/harness.py:71` shell out 调 `gates/rigor_gate.py`，而后者在 :183-187 **重写
`runs/<slug>/gate_report.md` 的 RIGOR 段**。实测 4 个 run 的 `gate_report.md` mtime 全部是
`Jul 10 11:49`（= eval 跑的时刻），而 claims.tsv/paper.md 的 mtime 早得多。
所谓 held-out 评测**物理修改了它正在评的工件**。

---

### D 组 — 四个真实 run 到底证明了什么

**F-29 · 规模与构成（实测统计）**

| run | 领域 | field-weight (K) | claims 合计 | data | source | positions.md 立场数 | answer_key 立场数 | D1 screen | eval overall |
|---|---|---|---|---|---|---|---|---|---|
| `ai-employment` | 劳动经济 | mixed (0.6) | 4 | 1 | 3 | 7 (P7 excluded) | 8 | 5/8 = 62% | REVISE |
| `black-death` | 中世纪经济史 | humanities (0.8) | 3 | 0 | 3 | 7 | 7 | 7/7 = 100% | **SHIP（假）** |
| `alcohol-jcurve` | 流行病学 | mixed (0.6) | 3 | 0 | 3 | 6 | 7 | 6/7 = 86% | REVISE |
| `nuclear-safety` | 能源/物理科学 | science (0.5) | 12 | 5 | 7 | 7 (P7 excluded) | 8 | 8/8 = 100% | REVISE |
| `_smoke` | 黄金自测 | mixed | 2 | 1 | 1 | 4 (P4 excluded) | — | — | — |

**四个 run 的 reproduce-rate 全部 100%**（4/4、3/3、3/3、12/12）。
**四个 run 的双门全部 PASS**（`gate_report.md` 逐个确认）。

**F-30 · "作者自画的地图比文献的地图小"是可量化的**

3/4 的话题里，作者 positions.md 的立场数 < 独立 answer key 的立场数
（nuclear 7<8、alcohol 6<7、ai-employment 7<8），只有 black-death 持平（7=7）。
这正是 `eval/EVAL.md:115-116` 说的"a cozy, self-authored position map that omits the positions
most awkward for the thesis"——而 **in-loop 门在结构上不可能发现它**（分母就是作者给的）。

`eval/CHANGELOG.md:33-36` 记录了 v0.2.0 的首个真实发现：nuclear-safety 自家门 7/7 PASS，
独立 key 上 6/8=75% REVISE，且做了校准——真实综述（Wikipedia "Nuclear power debate"）
覆盖同一 key 的 7/8=88%，**证明缺口是真的而不是口味问题**。这个"用真实文献给尺子做校准"
的动作是整个 eval 设计里最值得继承的一招。

**F-31 · 数据规模非常小（这是它跑得通的隐藏前提）**

最大的 run 只有 12 条 claim、7 个立场、5 个 dvc stage、7 个 source 文本（最大 1423B）；
原始数据 `data/energy/death_rates_per_twh.csv` 只有 **214 字节**。
所有"跨领域可用"的结论都建立在**每个 run 十条量级的 claim** 之上。
把它当作"高并行探索系统的契约基线"时必须记住这个量级差。

**F-32 · 唯一跑完的完整 eval 面板（nuclear-safety）到底发现了什么**

一手工件 `eval/verdicts/nuclear-safety.json` + `eval/reports/nuclear-safety.md`。
三条 kill-criterion 被触发，**全部来自对抗性程序，无一来自机械筛**：

1. **D2 稻草人**：`"steelman_by_pos": {"K1":2,"K2":2,"K3":2,"K4":2,"K5":1,"K6":1,"K7":1,"K8":0}` → min=0。
   K8（firm-power/系统成本）被判为稻草人——**而 D1 screen 给它打了 ✅（命中词 "variable renewables"）**。

2. **D3 更强的未回应反驳**（逐字）：
   > "By honestly loading Fukushima evacuation (~2,313) and high-end Chernobyl (~27,000) deaths into
   > the numerator, the paper's own concession pushes nuclear to ~0.2-0.5 deaths/TWh — still below
   > coal but now ~an order of magnitude ABOVE wind (~0.035) and solar (~0.019); the paper keeps
   > asserting the thesis's 'comparable to wind and solar' clause and never revisits that its own
   > tail-accounting refutes it."

   **这条是全项目最重要的一条证据**：论文的每一条 claim 都逐条复现了（12/12），
   但**这些 claim 组合起来推不出论文保留的那句论点**。这是一次纯粹的**推断失效**，
   而系统里没有任何门能看见它——因为论点与 claim 之间不存在被检查的推断链。

3. **D4b claim 覆盖 12/16 = 0.75**，4 条承重断言无台账行，其中包括
   "'far beneath coal or gas' lifecycle emissions — no ledger row gives a coal/gas gCO2/kWh figure"
   ——**论点的一半（"远低于化石燃料"）根本没有证据行**，而 rigor 门报 100%，
   因为门只检查"台账里有的"，不检查"论文里该有的"。

4. **5 条 honesty flags**，性质高度一致——**数字为真但口径失真**：
   - "asserts equivalence from bare point estimates with no CIs"（无置信区间就断言等价）
   - "nuclear 0.03 (c1) is OWID's low-end figure embedding a LOW Chernobyl count"（口径内嵌了低估）
   - "n1 … and n5 … are sourced to the World Nuclear Association (industry body), not IPCC/official
     reconstruction directly"（**转引 + 来源独立性问题**：核工业协会转述 IPCC）
   - "the ~27,000 Chernobyl ceiling understates higher independent projections (TORCH-type)"
   - "the c3 ~821x ratio is best-case: a modestly higher nuclear estimate (0.06-0.07) roughly halves it"
     （**敏感性**：分母微调，结论砍半）

5. **对照组：3 个 rubric referee 全给 `accept`**，评分 4-5 分档
   （`{"thesis":4,"evidence":4,"counterargument":4,"calibration":5,"prose":4}`）。
   **在三条 kill 同时成立的论文上，rubric 评分给了满堂彩。**
   这是"对抗性程序 > rubric 评分"最干净的一次实证。

**F-33 · 项目自己在文档里承认了这些洞（但没修）**

`CHANGELOG.md:64-66` 逐字：

> The current eval harness is not fail-closed on missing panel fields and does not enforce every
> `EVAL.md` verdict condition. The current rigor gate also does not make DVC reproduction failure
> independently fatal. Both remain implementation conformance work; neither was changed here.

`README.md:29-38` 列了四条自认缺口，包括
"`eval/selftest.py` passes its present cases but has no negative case proving that a missing panel
cannot produce `SHIP`."（:37-38）

**即：这些不是我发现的隐藏 bug，是被写进文档、被留在代码里、然后被 scoreboard 上一行假 SHIP 兑现的已知洞。**
这本身就是最重要的一条教训：**"文档里写了 known limitation" 不能替代 "代码里 fail-closed"。**

---

### E 组 — validate_eval_bundle.py：正确的范本，与它为什么没接上

**F-34 · 它是对的，而且对在"全集校验"这个结构上**

`skills/papergraph/scripts/validate_eval_bundle.py`（127 行）。四个结构性优点：

1. **必需文件是常量元组，先查缺失再谈内容**（:12-18, :39-41）：
   ```python
   REQUIRED_FILES = ("d1_answer_key.json","d2_steelmans.json","d3_adversary.json",
                     "d4b_claim_audit.json","d5_referees.json")
   missing = [name for name in REQUIRED_FILES if not (root / name).is_file()]
   if missing:
       return _result("INCOMPLETE", complete=False, reasons=[f"missing:{name}" for name in missing])
   ```
   **三态输出 `INCOMPLETE / REVISE / SHIP`**，"缺失"是独立的第一等结论，不会退化成"通过"。

2. **集合相等而非"碰巧在场"**（:72-73）：
   ```python
   if set(steelmans) != position_ids:
       reasons.append("D2 does not cover exactly the D1 positions")
   ```
   D2 必须**恰好**覆盖 D1 的立场集合——多一个少一个都是 reason。这正是 `harness.py:88-98`
   的 `reconcile` 缺的东西。

3. **每条判定都是显式恒等而非真值性**（:75, :81, :87, :89, :109, :111）：
   `judgment.get("passed") is not True`、`d3.get("stronger_unaddressed_objection") is not False`、
   `d4.get("claims_complete") is not True`、`traceability != 1.0`（并显式排除 `bool`）、
   `referee.get("independent") is not True`、`referee.get("band") != passing_band`。
   **`None`/缺失/类型错误一律落进 FAIL 分支**，而不是像 `v.get(...) is not None and …` 那样跳过。

4. **文档没实现的规则它实现了**：`honesty_flags` 非空即 FAIL（:91-92）、
   referee ≥3 且 id 唯一（:96, :105-106）、`passing_band ∈ {"ACCEPT","MAJOR_REVISION"}`（:111）
   ——即 EVAL.md 那三条 harness 从未实现的条件（F-23），**在这个脚本里全都是实现了的**。

`main()` 的退出码是 `0 if result["verdict"] == "SHIP" else 1`（:123）——INCOMPLETE 也非零。

**F-35 · 它从未被接进 eval/，而且契约已经分叉到不可能直接接**

grep 全仓（排除 .venv/.git/archive）：`validate_eval_bundle` 的引用**全部落在 `skills/papergraph/` 内部**
（SKILL.md、rules/workflow.md、evals/run_all.py、evals/run_mutation_checks.py、scripts/workflow_contract.py、
.skill-engineer/build-report.json、.skill-guidance/handoff-spec.json）。
`eval/` 与 `gates/` 下**零引用**。

契约差异（这才是"没接上"的实质原因）：

| | 主 eval 轨（实际在跑） | skill 轨（fail-closed 范本） |
|---|---|---|
| 面板载体 | 单文件 `eval/verdicts/<slug>.json` | 五文件目录 `<bundle>/d{1,2,3,4b,5}*.json` |
| D1 表示 | `answer_key.json` 的 `positions[].id/key_terms` | `d1_answer_key.json` 的 `positions[].position_id/literature_answer` |
| D2 表示 | `steelman_by_pos: {"K1":2}`（0/1/2 整数） | `steelmans: {"p1": {"passed": true}}`（布尔） |
| D3 表示 | `objection_robust: bool` | `objection_robustness:"PASS"` + `stronger_unaddressed_objection: false` |
| D4b 表示 | `claim_coverage: float` | `claims_complete: bool` + `traceability_rate: 1.0` |
| D5 表示 | `referee_verdict` + `referee_panel[]` | `referees[]{referee_id,independent,band}` + `passing_band` |
| 缺失语义 | 跳过 → SHIP | INCOMPLETE |

**唯一存在的 bundle 是测试 fixture**（`skills/papergraph/evals/fixtures/eval_bundle_complete/`，
内容是两行 toy JSON），**没有任何一个真实 run 产出过合规 bundle**。
`workflow_contract.py:91` 只在离线 smoke 里调它。

**根因判断**：这个 skill 是 2026-07-10 由 skill-builder 流水线独立生成的
（`skills/papergraph/CHANGELOG.md` 0.1.0，`.skill-engineer/`/`.skill-conductor/` 目录俱在），
**它按 SKILL.md/rules 的应然规格重新实现了一遍验收契约，而不是接管既有实现**。
于是同一个契约有了两个可执行权威，跑的是弱的那个，强的那个只服务于自己的 fixture。
`skills/papergraph/rules/workflow.md:59` 甚至写死了
"Return `SHIP` only when `validate_eval_bundle.py` reports `SHIP`"——
**规则文档指向的执行体，与真实 scoreboard 上写 SHIP 的执行体，不是同一个。**

**F-36 · `.loop/` 是上一代（已归档）系统的遗留，不描述当前系统**

`.loop/papergraph-v1-build.loop.{json,md}`（26KB/24KB）与 `.loop/state/`（contract.md/progress.md/log.md
+ 13 份 gate-report）**全部是 2026-07-07~07-09 的 paperproof/nd 框架构建记录**
（`log.md` 里是 `V-SP`/`V-COV`/`docs wave-member`/`587 green` 这类已归档 CLI 的词汇）。
post-reset 系统**不由 loop 驱动**，`.loop/state/traces/` 为空目录。
读它只对"上一代为什么失败"有价值，对当前契约无效。
其中一条可迁移的运维教训（`log.md`）：一个 review 子代理的 `rm -rf … data` 误删了未跟踪的
`data/projects/ai-jobs{,-2}`，不可恢复——**子代理的破坏半径必须在设计里被限住**。

---

## 与二手文档的冲突

> 这里的"二手文档"= ① Paper Graph 自己的 README/CHANGELOG/DESIGN/EVAL.md（相对代码而言是二手）；
> ② academic-research-plugin v1 规划文档集（`.archive/v1-2026-08-17/`）。

### C-1 【代码 vs 项目文档】"The gate re-executes — it does not trust prose."（假）

`gates/rigor.md:5` 与 `DESIGN.md:61-62`（"**The gate RE-EXECUTES the transform** on the raw data and
checks the produced value matches the claim within tolerance"）都断言重执行是通过条件。
**代码不是这样**：`rigor_gate.py:189` 只看 metric 文件里的数字（F-07/F-08/F-13 实跑证明）。
项目自己在 `CHANGELOG.md:65-66` 和 `README.md:33-34` 承认了，但 `gates/rigor.md` 与 `DESIGN.md`
的断言至今未改。**以代码为准：这个系统从未真正强制过重执行。**

### C-2 【代码 vs 门文档】"≥ 3 real positions" 是未实现的规则

`gates/divergence.md:26` 的硬规则在 `divergence_gate.py` 中**完全不存在**（F-15 实跑证明 1 个立场也 PASS）。
`skills/papergraph/rules/workflow.md:23-25` 把它挪给了 orchestrator 的判断力
（"Validate at least three genuinely disagreeing positions … before the Orchestrator writes positions.md"）
——即**从"门检查"降级为"agent 自律"**，而这正是 DESIGN.md 反复说不能依赖的东西。

### C-3 【代码 vs EVAL.md】SHIP 判据三缺（F-23）

均值 steelman ≥1.5、honesty flags 清零、referee band —— EVAL.md 白纸黑字，harness 一条没实现。
更严重的是 `EVAL.md:33-34` 那句"If you find yourself editing this file in the same breath as making a
paper pass, stop"——**Isolation Contract 全靠人守，代码里没有任何哈希/版本/身份绑定**（F-24）。

### C-4 【代码 vs WORKFLOW.md / README.md】"Missing judge outputs are incomplete, never a pass"（被 scoreboard 证伪）

`WORKFLOW.md:93-94` 逐字："`SHIP` only when the complete D1-D5 evaluation satisfies `eval/EVAL.md`.
Missing judge outputs are incomplete, never a pass."
`README.md:78-79`："Missing eval dimensions fail closed: the result is incomplete, never `SHIP`."
`README.md:139`（Non-negotiables）："Never ship while any held-out eval dimension is missing or failing."

**`eval/scoreboard.tsv` 第 2 行**：
```
black-death	gated	0.3.0	1.00	1.00	?	?	?	?	SHIP	-
```
四个 `?` = D2/D3/D4b/D5 全缺，`overall = SHIP`。`eval/reports/black-death.md` 底部同时写着
"_Subjective dimensions (D2/D3/D5) not yet run_"。**规则说不可能发生的事，已经发生并落进了永久台账。**

### C-5 【skill 轨 vs eval 轨】同一契约两个可执行权威（F-35）

`skills/papergraph/rules/workflow.md:59` 指定 `validate_eval_bundle.py` 为 SHIP 权威；
`eval/EVAL.md` + `eval/harness.py` 是另一套。两者数据格式不兼容，实际跑的是弱的那套。

### C-6 【v1 规划文档 · 需要加强】"4/4 双门全绿，独立 eval 3/4 REVISE"

v1 `PRINCIPLES.md` P-7 引 `eval/CHANGELOG.md v0.2.0` 说"过拟合被量化"。**方向正确但低估了。**
一手订正：那第 4 个不是"SHIP"，是**面板缺失导致的 fail-open 假 SHIP**（F-21/C-4）。
准确表述应为：**4/4 双门全绿；完整跑过 D1–D5 的只有 1 个，结论 REVISE；
其余 3 个中 2 个 REVISE、1 个假 SHIP。真正获得过发布裁决的论文：0 个。**
这条更硬，且直接支撑 v2 的"MISSING==FAIL"原则。

### C-7 【v1 规划文档 · 需要加强】"前代只有 data|source 两类，逻辑推断无 grounding 契约是已确认的空白"

方向正确，但**比"空白"更糟**：`gates/rigor_gate.py:152-153`
```python
else:
    ok, detail, trail = False, f"unknown kind {kind!r}", ""
```
任何 `kind=inference` 的行会被**计为失败**，把 reproduce-rate 拉到 100% 以下 → 门 FAIL。
即前代不是"没管推断"，而是"台账里出现推断类 claim 会让论文过不了门"。
v2 的第三通道是**新增机制**，不是补一个字段。

### C-8 【v1 规划文档 · 需要加强】"reproduced 留 ?，门的输出才是记录"

引文本身准确（`gates/rigor.md:32`），但一手核对显示 **`reproduced` 列门既不读也不写**（F-02）——
"门的输出才是记录"只兑现在 `gate_report.md` 这个**旁路文件**里，台账本身永远停在 `?`。
v1 ARCHITECTURE 提出的"status 列唯一物理写者 = 门脚本"是对这个缺陷的正确修法，
但必须配一条负向测试：**worker/conductor 试图写 status 必须被观察到拒绝**，否则又是一句散文。

### C-9 【v1 规划文档 · 精度订正】"继承 Paper Graph 全部角色文本资产"

一手核对：可继承的角色提示词总量很小——`WORKFLOW.md:112-124` 四条作者侧
（Cartographer/Advocate/Adversary/ClaimGrounder），`eval/protocol.md:42-55` 四条评审侧
（D2/D3/D4/D5），`skills/papergraph/assets/worker-packets.md`（50 行）是同一批的 packet 化版本。
**合计 8 条、每条 3-5 行**。这是"有用的措辞种子"，不是"资产库"。
其中最值钱的一句是 Cartographer 的
"Do not read the draft or optimize the map for its current argument."——**独立性写进了 prompt，
但没有任何机制强制它**（cartographer 与 orchestrator 是同一个会话的不同子代理，输出由 orchestrator 合并）。

### C-10 【v1 规划文档 · 确认无误的部分】

以下 v1 断言经一手核对**完全准确**，可直接沿用：
- claims.tsv 七列名称与顺序（F-01）；
- `divergence_gate.py:82-84` field_weight 从 paper.md 读取 → 作者可自降 K（F-17，且 nuclear-safety 生产实例坐实）；
- `rigor_gate.py:189` 是 DVC 失败不致命的那一行（F-07）；
- `harness.py` 的 `load_verdicts()` 是面板缺失 fail-open 的入口（F-21）；
- `validate_eval_bundle.py` 造出来却从未接回主 eval（F-35）；
- nuclear-safety 5 条 honesty flags 的性质（点估计无 CI、转引来源、cherry-picking 窗口、最优情形比率）（F-32）；
- 3 个 rubric referee 全 accept 而三条 kill 同时成立（F-32）。

---

## 对 academic-research-plugin 设计的含义

### 一、原样继承（verbatim carry-forward）

**V-1 · claims.tsv 的 TSV 极简形态 + 一 claim 一 id 的寻址**。
7 列表头在 5 个 run 里逐字节稳定、跨 4 个学科可用（F-01/F-29）。v2 扩到 8 列
（`method_ref`/`status`/`flags`）是合理增量，但**每加一列必须先有消费它的代码路径**——
前代 3/7 列无消费方（F-02、F-25）就是反面教材。

**V-2 · `metrics/<cid>.json = {"value": v}` 单键产物约定**。
极简、可 diff、可 git、机器可判。（F-05）

**V-3 · 每个 data claim 一个"无网络确定性脚本"，脚本本身即证明**。
`gates/rigor.md:24-26` 那句"Keep it short; it IS the proof of the number, and its cleaning steps
are the audit trail"是这个项目最好的一句设计判断，直接继承。

**V-4 · 黄金自测 run（`runs/_smoke`）与真实 run 用同一套契约**。
smoke 里同时有 1 个 data + 1 个 source claim、完整 dvc 接线，是最便宜的契约回归。

**V-5 · answer key 从真实文献独立派生 + 用真实综述做校准**。
`eval/CHANGELOG.md:33-36` 的做法（拿 Wikipedia "Nuclear power debate" 跑同一把尺子，得 7/8=88%，
证明我们的 6/8 缺口是真的）是把"标准是否自利"变成可检验命题的正确手法。继承。

**V-6 · 对抗性程序为主、rubric 为辅的裁决结构**。
F-32 是最干净的实证：三条 kill 同时成立时，3 个 rubric referee 全给 accept。

**V-7 · `validate_eval_bundle.py` 的四个结构特征**（F-34）：必需文件常量元组先查缺失；
三态 `INCOMPLETE/REVISE/SHIP`；集合相等而非"碰巧在场"；每条判定用 `is not True`/`is not False`/
显式恒等而非真值性。**这四条应当成为 v2 所有聚合器的强制写法。**

### 二、必须重设计（redesign）

**R-1 · 门的"通过"必须由子检查全集合成，而不是由单一比率决定。**
前代的病灶是同一个模式反复出现：`dvc repro` 失败被记录不进判定（F-07）、
provenance 缺失静默软失败（F-10）、面板缺失跳过（F-21）、门崩溃 → None → 跳过（F-22）、
honesty_flags 只打印（F-23）。
**规则：任何子检查三态 `PASS/FAIL/MISSING`，`MISSING == FAIL`；聚合对"必需清单"做全集校验。**

**R-2 · 新鲜度绑定：验证产物必须携带本次执行的输入 hash + 执行 id，聚合时校验匹配。**
F-13 证明手写 metric 与真跑 metric 对门等价。修法不是"记得跑 dvc"，而是让 metric 文件
自带 `{value, input_sha256, transform_sha256, exec_id, produced_at}`，门校验这四项与本次执行一致，
否则 MISSING==FAIL。（这也顺带解掉 F-28：不需要 eval 去重跑门来取数。）

**R-3 · 语义覆盖必须替换字符计数。**
F-14 证明"200 字符/段"这个代理指标可被一段 lorem ipsum 击穿，而且 F-20 证明关键词筛
同样只是代理指标（D1 8/8 vs D2 min=0）。v2 的交锋判定应当是
**"每个立场一个独立辩护人给出 0/1/2 + 反例构造记录"作为裁决输入工件**，
机械筛只产 provisional 状态、只能向上救不能定终局。**且必须允许向下扣**——
前代 `reconcile` 只 RESCUE 不 DEMOTE（F-20）是一个方向性偏置。

**R-4 · 阈值与分母都必须在检查方轨道，作者轨只读。**
F-17（K 由 paper.md 自声明）+ F-15（立场数下限不强制）+ F-16（少个冒号就少个分母）
是同一个病：**尺子和分母在被告手里**。v2 里 K、必需立场数、必需维度清单一律由 eval 轨固定，
且 answer key 与 harness 的内容哈希必须进 scoreboard（修 F-24）。

**R-5 · 证据的可信基底必须是内容寻址快照，而不是"作者保存的那个 txt"。**
F-11 证明 source 校验只对作者自留文本做子串比对，联网核验非致命且现实中约有一半确认不了（F-11 引 CHANGELOG）。
v2 的 CAS + 抓取工具直写 + session 事件层逐字出处断言，正是对这条的修补。
**注意 F-11 揭示的现实约束：实时 refetch 在 403/paywall/JS 下不可靠，所以快照必须在抓取时刻落盘，
之后一律对快照校验、对 URL 只做健康度旁证。**

**R-6 · 台账的完备性必须被独立审计，门不能只检查"台账里有的"。**
F-32 的 D4b 是全项目最有价值的发现之一：rigor 门报 12/12=100%，
独立审计员反向抽取发现 16 条承重断言里 4 条无台账行，**其中包括论点的一半**。
**"门只验证已登记项"是结构性盲区**，必须由一个不看台账、从散文反向抽取断言的审计通道补。
v2 的"prose exit 必须 ledger-closed（每句经验性断言都引 claim_id）"是这条的正确落法。

**R-7 · 一个契约只允许一个可执行权威。**
F-35 的教训：skill 流水线按应然规格重新实现了一遍验收，造成两个权威、跑弱的那个。
v2 若同时有 plugin 侧脚本与 skill 侧脚本，必须是**同一个文件被两边引用**，不是两份实现。

**R-8 · 负向测试必须由工具触发并断言被拒；"存在即覆盖"必须被明令禁止。**
F-27 是活教材：selftest 8 条全绿，却没有一条覆盖 fail-open 路径，
因为每条断言都显式喂了要测的字段。
**规则：每一条 pass 规则配一条负例；负例必须真正走一遍门的入口（而非直调内部函数并预填字段）。**

**R-9 · eval 不得修改被评工件。**
F-28：held-out eval 通过 shell out 重写了 `gate_report.md`。
v2 的 eval 必须只读被评快照（配合 R-2 的执行 id，读取而非重跑）。

**R-10 · 记住量级前提。**
F-31：最大 run 只有 12 条 claim、214 字节原始数据。所有"契约可用"结论都在这个量级上成立。
v2 的 hyper-parallel 系统会把 claim 数推高一到两个数量级，
**TSV 台账 + 每 claim 一 manifest + CAS 的组合需要在目标量级上做一次真实压测**，
而不是假设前代的可用性自动迁移。

### 三、第三种 claim kind（逻辑推断）需要而这个系统从未有过的东西

前代的两条通道各有一个**"重执行等价物"**：data 有 `dvc repro`（真跑一遍），
source 有"逐字子串在快照里"。**推断没有天然的重执行等价物**——这是设计难点的全部所在。
一手证据（F-32 的 D3）说明推断失效是真实且致命的失败模式：
**每条 claim 都 100% 复现，组合起来却推不出论文保留的那句论点。**

具体缺什么：

**I-1 · 前提闭包 + 状态传导（DAG 检查，Class-0 离线确定性）**
`raw_ref` 存前提 claim_id 列表；门必须校验：所有前提存在、无环、
且**没有一条 `logically-derived` 的结论挂在 `unverified`/`pending` 的前提上**。
前代连"kind 不认识就判 FAIL"之外什么都没有（F-02/C-7）。

**I-2 · warrant（推理许可）必须被显式声明且属于封闭枚举**
前提 → 结论之间的**步骤类型**（演绎 / 统计推广 / 因果识别 / 类比 / 溯因）必须写死在
`inferences/<cid>.md` 里。理由：F-14 证明"读起来像论证的散文"正是字符数门最擅长盖章的东西；
不声明 warrant，推断通道会立刻退化成第二个 200 字符门。

**I-3 · 结论强度不得超过最弱前提（模态/量词降级检查）**
F-32 D3 的失效精确地是这个：前提被诚实地放宽（把 Fukushima 疏散 + Chernobyl 高端计入分子，
得 ~0.2-0.5 deaths/TWh），**结论句却原封不动保留了 "comparable to wind and solar"**
（而 wind ~0.035、solar ~0.019，相差约一个数量级）。
门必须能对"前提改变后结论是否仍成立"提出问题——最低限度是**强度标注 + 敏感性标注**
（这也与 5 条 honesty flags 里的 "c3 ~821x ratio is best-case: a modestly higher nuclear
estimate (0.06-0.07) roughly halves it" 同构）。

**I-4 · 口径三元组（指标名 / 样本口径 / 对比对象）必须随前提传导**
5 条 honesty flags 里至少 3 条是**数字为真、口径被换**（无 CI 就断言等价；
0.03 内嵌低估的 Chernobyl 计数却宣称"已包含事故death"；WNA 转引 IPCC）。
推断门必须校验前提之间的口径可比性，否则"每个数字都对、拼起来是错的"会被 100% 复现率背书。

**I-5 · 独立再推导 + 反例构造，作为门的输入工件（Class-2）**
既然没有重执行，唯一等价物是 **maker ≠ checker 的再推导**：
复核者独立从前提出发推一遍，并**必须提交反例构造记录**（找不到反例也要记录搜索过程）。
门校验：工件存在 + reviewer id ≠ producer id + 反例记录非空 → 才写状态。
身份必须取自 harness 侧的 childId（不可取 manifest 里的自报字段）。
前代把"独立性"完全交给 prompt 措辞（C-9），零机械强制。

**I-6 · 来源独立性分级必须进入推断的前提质量**
"n1 (IPCC 12g) 和 n5 (Fukushima 2,313) 源自 World Nuclear Association（行业机构）而非 IPCC/官方重建"
——**转引链在前代台账里完全不可表达**（`raw_ref` 只有一个 URL 字段）。
推断以这类前提为基础时，结论强度必须自动降级。

**I-7 · 推断失效必须能反向污染已 verified 的结论**
F-32 的场景是：论文改了（loop iteration 2，见 `eval/verdicts/nuclear-safety.json` 的 `_note`），
诚实地加了 tail-accounting，**但没有回头修那句论点**。
v2 需要"前提变更 → 依赖它的推断结论自动置 `stale`"的传导，
这正是前代 `reproduced` 死列（F-02/C-8）所缺的动态语义。

---

## 未决问题

1. **`--verify-sources` 的真实确认率是多少？** 唯一的一手数据点是 `CHANGELOG.md:45-46`：
   "black-death's 3 quotes confirmed at their live URLs; nuclear's 2 flagged ⚠️ (JS/blocked)"。
   （注意这是**当时**的规模：`CHANGELOG.md:28` 记录 nuclear 当时是 "3-stage DVC + 2 source"，
   后来才扩到 5 data + 7 source，所以"2 条"不是笔误，只是那一刻的全部 source claim。）
   即已知样本上的联网确认率是 **3/5 = 60%，且失败全部集中在同一个来源域**。
   我没有联网重跑（会改写用户仓库的 `gate_report.md`，且结果依赖当下网络状态）。
   v2 若要给 source 通道定 SLA，必须在自己的语料上实测这个比率——
   60% 这个量级正是"必须在抓取时刻落 CAS 快照、事后只对快照校验"的直接理由（见 R-5）。

2. **门崩溃时的真实退出行为未穷举。** `rigor_gate.py:135` 用 `l.split("\t")` 无引号解析，
   claim_text 里含 tab 会错位；:147 的索引访问在列数不足时抛 IndexError。
   我验证了"抛异常 → 非零退出 → harness 正则匹配不到 → repro=None → D4 静默消失"这条链的后半段（F-22），
   但没构造前半段的真实崩溃样本。v2 的台账解析必须用带 schema 校验的读取器。

3. **`gate_report.md` 是否曾被手工编辑过？** 四份报告的 mtime 全是 eval 跑的时刻（F-28），
   git 状态显示工作树有大量未提交变更，我无法从当前工作树区分"生成的"与"手改的"。
   这本身说明 **v2 必须让门产物携带自证签名**（生成器版本 + 输入 hash），否则报告不可信。

4. **freehand vs gated 的 A/B 从未跑过。** `DESIGN.md:112-117`（"The honest test"）与
   `CHANGELOG.md:59-60`（"remains the top open item"）、`README.md:26`（"has not been completed"）
   三处一致承认。**所以"这套门是否真的提升质量"在前代是未经检验的**——
   v2 的 Milestone-1 A/B 不是锦上添花，而是补上前代欠的那笔债；
   并且要注意：前代之所以跑不成，部分原因是 scoreboard 的 SHIP 本身不可信（C-4），
   A/B 的度量必须先 fail-closed 才有意义。

5. **positions.md 的 cartographer 独立性在前代是零强制**（C-9）。
   我无法从工件判断四个 run 的 positions.md 究竟是独立 cartographer 产出还是 orchestrator 顺手写的
   ——**没有任何来源痕迹进入工件**。v2 若沿用"独立制图"这一角色，
   必须让工件携带产出 agent 的 harness 身份，否则这个角色在审计上不存在。

6. **`eval/corpus/*/answer_key.json` 的 `benchmark_claims` 该由谁消费？**（F-25）
   它是现成的"独立于作者台账的数值基准"，前代造了却没接。
   v2 是否要用它做"文献基准 vs 我方 claim 的数值一致性检查"，是一个待定的设计选择
   （潜在收益高，但会引入"文献基准本身是否可靠"的二阶问题）。

7. **量级迁移未验证**（R-10）。前代最大 run = 12 claims / 214B 原始数据。
   v2 的目标量级（高并行、多 loop）下，TSV + per-claim manifest + CAS 的读写与并发行为
   需要一次真实压测才能确认契约仍然成立。
