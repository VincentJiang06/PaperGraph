# 留出集二 · 快照出处与版权

五篇 GWAS / 孟德尔随机化摘要，**全部 CC BY**，2026-08-19 经 Europe PMC
`resultType=core` 取回，`license` 字段逐篇核实。摘要为纯文本（已去 HTML 标签），
未做任何改写——三种 `10⁻⁸` 写法是各篇论文自己的排版，不是本项目构造的变体。

| 文件 | PMID | DOI | PMCID | 许可 |
|---|---|---|---|---|
| `G1-42181176.txt` | 42181176 | `10.3389/fendo.2026.1805824` | PMC13189953 | CC BY |
| `G2-41560095.txt` | 41560095 | `10.1097/md.0000000000047177` | PMC12826245 | CC BY |
| `G3-41125582.txt` | 41125582 | `10.1038/s41467-025-64337-7` | PMC12546916 | CC BY |
| `G4-41844886.txt` | 41844886 | `10.1038/s41598-026-43993-9` | PMC13129092 | CC BY |
| `G5-41075272.txt` | 41075272 | `10.1093/hmg/ddaf131` | PMC12627943 | CC BY |

复核命令（任何人可重跑）：

```
curl -s "https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=EXT_ID:41844886&format=json&resultType=core" \
  | python3 -c "import json,sys;r=json.load(sys.stdin)['resultList']['result'][0];print(r['license'],r['doi'])"
```

## 为什么保留整段摘要而不是只留被引句

与外部标定集同一条理由：J-5 的证据力**就在于同一篇摘要里另一句话**
（前面写 `four novel loci`，后面写 `three novel loci`）。截成一句，
这条自相矛盾就看不见了。
