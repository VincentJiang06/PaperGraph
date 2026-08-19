# 留出集二 · 首跑结果

预测哈希 `52d88ab797361730a96e5a6bd7fa9c9ef24233fda327e79bb1454be539c000ab`
（`PREDICTIONS.sha256`，落盘早于本文件第一次运行）。

```
判定正确 4/8
预测命中 5/8      ← 我事前对系统行为的把握程度
```

**4/8 是可引用的那个数字。** 第一批留出集首跑是 5/8，修完 8/8 之后就烧掉了；
这一批换成 GWAS 摘要（科学计数法），首跑掉到 4/8。
**换一个从未见过的文体，正确率掉了一半**——这比任何一次修复后的满分都说明问题。

| 编号 | 应判 | 预测 | 实测 | |
|---|---|---|---|---|
| J-1 | attributed | attributed | **unverified** | ✗ 意外 |
| J-2 | unverified | unverified | unverified | ✓ |
| J-3 | attributed | unverified | unverified | 事前预告的失败 |
| J-4 | attributed | attributed | attributed | ✓ |
| J-5 | attributed | attributed | attributed | ✓ |
| J-6 | unverified | attributed | attributed | 事前预告的失败 |
| J-7 | attributed | attributed | **unverified** | ✗ 意外 |
| J-8 | unverified | attributed | unverified | 判对了，**但理由不是我预测的那个** |

## 三条意外是**同一个**缺陷

J-1 / J-7 / J-8 的门报告里是同一句话：

```
caveats: ["payload_pre_token_not_whitelisted"]
polarity_marker: ["NEG-P:worse"] / ["NEG-P:another"] / ["NEG-P:included"]
scopes_found: 0
```

`scopes_found: 0`——**句子里根本没有否定**。拦住它们的是 L1-c 的
**前置位白名单**：紧邻数值之前的那个词必须在受控表里，否则降级。
三个词分别是 `worse`（"survival was significantly worse (83% ...)"）、
`another`（"another 21 suggestive associations"）、
`included`（"The study included 374,254 participants"）。
三个都是完全正常的英文，三个都不在表里。

### 这不是新缺陷，是**已声明的代价第一次被量出来**

`src/gates/g-polarity.mjs` 的注释原话：

> 代价是真实的、且必须说清楚：合法但没被收进白名单的写法会被降到 ST-A。

写得很清楚。但**从来没有人量过"多频繁"**。现在有数了：

**一批没参与过修复的真实语料，8 条里 3 条因为白名单未覆盖而降级 —— 37.5%。**

这个数字此前不存在，因为所有标定集的前置词都是白名单里那些
（`of` `was` `reached` `达到`）——**标定集在这一维度上不是随机样本**。
这与 [[boundary-statements-rot]] 是同一形状：一句写清楚的边界，
因为写得清楚，反而没有人再去量它。

### 三个词的语义类别，恰好是表里已有的那两类

- `included` / `includes` —— 断言性动词，与表里的 `reported` `showed` `recorded` 同类
- `another` —— 中性限定词，与表里的 `the` `a` `an` 同类
- `worse` —— 比较级形容词，**表里一类都没有**

值得注意的是**为什么比较级是安全的**：真正改写数值含义的构造
（`lower than 92%` / `at most 92%` / `below 92%` / `as low as 92%`）
在数值之前的那个词永远是 `than` / `most` / `below` / `as`，
**不是比较级本身**。`than` 不在白名单里，加了比较级也仍然不在。

但**本文件不做这个修改**。理由是本项目自己的规矩（`tests/holdout/run.mjs` 头注）：

> 不许为了让它变绿而改代码，除非那个改动同时能在外部标定集上站住。

而且一旦改了，这批留出集就和第一批一样烧掉了。**4/8 先记账。**

## 一条预测错在两头（J-8）

我预测千分位逗号会被 G-FRAME 的子句切分切碎，导致 fail-open。**两头都错**：

- 逐字包含判定对 `374,254` 是 `matched: "exact"` —— 逗号根本没造成问题；
- 真正拦住它的是白名单（`included`），而不是我说的那个机制；
- 而且我这条用例自己有毛病：`group: 'total'` 这个槽值在原句里不存在，
  所以包含判定本来就该判 false。**用例构造得不好，结论碰巧对。**

记下来是因为：**"判对了"和"判对了理由"是两件事**，而留出集只自动核对前者。
这次是靠逐条读门报告才发现的。

## 两条事前预告的失败（仍然是真实缺陷）

**J-3 · 上标负号 ≠ 连字符。** 预测正确：NFKC 把 U+207B 归到 U+2212
而不是 U+002D，所以 `10⁻³` 与 `10-3` 归一化之后仍不相等。
本项目此前的 NFKC 修复（E-3 / T4-1）处理的全是全角→半角，从未遇到这一档。

**J-6 · 英文数词。** 预测正确：`NUMERICISH` 只认阿拉伯数字与中文数字，
`three` 不被当成数值载荷，于是同句竞争读数 `49` 不触发 G-FRAME，
没有 discriminator 也放行。与 H-5（`nonsignificant` 不在算子表）同一类。

## 一条新记的盲点（J-5）

G4 那篇摘要**自己前后矛盾**：前面写 European 队列 `four novel loci`
（TUT4/RYK/MOXD1/UBAP2），后面写 `three novel loci`（TUT4/RYK/MOXD1）。
系统按合同放行（转录属实），判成〔已归因〕。

**单篇内部一致性**在本系统的六值状态里没有任何一档表达。
一篇自相矛盾的摘要里的一句话，与一篇自洽摘要里的一句话，在系统眼里完全一样。
与 H-8（I²=98% 不可见）并列，记入未闭合项。
