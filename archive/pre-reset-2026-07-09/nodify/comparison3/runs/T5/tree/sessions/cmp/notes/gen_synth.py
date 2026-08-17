# -*- coding: utf-8 -*-
import json
base="sessions/cmp/notes"
U={ 'DOC-0001':'https://www.nber.org/papers/w25434','DOC-0002':'https://www.journals.uchicago.edu/doi/10.1086/685449',
    'DOC-0003':'https://www.nber.org/papers/w24147','DOC-0006':'https://irle.berkeley.edu/publications/',
    'DOC-0010':'https://www.nber.org/papers/w19262','DOC-0012':'https://irle.berkeley.edu/publications/brief/effects-of-the-20-california-fast-food-minimum-wage/',
    'DOC-0013':'https://www.cato.org/research-briefs-economic-policy/did-californias-fast-food-minimum-wage-reduce-employment'}
def ev(doc,quote,title,note=None,loc='abstract'):
    return {"title":title,"doc_id":doc,"quote":quote,"url":U[doc],"locator":loc,"tool":"web_fetch","note":note}
items={}
items['N-0010']=("mixed",[],
 "识别风险真实但有界:Meer-West显示含州趋势的水平型设定会漏掉经由job growth实现的负效应,支持'零可能是测不出'的担忧;但Cengiz的bunching对pooled估计给出较窄置信区间,直接压制了'功效不足'这一路。结论:单个合成控制研究功效常有限,应看设计互补的证据体(bunching+边界断点+动态)而非任一单点。","medium",
 [ev('DOC-0010',"the minimum wage reduces job growth over a period of several years. These effects are most pronounced for younger workers and in industries with a higher proportion of low-wage workers.","Meer-West:水平设定漏动态"),
  ev('DOC-0001',"the overall number of low-wage jobs remained essentially unchanged over five years following the increase","Cengiz:pooled估计精度较高")],
 ["跨研究的最小可检测效应(MDE)分布有多大?"])
items['N-0013']=("mixed",[],
 "monopsony不是纯事后合理化:DLR预测并验证了'分离下降'这一可证伪指纹,且Azar证明买方势力结构上普遍;但低薪快餐/零售雇主众多、离职频繁,买方势力更可能来自搜寻摩擦而非集中度,故monopsony是部分而非普适的解释。它能消化温和上调的相当部分冲击,但不足以独力解释所有近零。","medium",
 [ev('DOC-0002',"Separations and accessions fall among affected workers, especially those with low tenure.","DLR:可证伪的分离下降"),
  ev('DOC-0003',"Based on the DOJ-FTC horizontal merger guidelines, the average market is highly concentrated.","Azar:结构性买方势力")],
 ["搜寻摩擦型vs集中度型monopsony在低薪部门各占多大权重?"])
items['N-0017']=("mixed",[],
 "非工资边际证据确实不一致:加州快餐$20未见削工时/加剧排班,支持'margins未必都动'的质疑;但西雅图工时明显下降、价格转嫁在RMS/CA20中都稳健。综合:价格转嫁是最稳健的margin,工时高度依情境(西雅图强、加州快餐弱),福利/培训边际证据薄弱。'成本被转移'总体成立,但具体到哪条margin因地因业而异。","medium",
 [ev('DOC-0012',"reports no evidence of employers cutting hours or increasing just-in-time scheduling in response","CA20:未见工时/排班调整",'brief'),
  ev('DOC-0013',"reduced fast-food employment by 3.6 percent","CA20反方:若不减margin则可能减员",'report')],
 ["福利/非工资补偿(排班稳定性、培训)缺乏高质量因果证据。"])
items['N-0020']=("mixed",[],
 "阈值在美国已充分观测的区间内确实未被干净识别:Cengiz称即便更高水平也无就业损失,支持'阈值多为外推'的质疑;但$15联邦(CBO)与$20快餐(反方估计)所处的相对工资更高,并出现或预测负效应。结论:非线性作为方向可信,但拐点位置的经验精度低,现有'安全'结论对相对比值的外推应保守。","medium",
 [ev('DOC-0001',"We also find no evidence of disemployment when we consider higher levels of minimum wages.","Cengiz:观测区间内无阈值迹象"),
  ev('DOC-0013',"reduced fast-food employment by 3.6 percent","CA20反方:更高相对水平的负估计",'report')],
 ["把最低/中位比值作为连续自变量,美国数据能否定位拐点区间?"])
