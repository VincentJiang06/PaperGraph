# Research Log — 最低工资与就业 (2015-2024 US natural experiments)

## Root question
最低工资上调是否降低就业?以2015-2024美国州/城市自然实验为主要证据,调和 Card-Krueger 式准实验(效应小/零)与竞争性市场理论(预测下降)之间张力。机制:monopsony / 成本转嫁 / 非工资调整(工时、福利、招聘门槛、自动化)。效应是否非线性(随 bite/Kaitz index)?

## Viewpoints & claims

### V1 竞争性市场理论:预测就业下降
- C1.1 (独立可答): 2015-2024有没有严肃自然实验发现州/城市级最低工资上涨显著降低就业(尤其大幅上调案例)?
- C1.2 (adversarial to V2/monopsony-optimism): 大幅上调(西雅图$15+, 加州快餐$20)是否有负效应证据?

### V2 Card-Krueger式证据:效应接近零
- C2.1: Cengiz et al. 2019 QJE (bunching estimator, 138次州级变动) 发现什么?
- C2.2 (adversarial): 该研究是否在所有幅度下都成立,还是有阈值/异质性?

### V3 Monopsony 机制
- C3.1: 劳动力市场垄断买方势力的证据基础是什么(集中度、跳槽摩擦)?
- C3.2 (adversarial): monopsony模型本身预测存在最优最低工资上限,超过后就业下降——是否有证据当前上调正在接近/超过该点?

### V4 成本转嫁(涨价)机制
- C4.1: 是否有证据显示价格上涨部分/大量吸收了最低工资成本,从而是效应小的原因之一?

### V5 非工资边际调整
- C5.1: 工时是否比人头就业更敏感(hours vs headcount margin)?
- C5.2: 福利/非货币补偿是否被削减?
- C5.3: 自动化是否因最低工资上涨而加速(尤其可自动化岗位)?
- C5.4: 招聘门槛/技能要求是否提高,挤出低技能求职者?

### V6 非线性:效应随 bite(上调/中位数工资比值)变化
- C6.1: Cengiz et al. 是否发现高bite下效应变负(阈值大概多少)?
- C6.2: 西雅图/加州快餐$20的bite有多高,是否落入"高风险区"?
- C6.3 (adversarial to V6): Dube综述/meta是否认为即使高bite效应仍很小,非线性证据不够强?

## Findings

### C1.1 / C2.1 竞争模型基线 vs 实证零效应
- Cengiz, Dube, Lindner, Zipperer (2019 QJE), bunching estimator, 138次1979-2016州级最低工资变动: "the overall number of low-wage jobs remained essentially unchanged over five years following the increase"; "We also find no evidence of disemployment when we consider higher levels of minimum wages."
- 但样本中最高的州级 Kaitz index(最低工资/本地中位数工资)只到约59%——即证据的"零效应"结论有范围限制,不能外推到极高bite。
- Lean: 支持"效应接近零",但证据有bite上限,不能一般化到所有幅度 → 直接喂给V6非线性讨论。

### C1.2/C6 adversarial 大幅上调案例
- Seattle: Jardim et al. (NBER w23532, AER Pol 2019) 用WA行政数据: 2016年涨到$13,"reduced hours worked in low-wage jobs by 6-7 percent, while hourly wages...increased by 3 percent", 总工资单下降,月均减少$74/低薪岗位。
- 但同期 Reich, Allegretto, Godoey (Berkeley IRLE, synthetic control): "synthetic control models suggest that restaurant industry employment at all wage levels did not significantly change following Seattle's minimum-wage increases" — 用行业加总数据得零效应。
- 两方法论分歧(个体行政数据 vs 行业加总的合成控制)是文献内部真实张力,不是伪造分歧。
- Lean: mixed——效应的符号依赖于用"工时"还是"人头"衡量,以及个体层面 vs 行业加总层面。这正指向V5(非工资边际:工时优先于人头调整)。

### C1.2/C6 2024 加州快餐 $20 (AB 1228) —— 最新、最高bite的自然实验之一
- Clemens, Edwards, Meer (NBER w34033, 2025): $16→$20(相对全美快餐业约+8%相对工资), "employment in California's fast food sector declined by 2.7 percent...from September 2023 through September 2024"; 调整趋势后3.2%;点估计约损失18,000个岗位。
- Reich & Sosinskiy (Berkeley IRLE/CWED, 2025): 用Glassdoor等新数据,"did not reduce employment"; 覆盖工人周薪上升约8-11%;价格上涨约1.5%(四美元汉堡约涨6美分)。
- 与西雅图案例结构相同的"dueling studies"(行政/微观 vs 合成控制/加总;经济学右翼智库背景 vs 劳工资助背景机构)。
- Lean: mixed/open——两派方法论都非平凡缺陷,应作为"证据不确定但都不支持大灾难式失业"的例证,同时承认负效应估计并非零。

### V3 Monopsony 机制
- Card (2022 AER, presidential address "Who Set Your Wage?"): "researchers have used a number of different strategies to identify the elasticity of firm-specific labor supply. A growing consensus is that firms have some wage-setting power" —证据基础是有限但不为零的买方垄断力。
- Azar, Marinescu, Steinbaum (ReStud 2023, retail部门): 低集中度市场"significantly decrease employment"于最低工资上涨后;高集中度市场效应"less negative" 甚至 "estimated to be positive"。直接支持"monopsony解释零效应"的空间异质性证据。
- Wiltshire/McPherson/Reich(Sosinskiy) IRLE working paper: 纽约/加州47个涨到$15+的县,fast-food数据,"substantial pay growth and no disemployment effects"; "Minimum wage increases reduce separation rates and raise wages faster than prices at McDonald's stores; both findings imply a monopsonistic labor market with declining rents."
- Lean: 支持monopsony能解释部分/多数近零效应,尤其在集中度较高、离职率高(高流失率行业如快餐)的劳动力市场。

### C3.2 adversarial: monopsony是否也有上限?
- 未找到明确证据表明"当前上调已系统性超过monopsony最优点"——CBO对全国性$15的模拟(非monopsony模型)仍预测净损失(中位数130万),提示:monopsony框架在局部/渐进上调下解释力强,但外推到全国性大幅统一上调(federal $15,相对更多低工资地区中位数的bite会畸高)时,竞争模型的下降预测重新占优。
- CBO (2019): "1.3 million people would lose jobs if the federal minimum wage were raised to $15 per hour by 2025"; 区间"about zero and 3.7 million"。
- Lean: monopsony对局部/渐进上调解释力强,但不是无限的;全国统一大幅上调时风险上升——为V6非线性提供跨政策尺度的佐证。

### V4 成本转嫁(涨价)
- Renkin, Montialoux, Siegenthaler (ReStat 2022,超市扫描数据,2001-2012州级变动): "A 10% minimum wage hike translates into a 0.36% increase in the prices of grocery products. This magnitude is consistent with a full pass-through of cost increases into consumer prices."
- CA快餐案例中 Reich/Sosinskiy 也发现价格涨约1.5%(伴随8-11%工资涨幅)——价格转嫁并非能完全解释,但是缓冲渠道之一。
- Lean: 支持——价格转嫁是解释"就业未大跌"的重要但非唯一渠道,尤其零售/餐饮这类可转嫁给本地消费者的行业。

### V5 非工资边际调整
- Clemens (2021 JEP, 综述) "How Do Firms Respond to Minimum Wage Increases? Understanding the Relevance of Non-employment Margins": 列举 evasion, output prices, noncash compensation(福利), job attributes/effort, skill-mix, labor-capital mix 等边际;"firms can adjust... by making noncash benefits... less generous."
- Jardim et al.(Seattle): 工时降6-7% > 就业人数变化——工时边际比人头边际更敏感,是关键的"缓冲阀"。
- Lordan & Neumark (2018, Labour Economics, CPS 1980-2015): "increasing the minimum wage decreases significantly the share of automatable employment held by low-skilled workers, and increases the likelihood that low-skilled workers in automatable jobs become nonemployed"——自动化替代效应在可自动化制造业尤其明显。
- Clemens, Kahn, Meer (2021 JOLE) "Dropouts Need Not Apply?": ACS+Burning Glass招聘数据,"workers employed in low-wage occupations are older and more likely to have a high school diploma following recent statutory minimum wage increases"; 招聘广告中高中学历要求上升——低技能/低学历求职者被挤出岗位可得性,即使总"就业人数"不降,弱势群体的可得岗位在缩小。
- Lean: 支持——就业总量的"零效应"掩盖了工时、福利、招聘门槛、自动化上的显著调整;这是调和张力的核心机制之一:总量稳定不等于个体/边际群体无损。

### V6 非线性 bite/Kaitz index
- Cengiz et al. 覆盖的州级样本bite上限约59%,零效应。
- Godoey & Reich (2021, low-wage counties, 51 events 2004-2016,45州750县): 利用州内县级中位数工资差异,"relative minimum wage ratios reach as high as .82"(82%),依然"did not detect adverse effects on employment, weekly hours or annual weeks worked"。
- 但加州快餐$20案例(相对快餐业自身工资分布bite极高,覆盖了大量此前低于$20的岗位)出现了两派对立估计,其中Clemens等估计出净负值(-2.7~-3.2%,约1.8万岗位),说明高bite区间证据不再是"稳定零",而是变得有争议/分散。
- Lean: mixed支持非线性——现有高质量准实验的"安全区"大致到70-80%左右的相对bite仍多为零效应,但当bite进一步逼近或超过当地/行业工资分布上段(如CA快餐案例这种"一次性" $16→$20的行业专项跳涨)时,估计开始出现显著且有分歧的负值,方差和分歧本身就是"风险上升"的信号。
- adversarial (C6.3): Dube (2019, UK Low Pay Commission综述): "the most up to date body of research from US, UK and other developed countries points to a very muted effect of minimum wages on employment, while significantly increasing the earnings of low paid workers." 该综述整体基调仍是"效应很小",未强调强非线性——需要在文中如实呈现这一保留意见。

## Root synthesis (thesis)
零效应的"平均"结论是真实但语境受限的:(1) 在美国过去十年多数州/城市级渐进式上调、bite多在40%-80%区间的样本中,monopsony租金空间+成本转嫁+工时/福利/招聘门槛的非工资调整,三条渠道共同吸收了理论上的失业压力,总就业量确实近似不变;(2) 但当bite被单次推到行业工资分布的高段(如CA快餐$16→$20)或被推广到全国统一大幅上调(联邦$15模拟)时,零效应的稳健性下降、估计出现分裂,竞争模型的下降预测重新获得部分支持力。校准判断:效应函数不是常数零,而是随相对bite呈现"平坦区+尾部风险上升"的形状,零效应结论在中等bite区间(粗略59%-80%左右)有较强证据支持,在高bite尾部证据不足且开始出现显著负估计。


## Done
- article.md written, body CJK char count = 1714 (within 1500-1800 hard limit).
- 15 sources cited (S1-S15), each verbatim-quoted and saved to sources/S<n>.txt.
- Counterpoints section explicitly engages: (a) monopsony's own upper bound (C3.2 adversarial), (b) Dube's muted-effect synthesis not emphasizing nonlinearity (C6.3 adversarial), (c) that headcount-neutral findings mask hours/benefits/hiring-bar/automation costs to marginal workers.