items['N-0024']=("supports",[],
 "对红队的有效反驳:红队最有力的负效应多来自特定设定(大衰退、高bindingness、含州趋势的水平回归);而不依赖增长counterfactual的bunching与边界断点设计仍落在近零,西雅图中数据更全的餐饮估计也更接近零。近零对温和上调是稳健的,红队缩小了但未推翻它。","medium",
 [ev('DOC-0001',"We also find no evidence of disemployment when we consider higher levels of minimum wages.","Cengiz:设计不依赖增长反事实"),
  ev('DOC-0006',"found no evidence of job loss in Seattle's restaurant industry, even as hourly pay reached $13.","Berkeley:数据更全的估计近零")],
 ["若给红队证据更高权重,'近零'区间的上界会移动多少?"])
items['N-0002']=("supports",["N-0008","N-0009","N-0010"],
 "实证地基:2015-2024为止最强的整合性准实验(Cengiz bunching覆盖138次上调)给出低薪岗位总数五年内基本不变、就业弹性近零且精度较高;西雅图分歧主要是测量对象(工时vs人数)之别而非政策效果;识别/功效担忧真实但被互补设计的证据体压制。校准判断:对温和州级上调,近零(小负)是当前最有依据的经验结论,但它是'headcount近零',非'零成本'。","high",
 [ev('DOC-0001',"the overall number of low-wage jobs remained essentially unchanged over five years following the increase","Cengiz核心结果")],
 ["bunching对tradable部门外溢与5年以上长期动态的覆盖仍有限。"])
items['N-0003']=("supports",["N-0011","N-0012","N-0013"],
 "机制A—monopsony/摩擦是调和CK与竞争理论的首要通道且有可证伪支撑:DLR的分离/雇佣双降是买方势力/搜寻摩擦的直接指纹,Azar证明买方势力结构上普遍。但低薪部门的买方势力更多源于摩擦而非集中,故monopsony能解释温和上调近零的相当部分,却非全部——它需与成本转嫁、非工资边际共同作用。","medium",
 [ev('DOC-0002',"We find that minimum wages have a sizable negative effect on employment flows but not on stocks.","DLR:流量降存量不降")],
 ["turnover节省能定量覆盖多大比例的加薪成本?"])
items['N-0004']=("supports",["N-0014","N-0015","N-0016","N-0017"],
 "机制B—成本主要经非headcount边际消化:价格转嫁最稳健(杂货full pass-through,快餐~1.5%),工时是被低估的边际(西雅图工时-6/7%、月报酬-$74),自动化/门槛是长期出口(Lordan-Neumark)。这解释了为何headcount近零却非无代价:代价被转移到价格(消费者)、工时(在职者)与岗位构成(最边际者)。但各margin权重因地因业而异,福利边际证据薄弱。","high",
 [ev('DOC-0012',"price increases of about 1.5 percent— or about 6 cents on a four-dollar hamburger","转嫁量化",'brief')],
 ["跨margin的相对权重缺乏统一的因果分解。"])
items['N-0005']=("mixed",["N-0018","N-0019","N-0020"],
 "非线性:方向可信、拐点位置不精。观测充分的温和区间内(Cengiz)即便较高水平也近零;但$15联邦(CBO中位-130万)与$20快餐(反方-3.6%)所处相对工资更高,出现或预测明显负效应。校准:就业效应确随最低/中位(Kaitz)比值非线性放大,存在低比值'安全区'与高比值'风险区',但拐点的经验精度低,现有安全结论不宜外推到未观测的高比值。","medium",
 [ev('DOC-0013',"reduced fast-food employment by 3.6 percent","高相对水平负估计",'report')],
 ["美国数据能否把拐点定位到具体的Kaitz区间(如0.5-0.6)?"])
items['N-0006']=("mixed",["N-0021","N-0022","N-0023","N-0024"],
 "红队检验:竞争理论并未被证据击溃。Neumark-Shirley显示文献重心偏负(约79%负估计),Meer-West指出水平设定漏掉动态,Clemens-Wither在高bindingness+衰退下测得明显负效应。但这些最强负结果集中在特定设定;不依赖增长反事实的bunching/边界断点仍近零。结论:近零主张被收窄、被加上条件(温和幅度、非衰退、看对margin),但未被推翻——'近零'与'偏负'的分歧很大程度是幅度/群体/设定之别。","high",
 [ev('DOC-0001',"We also find no evidence of disemployment when we consider higher levels of minimum wages.","近零对设计稳健")],
 ["给红队证据体系统性加权后,合意的中心估计会落在哪个弹性区间?"])
items['N-0007']=("mixed",["N-0025","N-0026","N-0027"],
 "异质性与分配:平均近零掩盖分布。加州快餐$20(高相对水平)证据分歧(Berkeley无损vs反方-3.6%);负担集中在青年/低技能(Neumark-Shirley更强负)与边际企业(Luca:中位餐厅退出+14%)。校准:即便平均近零,谁受损很重要——最边际的工人与企业承担了主要(仍不大的)调整,这正是竞争理论压力的真实落点。","medium",
 [ev('DOC-0013',"reduced fast-food employment by 3.6 percent","高相对水平案例分歧",'report')],
 ["被挤出的最低技能工人与退出企业岗位的再吸收率是净福利的关键未知。"])
items['N-0001']=("mixed",["N-0002","N-0003","N-0004","N-0005","N-0006","N-0007"],
 "校准判断:对2015-2024美国州级/城市级、幅度温和(相对中位数比值处历史区间内)的上调,最低工资对就业(headcount)的效应小到近零——Cengiz bunching是最强整合证据;但'近零'≠'零成本',更≠'普遍无害'。张力的调和有四层:①monopsony/搜寻摩擦(DLR分离下降、Azar买方势力)使温和上调可在不减员下逼近竞争工资;②成本主要经价格转嫁(RMS full pass-through、快餐~1.5%)传给消费者;③非工资边际吸收余下冲击——工时(西雅图-6/7%)、自动化/招聘门槛(Lordan-Neumark);④分布:损失集中在青年/低技能与边际企业(Luca退出+14%)。竞争理论并非错,而是其'减员'预测被这些边际重新导向,并主要在高相对工资区显形。非线性成立:效应随Kaitz比值非线性放大,$15联邦(CBO中位-130万)与$20快餐(反方-3.6%)标示风险区上端,但拐点经验精度低。综合置信度:对'温和上调近零'为中-高;对'高比值转负'为中;对拐点具体位置为低。","medium",
 [ev('DOC-0001',"the overall number of low-wage jobs remained essentially unchanged over five years following the increase","近零的最强整合证据"),
  ev('DOC-0002',"Separations and accessions fall among affected workers, especially those with low tenure.","monopsony/摩擦机制"),
  ev('DOC-0013',"reduced fast-food employment by 3.6 percent","高相对水平的负向前沿",'report')],
 ["最低/中位(Kaitz)比值的负效应拐点在美国数据中的具体区间仍未被干净识别。",
  "各调整margin(价格/工时/自动化/门槛/退出)对给定冲击的相对权重缺乏统一因果分解。",
  "加州快餐$20(AB1228)的就业效应尚未收敛(Berkeley无损 vs 反方-3.2/3.6%)。",
  "被挤出的最低技能工人与退出企业岗位的净再吸收率,决定近零的真实福利含义。",
  "衰退期(Clemens-Wither)与扩张期上调的负效应可外推性存疑。"])
for nid,(lean,children,summ,conf,evs,oq) in items.items():
    obj={"node_id":nid,"lean":lean,"summary":summ,"confidence":conf,
         "based_on":{"children":children,"evidence":evs},"open_questions":oq}
    with open(base+"/con_"+nid+".json","w",encoding="utf-8") as f: json.dump(obj,f,ensure_ascii=False,indent=1)
print("wrote", len(items), "synthesis files")
