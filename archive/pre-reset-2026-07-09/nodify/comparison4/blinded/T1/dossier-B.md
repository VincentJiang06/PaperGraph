# Investigation: 系统性证据地图:2020–2025 年 AI/自动化对劳动力市场的一手实证研究——按研究设计与方法学质量分层、分领域(任务级替代/增效、岗位级净增减、工资、特定人群、跨国差异)加权综合,并标注分歧、一致与开放问题。

## Lines of inquiry

### L1 [orientation: neutral]
  - statement: 任务级证据:在具体工作任务上,AI(尤其生成式)一手实验/准实验主要显示增效(augmentation,提升生产率/质量)还是替代(substitution)?效应量与适用条件如何。
  - conclusion: [supports/high] 任务级证据现达 6 项 RCT/准实验,一致显示生成式 AI 以增效为主,并已覆盖客服(+14%)、写作(-40%时/+18%质)、咨询(界内+12.2%)、软件开发(Copilot RCT 快 55.8%;三企 4,867 人完成任务 +26.08%)。novice-benefit 在客服/写作/两项开发研究中反复出现。但边界更清晰:(a) Dell'Acqua 锯齿前沿——界外任务正确率反降 19pp;(b) Otis 肯尼亚 RCT——平均≈0 且异质性反向(高绩效+15%/低绩效-8%),AI 可能放大差距。结论:任务级 augmentation 稳健且跨职业,但'增益且压缩不平等'是有条件的,取决于任务是否落在能力前沿内及用户如何取用建议。
  ### L1.1 [orientation: neutral]
    - statement: Brynjolfsson, Li & Raymond(2023, NBER w31161;2025 QJE):对某大型客服公司 5,179 名坐席分阶段(staggered)引入生成式 AI 对话助手,坐席级生产率(每小时解决问题数)平均提升 14%,新手/低技能者 +34%,资深/高技能者几无变化——客服任务上以'增效+压缩技能差距'为主。
    - conclusion: [supports/high] 客服任务上生成式 AI 助手显著增效(+14%),且效应集中于新手/低技能者(+34%),对高技能者几无影响——支持'任务级以增效为主、并压缩技能差距'。
    - evidence:
      - Brynjolfsson, Li & Raymond — Generative AI at Work (NBER w31161) — https://www.nber.org/papers/w31161 — "Access to the tool increases productivity, as measured by issues resolved per hour, by 14% on average, including a 34% improvement for novice and low-skilled workers but with minimal impact on experienced and highly skilled workers."
  ### L1.2 [orientation: neutral]
    - statement: Noy & Zhang(2023, Science):453 名大学学历专业人员的预注册在线 RCT,随机给一半人使用 ChatGPT,中级专业写作任务平均耗时下降 40%、产出质量上升 18%,并压缩工人间不平等——写作任务上生成式 AI 显著增效且更惠及低能力者。
    - conclusion: [supports/high] 预注册 RCT 显示 ChatGPT 使中级写作任务耗时降 40%、质量升 18%,并压缩工人间不平等——任务级随机化因果证据支持增效且更惠及低能力者。
    - evidence:
      - Noy & Zhang — Productivity effects of generative AI (Science 2023) — https://www.science.org/doi/10.1126/science.adh2586 — "ChatGPT substantially raised productivity: The average time taken decreased by 40% and output quality rose by 18%."
  ### L1.3 [orientation: adversarial]
    - statement: Dell'Acqua 等(2023, HBS/BCG 田野实验):758 名 BCG 顾问随机分组,前沿内 18 项任务用 GPT-4 者多完成 12.2%、快 25.1%、质量显著更高;但对刻意置于能力'前沿之外'的复杂任务,用 AI 者正确率反而低约 19 个百分点——'锯齿状前沿'表明 AI 会在界外损害而非提升绩效。
    - conclusion: [supports/high] BCG 顾问田野实验:前沿内任务 AI 大幅增效(+12.2% 完成、快 25.1%),但刻意置于能力前沿之外的复杂任务上,用 AI 者正确率反低 19 个百分点——'增效'有条件边界,界外会损害绩效。
    - evidence:
      - Dell'Acqua et al. — Jagged Technological Frontier (HBS WP 24-013) — https://ssrn.com/abstract=4573321 — "they completed 12.2% more tasks on average, and completed tasks 25.1% more quickly"
      - Dell'Acqua et al. — Jagged Technological Frontier (HBS WP 24-013) — https://ssrn.com/abstract=4573321 — "consultants using AI were 19 percentage points less likely to produce correct solutions compared to those without AI."
  ### L1.4 [orientation: neutral]
    - statement: Peng, Kalliamvakou, Cihon & Demirer(2023, arXiv 2302.06590,微软/GitHub RCT):95 名软件开发者随机分组实现一个 JavaScript HTTP 服务器,获得 GitHub Copilot 的处理组比对照组快 55.8% 完成(95% CI 21–89%),且异质效应更利于经验较少者——软件开发任务上生成式 AI 显著增效。
    - conclusion: [supports/high] 软件开发任务上生成式 AI 显著增效:Copilot 组比对照组快 55.8% 完成编码任务,且经验较少者获益更大——将任务级增效证据从客服/写作/咨询扩展到高价值的软件开发。
    - evidence:
      - Peng et al. — GitHub Copilot RCT (arXiv 2302.06590) — https://arxiv.org/abs/2302.06590 — "The treatment group, with access to the AI pair programmer, completed the task 55.8% faster than the control group."
  ### L1.5 [orientation: neutral]
    - statement: Cui, Demirer, Jaffe, Musolff, Peng & Salz(2025, SSRN 4945566 / Management Science 2026):在微软、埃森哲与一家匿名财富100电子制造企业开展三项 RCT,共 4,867 名开发者随机获得 GitHub Copilot,完成任务数平均增加 26.08%(SE 10.3%),经验较少者采用率与生产率增益都更高——真实企业部署下的任务级增效,且惠及低经验者。
    - conclusion: [supports/high] 真实企业规模化部署证据:三项 RCT、4,867 名开发者中,用 Copilot 者完成任务数 +26.08%,且低经验者采用率与增益更高——增效在真实生产环境成立,并再度惠及低经验者。
    - evidence:
      - Cui et al. — Three Field Experiments with Software Developers (SSRN 4945566) — https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4945566 — "our analysis reveals a 26.08% increase (SE: 10.3%) in completed tasks among developers using the AI tool."
  ### L1.6 [orientation: adversarial]
    - statement: 对'AI 增效并压缩组内不平等'的反证:Otis, Clarke, Delecourt, Holtz & Koning(2024,肯尼亚 640 名企业主 5 个月 RCT,GPT-4 经 WhatsApp 提供经营建议):平均效应约为零,且异质性反向——基线高绩效者收入/利润 +15%,低绩效者反而 -8%(约 0.25 SD 差距),AI 可能放大而非缩小差距。
    - conclusion: [supports/medium] 对'AI 增效并压缩不平等'的有力反证:肯尼亚 640 企业主 RCT 中平均效应≈0,且高绩效者 +15%、低绩效者 -8%(≈0.25SD 差),源于低绩效者选择实施了不当建议——生成式 AI 可能放大而非缩小组内差距,'低技能者更受益'非普遍规律。
    - evidence:
      - Otis et al. — Uneven Impact of Generative AI on Entrepreneurial Performance — https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4671369 — "the above-median performers saw profits or revenue climb by 15%, whereas the low-performers' revenues sagged by 8%."
  ### L1.7 [orientation: neutral]
    - statement: Dell'Acqua 等(2025,NBER w33641):宝洁 776 名专业人员的预注册田野实验(真实新产品创新任务,2×2 随机化:有/无 AI × 个人/团队)——'有 AI 的个人'绩效追平'无 AI 的团队',即 AI 可复制人类协作的部分收益;AI 还打破职能壁垒(R&D 与商务背景者都产出更均衡方案),并激发更多正向情绪。把任务级增效证据从'个人生产率'拓展到'团队协作/专长共享'维度。
    - conclusion: [supports/high] Dell'Acqua 等(2025,宝洁 776 人预注册田野实验)把任务级增效证据推进到团队维度:'有 AI 的个人'绩效追平'无 AI 的团队',即 AI 复制了人类协作的部分收益;AI 还打破职能壁垒(R&D 与商务背景者都产出更均衡方案),并激发更多正向情绪。方法学质量高(预注册、随机化、真实企业创新任务、大样本),且与前 6 项 RCT 一致指向增效/专长均衡化——强化了任务级 augmentation 的稳健性,并新增'AI 可部分替代团队协作与跨职能专长'的洞见。
    - evidence:
      - Dell'Acqua et al. — The Cybernetic Teammate (NBER w33641, 2025) — https://www.nber.org/papers/w33641 — "individuals with AI matched the performance of teams without AI, demonstrating that AI can effectively replicate certain benefits of human collaboration"
      - Dell'Acqua et al. — The Cybernetic Teammate (NBER w33641, 2025) — https://www.nber.org/papers/w33641 — "Professionals using AI produced balanced solutions, regardless of their professional background"

### L2 [orientation: neutral]
  - statement: 岗位级证据:AI/自动化采用后,在企业、地区与在线平台层面的就业净增减(岗位数、招聘、订单、离职)方向与幅度。
  - conclusion: [mixed/medium] 岗位级证据的核心新洞见:净效应随分析层级与国别翻转。具身自动化(机器人)——美国地区级净负(每千工人 1 台使就业-人口比 -0.2pp,〔另一分支〕);但企业级为正:西班牙采用者净创造就业 +10%、早期采用者 +50% vs 非采用者 -20%(Koch,〔另一分支〕),法国 plant/firm/industry 三层均正(就业弹性 0.28,含非熟练),且正效应集中于面对国际竞争行业的 business-stealing(Aghion,挂 〔另一分支〕)。差异机制:采用者以规模/生产率扩张增雇,部分以非采用者(及他国)裁员为代价——总量净值取决于聚合层级。生成式 AI——到 2019 在线职位未见总量冲击(〔另一分支〕);Hampole(2025)因果显示 AI 任务暴露压低劳动需求,但被采用企业生产率驱动需求上升抵消,总量温和(〔另一分支〕);在线平台暴露类目出现真实替代信号但为重配非毁灭(〔另一分支〕)。合成:岗位级负效应在美国机器人地区级与暴露平台细分可见,但企业/行业级与生成式 AI 总量层面多为温和或正——「替代真实但局部/未聚合,且符号随层级与制度翻转」。
  ### L2.1 [orientation: neutral]
    - statement: Acemoglu & Restrepo(2020, JPE《Robots and Jobs》):用行业机器人渗透+地方产业结构构造暴露度(shift-share IV),估计 1990 年后美国通勤区每千名工人多 1 台工业机器人使就业-人口比下降约 0.2 个百分点——岗位级净效应为负(注:对象是工业机器人自动化,非生成式 AI)。
    - conclusion: [supports/medium] 美国通勤区准实验:每千工人多 1 台工业机器人使就业-人口比降约 0.2pp——自动化对岗位的净效应为负;但对象为工业机器人而非生成式 AI,外推需谨慎。
    - evidence:
      - Acemoglu & Restrepo — Robots and Jobs (JPE 2020) — https://www.journals.uchicago.edu/doi/10.1086/705716 — "One more robot per thousand workers reduces the employment-to-population ratio by 0.2 percentage points and wages by 0.42%."
  ### L2.2 [orientation: adversarial]
    - statement: Acemoglu, Autor, Hazell & Restrepo(2022, JOLE《AI and Jobs: Evidence from Online Vacancies》):用 2010 年起美国近乎全量在线职位数据,发现 AI 暴露度高的企业在减少非 AI 岗位招聘,但到 2019 年 AI 对总量就业/工资无可检测的宏观影响。
    - conclusion: [supports/medium] 企业级在线职位数据:AI 暴露企业减少非 AI 岗位招聘(微观有信号),但到 2019 年 AI 对总量就业/工资无可检测宏观影响——支持'总量冲击尚不可检测'的反方。
    - evidence:
      - Acemoglu, Autor, Hazell & Restrepo — AI and Jobs: Online Vacancies (JOLE 2022) — https://www.journals.uchicago.edu/doi/10.1086/718327 — "AI is currently substituting for humans in a subset of tasks but it is not yet having detectable aggregate labor market consequences."
  ### L2.3 [orientation: neutral]
    - statement: 在线自由职业/零工平台的替代信号:生成式 AI 冲击(ChatGPT/DALL·E/Midjourney 发布)后,暴露类目(写作、编程、图像)的岗位量、订单与收入相对变化——自然实验/准实验。
    - conclusion: [mixed/medium] 三项独立平台准实验:生成式 AI 在暴露类目产生真实需求冲击,但净效应是'重配'而非一律毁灭。可替代技能持续为负——Hui 等(Upwork)写作月接单 -2%/收入 -5.2%、图像 -3.7%/-9.4%;Demirci 等(另一平台)写作/编程职位发布 -21%、图像创作 -17%;Teutloff 等(300万+职位)写作/翻译 -20~50%。但 Teutloff 同时显示互补技能上升(ML +24%、AI 聊天机器人开发近三倍),新手需求普遍下降、转向资深。合成:平台是生成式 AI 岗位替代最早显形处,方向稳健为负于可替代技能;但伴随 AI 互补岗位创造,总量净值取决于两者相对规模(未定)。
    ### L2.3.1 [orientation: neutral]
      - statement: Hui, Reshef & Zhou(2024, Organization Science,Upwork 准实验/DiD):ChatGPT 发布后,写作类自由职业者的月接单量下降约 2%、月收入下降约 5.2%;DALL·E/Midjourney 发布后,图像类工作者月接单 -3.7%、收入 -9.4%;且高绩效/高技能者受冲击不减反增——真实在线劳动市场出现生成式 AI 的岗位与收入替代信号。
      - conclusion: [supports/medium] 真实在线劳动市场出现生成式 AI 的需求替代信号:ChatGPT 后写作类 Upwork 自由职业者月接单 -2%、月收入 -5.2%;图像 AI 后图像类 -3.7%、-9.4%;高技能者受冲击不减反增——与任务级增效并存的需求侧岗位/收入下降。
      - evidence:
      - Hui, Reshef & Zhou — Short-Term Effects of Generative AI on Employment (Org. Science 2024) — https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4527336 — "the number of monthly jobs for writing-related freelancers on Upwork declined by 2%, while monthly earnings declined by 5.2%."
    ### L2.3.2 [orientation: neutral]
      - statement: Demirci, Hannane & Zhu(2025, Management Science / CESifo WP 11276,全球领先自由职业平台面板):ChatGPT 推出后八个月内,写作与编程等自动化易感岗位的职位发布数相对手工密集岗位下降约 21%;图像生成 AI 出现后,图像创作类职位发布下降约 17%;剩余岗位复杂度与报酬更高——独立数据源上重现平台层面的需求替代。
      - conclusion: [supports/medium] 第二个独立平台数据源复现需求替代:ChatGPT 后八个月内写作/编程类职位发布相对手工岗位 -21%,图像 AI 后图像创作类 -17%,且剩余岗位更复杂高薪——与 Hui 等收敛,平台层面替代信号稳健。
      - evidence:
      - Demirci, Hannane & Zhu — Who Is AI Replacing? (Management Science 2025) — https://www.ifo.de/en/cesifo/publications/2024/working-paper/who-ai-replacing-impact-generative-ai-online-freelancing-platforms — "21% decrease in the number of job posts for automation-prone jobs related to writing and coding"
    ### L2.3.3 [orientation: adversarial]
      - statement: 对'平台=生成式 AI 净杀岗位'的反证/细化:Teutloff 等(2025, JEBO,300 万+ 职位、116 技能簇 GPT-4o 分类):可替代技能(写作/翻译)需求相对反事实降 20–50%,但互补技能需求上升——机器学习编程 +24%、AI 聊天机器人开发接近三倍;新手需求下降、转向资深。平台效应是需求'重配'(有赢家有输家),非一律毁灭。
      - conclusion: [supports/medium] 平台层面的生成式 AI 效应是需求'重配'而非单向毁灭:可替代技能(写作/翻译)需求相对反事实降 20–50%(与 Hui/Demirci 一致),但互补技能需求上升(ML 编程 +24%、AI 聊天机器人开发近三倍),同时新手需求下降、转向资深——支持'替代真实但伴随互补岗位创造,净效应为再配置'的反方细化。
      - evidence:
      - Teutloff et al. — Winners and Losers of Generative AI (JEBO 2025) — https://ideas.repec.org/a/eee/jeborg/v235y2025ics0167268124004591.html — "Jobs involving skills that can be partly substituted, such as writing and translating, have seen demand drop by 20 to 50 per cent."
  ### L2.4 [orientation: adversarial]
    - statement: Koch, Manuylov & Smolka(2021, Economic Journal《Robots and Firms》,西班牙制造业面板 1990–2016):机器人采用者四年内产出增 20–25%、劳动成本份额降 5–7pp、净创造就业约 +10%;1990–98 采用者到 1998–2016 岗位增逾 50%,而非采用者减逾 20%。企业层面机器人是净增就业——对「机器人=净减岗」的层级反证(但含采用者对非采用者的竞争性替代)。
    - conclusion: [supports/medium] 岗位效应随分析层级翻转:Koch 等(2021)西班牙制造业面板显示,机器人采用者四年内净创造就业约 +10%(产出 +20–25%、劳动成本份额 -5–7pp);早期采用者 1998–2016 岗位增逾 50%,而非采用者减逾 20%。企业层面机器人净增就业,与 Acemoglu-Restrepo 地区级净负(〔另一分支〕)相反——差异部分来自采用者对非采用者的竞争性替代(business-stealing),提示总量净值取决于聚合层级。
    - evidence:
      - Koch, Manuylov & Smolka — Robots and Firms (Economic Journal 2021) — https://academic.oup.com/ej/article-abstract/131/638/2553/6124631 — "leads to net job creation at a rate of 10%"
      - Koch et al. — adopters vs non-adopters — https://academic.oup.com/ej/article-abstract/131/638/2553/6124631 — "Firms that adopted robots between 1990 and 1998 increased jobs by more than 50% between 1998 and 2016, while non-adopters reduced jobs by more than 20% over the same period."
  ### L2.5 [orientation: neutral]
    - statement: Hampole, Papanikolaou, Schmidt & Seegmiller(2025, NBER w33509):用 NLP 构造 2010–2023 firm×occupation 的 AI/ML 任务暴露度,历史大学招聘网络作工具变量;AI 暴露度高的任务随后劳动需求下降,但暴露集中度可缓冲(工人再配置到未替代任务)。尽管任务级替代强,总量就业效应温和——暴露职业需求下降被采用企业生产率驱动的劳动需求上升抵消。
    - conclusion: [supports/medium] AI 任务替代真实但总量温和:Hampole 等(2025)用 NLP 构造 firm×occupation 的 AI 暴露度(2010–2023)、以历史大学招聘网络作工具变量,发现 AI 暴露高的任务随后劳动需求下降,但暴露集中度可缓冲(工人再配置到未替代任务);尽管任务级替代强,总量就业效应温和——暴露职业需求下降被采用企业生产率驱动的劳动需求上升抵消。为「任务级替代→岗位级总量温和」提供因果机制(桥接 〔另一分支〕 与总量)。
    - evidence:
      - Hampole, Papanikolaou, Schmidt & Seegmiller — AI and the Labor Market (NBER w33509, 2025) — https://www.nber.org/papers/w33509 — "Despite strong substitution at the task level, overall employment effects are modest, as reduced demand in exposed occupations is offset by productivity-driven increases in labor demand at AI-adopting firms."
      - Hampole et al. — task exposure lowers labor demand — https://www.nber.org/papers/w33509 — "Tasks with higher AI exposure subsequently experience reduced labor demand."

### L3 [orientation: neutral]
  - statement: 工资证据:AI 暴露度或采用对工资水平与工资分布(技能溢价、极化)的一手实证效应。
  - conclusion: [mixed/medium] 工资证据分两条线且互相张力。自动化/机器人侧稳健为负:Acemoglu-Restrepo(2020)每千工人多 1 台机器人使当地工资 -0.42%(〔另一分支〕);同组(2022, Econometrica)任务框架估计常规任务群体的相对工资下降解释了美国 40 年工资结构变化的 50–70%(〔另一分支〕)——自动化压低工资并加剧分布不平等的因果证据强。生成式 AI 侧分歧:企业暴露度准实验(Azar 2025)发现 ChatGPT 后暴露企业相对工资 -4.5%、初级新岗起薪 -6.3%(〔另一分支〕),而丹麦全国行政数据 DiD 对 AI 的工资/收入效应精确为零、排除 >2%(〔另一分支〕);Hampole(2025,context)给出机制:AI 暴露压低劳动需求但被采用者生产率抵消,总量温和。合成:自动化对工资(尤其分布)负效应已确立;AI 对工资的负效应在企业相对口径已显形、在全国绝对口径尚不可测——差异主要是识别层级(暴露企业相对 vs 全国人群)与时点。
  ### L3.1 [orientation: neutral]
    - statement: Acemoglu & Restrepo(2020, JPE):同一机器人暴露度识别下,每千名工人多 1 台机器人使当地工资下降约 0.42%——自动化对工资的一手因果效应为负(工业机器人,非 AI)。
    - conclusion: [supports/medium] 同一机器人暴露度识别:每千工人多 1 台机器人使当地工资降约 0.42%——自动化对工资的一手因果效应为负(工业机器人)。
    - evidence:
      - Acemoglu & Restrepo — Robots and Jobs (JPE 2020) — https://www.journals.uchicago.edu/doi/10.1086/705716 — "One more robot per thousand workers reduces the employment-to-population ratio by 0.2 percentage points and wages by 0.42%."
  ### L3.2 [orientation: adversarial]
    - statement: 对'AI/自动化压低工资'的反证:Humlum & Vestergaard 丹麦全国行政数据 DiD 显示,AI 聊天机器人对工资/收入的因果效应精确为零(置信区间排除大于 2% 的平均效应)——生成式 AI 迄今未压低采用者工资。
    - conclusion: [supports/medium] 生成式 AI(区别于工业机器人)迄今未压低工资:丹麦行政数据 DiD 对工资/收入估计精确为零,排除 >2% 的平均效应——与 〔另一分支〕 机器人工资 -0.42% 形成技术间张力(机器人 vs AI、时点、口径)。
    - evidence:
      - Humlum & Vestergaard — Still Waters, Rapid Currents (NBER w33777) — https://www.nber.org/papers/w33777 — "Difference-in-differences estimates for earnings, recorded hours, and wages all center on zero, with confidence intervals ruling out average effects larger than 2%."
  ### L3.3 [orientation: neutral]
    - statement: Acemoglu & Restrepo(2022, Econometrica《Tasks, Automation, and the Rise in US Wage Inequality》):任务框架+shift-share IV,1980–2016 美国;自动化的任务替代(task displacement)使专精于常规任务的人群相对工资下降,解释了过去四十年美国工资结构变化的 50–70%。工资极化/不平等的一手准实验因果证据(自动化侧,数量之外的价格维度)。
    - conclusion: [supports/high] 自动化的任务替代是过去四十年美国工资结构变化的主因之一:Acemoglu & Restrepo(2022)用任务框架估计,专精常规任务群体在快速自动化行业的相对工资下降,解释了 50–70% 的工资结构变化——为「自动化压低工资并加剧分布不平等」提供最强准实验因果证据(区别于总量工资水平)。
    - evidence:
      - Acemoglu & Restrepo — Tasks, Automation, and the Rise in US Wage Inequality (Econometrica 2022) — https://onlinelibrary.wiley.com/doi/full/10.3982/ECTA19815 — "Between 50% and 70% of changes in the U.S. wage structure over the last four decades are accounted for by relative wage declines of worker groups specialized in routine tasks in industries experiencing rapid automation."
  ### L3.4 [orientation: neutral]
    - statement: Azar, Giné & Sanz-Espín(2025, SSRN,1.38 亿美国工人 worker-firm 匹配数据的准实验):ChatGPT 发布后,职业结构更暴露于自动化的企业相对工资下降约 4.5%;新入职起薪按层级分化——初级 -6.3%、中级 -5.9%,资深工资稳定甚至上升;暴露企业还降低初/中级新岗的学历要求。AI(非机器人)对工资的一手因果负效应。
    - conclusion: [supports/medium] AI(而非机器人)对工资已有可测因果负效应:Azar 等(2025)用 1.38 亿美国工人 worker-firm 匹配的准实验,ChatGPT 发布后自动化暴露度更高的企业相对工资下降约 4.5%,且沿资历分化——初级新岗起薪 -6.3%、中级 -5.9%,资深稳定/上升。与丹麦/CPS 的总量精确零效应形成方法与口径张力(企业暴露排序 vs 全国人群)。
    - evidence:
      - Azar, Giné & Sanz-Espín — AI Is Already Eroding Wages (SSRN 5842084, 2025) — https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5842084 — "The average wage of exposed firms fell 4.5% relative to unexposed firms."
      - Azar et al. — junior/mid starting wages — https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5842084 — "starting wages of new positions for junior and mid-level workers in exposed firms fell by 6.3% and 5.9% respectively relative to unexposed firms, while senior wages remained stable or even increased."

### L4 [orientation: neutral]
  - statement: 特定人群证据:AI 对青年、入门级、低经验劳动者的差异化影响——他们是否首当其冲。
  - conclusion: [mixed/medium] 「入门级/青年首当其冲」证据天平近期向支持倾斜,但未定论。支持面以 AI 特有、企业内部证据为主:Canaries(Stanford/ADP)22–25 岁最暴露职业就业相对下降(〔另一分支〕);Hosseini-Lichtinger(2025)6200 万工人 DiD 显示 2023Q1 起采用企业初级就业相对急降、资深上升,主因放缓招聘(〔另一分支〕);Azar(2025)初级新岗起薪 -6.3%、暴露企业降初级学历要求与占比。反方仍有力:丹麦全国行政数据对含入门级的 11 个暴露职业估计精确零效应(〔另一分支〕);且 Canaries 作者自身稳健性更新指出,加入 firm-time 固定效应后显著下降仅出现在 2024 年,早期降幅或部分源于利率等其他因素。合成:AI 采用企业内部的资历偏向(初级受损、资深获益)方向渐趋一致,但(a)全国总量层面是否显现、(b)是否仅 2024 后、(c)企业内部相对下降能否等同总量,均未解决。
  ### L4.1 [orientation: neutral]
    - statement: Brynjolfsson, Chandar & Chen(2025, Stanford,ADP 薪酬管理数据):生成式 AI 广泛采用后,最暴露职业中 22–25 岁早期职业工人的就业出现约 16% 的相对下降,且在控制企业级冲击后仍存在,集中于 AI 替代(而非增效)任务的岗位。
    - conclusion: [mixed/medium] 入门级是否首当其冲证据分歧:美国 ADP 数据显示 22-25 岁最暴露职业就业相对下降约 16%(支持);而丹麦行政数据对 11 个暴露职业的收入/工时估计精确为零(反证)。差异可能源于国别、结果变量或时点。
    - evidence:
      - Brynjolfsson, Chandar & Chen — Canaries in the Coal Mine? (Stanford 2025) — https://digitaleconomy.stanford.edu/publication/canaries-in-the-coal-mine-six-facts-about-the-recent-employment-effects-of-artificial-intelligence/ — "early-career workers (ages 22-25) in the most AI-exposed occupations have experienced a 16 percent relative decline in employment"
      - Humlum & Vestergaard — Still Waters, Rapid Currents (NBER w33777) — https://www.nber.org/papers/w33777 — "we find no significant effects in any of our 11 occupations, including those with flexible, decentralized wage-setting."
  ### L4.2 [orientation: adversarial]
    - statement: 对'青年/入门级首当其冲'的反证:Humlum & Vestergaard 在丹麦对含入门级在内的 11 个 AI 暴露职业估计收入/工时零效应,未见早期职业者被差异化冲击——与 Canaries 的美国入门级下降相左。
    - conclusion: [supports/medium] 入门级差异化冲击并非普遍:丹麦对含入门级在内的 11 个暴露职业估计零效应,与 Canaries 的美国入门级相对下降 16% 相左——'青年首当其冲'存在国别与结果变量(就业 vs 收入/工时)分歧。
    - evidence:
      - Humlum & Vestergaard — Still Waters, Rapid Currents (NBER w33777) — https://www.nber.org/papers/w33777 — "we find no significant effects in any of our 11 occupations, including those with flexible, decentralized wage-setting."
  ### L4.3 [orientation: neutral]
    - statement: Hosseini & Lichtinger(2025, SSRN/Stanford,美国简历+招聘数据,6200 万工人×28.5 万企业 2015–2025,DiD/三重差分):以「AI integrator」招聘标记企业采用生成式 AI;2023Q1 起采用企业的初级(junior)就业相对非采用者急剧下降、资深就业继续上升,降幅主要来自放缓招聘而非增加离职;按学历呈 U 形(中层学历降幅最大)。AI 作为「资历偏向型技术变革」的一手证据。
    - conclusion: [supports/medium] 生成式 AI 呈「资历偏向型技术变革」:Hosseini & Lichtinger(2025)用 6200 万工人×28.5 万企业 2015–2025 的 DiD/三重差分,以「AI integrator」招聘标记采用;2023Q1 起采用企业初级就业相对非采用者急剧下降(次级报道约 7–12%)、资深就业继续上升,降幅主因放缓招聘而非离职;按学历呈 U 形(中层学历降幅最大)。独立于 Canaries,强化「入门级首当其冲」于 AI 采用企业内部。
    - evidence:
      - Hosseini & Lichtinger — Generative AI as Seniority-Biased Technological Change (SSRN 5425555, 2025) — https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5425555 — "beginning in 2023Q1, junior employment in adopting firms declined sharply relative to non-adopters, while senior employment continued to rise."

### L5 [orientation: neutral]
  - statement: 跨国差异证据:AI 劳动力市场效应在不同国家/制度/发展水平上的异质性。
  - conclusion: [mixed/medium] 跨国差异证据(部分综合):效应存在显著国别/制度异质性。(1) 潜在暴露度随国家收入水平上升(ILO,〔另一分支〕),但(2) 高收入高暴露的丹麦实测收入/工时精确零效应(〔另一分支〕),说明暴露排序无法预测实现效应;(3) 同一 shift-share 识别下,德国机器人岗位净零(服务业抵消,〔另一分支〕)vs 美国净负(〔另一分支〕),制度(再培训/在职保护)可能是关键中介。合成:必须区分'暴露(预测)'与'实现效应(观测)',且制度环境显著调节自动化的净岗位/工资结果。
  ### L5.1 [orientation: neutral]
    - statement: ILO / Gmyrek, Berg & Bescond(2023, ILO 工作论文 96):用 GPT-4 对全球职业任务打分构造生成式 AI 暴露度,发现主要效应是增效而非自动化;文书类最暴露(24% 任务高暴露、58% 中暴露),且暴露程度随国家收入水平上升——跨国异质性显著(注:潜在暴露度预测,非事后因果)。
    - conclusion: [supports/low] ILO 全球暴露度分析:生成式 AI 主效应是增效而非自动化,文书类最暴露(24% 高/58% 中),且暴露程度随国家收入水平上升——跨国异质性显著。但为潜在暴露度预测,非事后因果,置信度低。
    - evidence:
      - Gmyrek, Berg & Bescond (ILO) — Generative AI and Jobs: Global Analysis (WP96 2023) — https://www.ilo.org/sites/default/files/wcmsp5/groups/public/@dgreports/@inst/documents/publication/wcms_890761.pdf — "the overwhelming effect of the technology will be to augment occupations, rather than to automate them."
      - Gmyrek, Berg & Bescond (ILO) — Generative AI and Jobs: Global Analysis (WP96 2023) — https://www.ilo.org/sites/default/files/wcmsp5/groups/public/@dgreports/@inst/documents/publication/wcms_890761.pdf — "24 percent of clerical tasks considered highly exposed and an additional 58 percent with medium-level exposure"
  ### L5.2 [orientation: adversarial]
    - statement: 对'潜在暴露度决定跨国实际效应'的反证:高收入、高暴露的丹麦(Humlum & Vestergaard)实测收入/工时零效应,说明 ILO 式暴露度排序无法预测各国真实劳动力市场结果。
    - conclusion: [supports/medium] 潜在暴露度不能预测各国实际效应:高收入、高暴露的丹麦实测收入/工时精确零效应,直接反例 ILO 式暴露排序的外推力——跨国综合须区分'暴露(预测)'与'实现效应(观测)'。
    - evidence:
      - Humlum & Vestergaard — Still Waters, Rapid Currents (NBER w33777) — https://www.nber.org/papers/w33777 — "We find precisely null effects of AI chatbot use on earnings and hours."
  ### L5.3 [orientation: adversarial]
    - statement: 对'机器人自动化净减岗位'的跨国反证:Dauth, Findeisen, Südekum & Woessner(2021, JEEA,德国行政数据 shift-share):机器人暴露在制造业造成岗位替代,但被服务业新增岗位完全抵消,总量就业无净损失;冲击主要落在初入劳动力市场的年轻人身上——与美国 Acemoglu-Restrepo 的净负结论形成制度性差异。
    - conclusion: [supports/high] 机器人自动化的岗位净效应存在制度性跨国分歧:德国行政数据显示制造业岗位替代被服务业新增完全抵消、总量就业无净损失,与美国 Acemoglu-Restrepo 的净负形成直接对照——同一 shift-share 识别、不同制度、相反净结论,冲击主要落在青年。
    - evidence:
      - Dauth et al. — The Adjustment of Labor Markets to Robots (JEEA 2021) — https://academic.oup.com/jeea/article-abstract/19/6/3104/6179884 — "Robot exposure, as predicted by a shift-share variable, is associated with displacement effects in manufacturing, but those are fully offset by new jobs in services."
  ### L5.4 [orientation: adversarial]
    - statement: Adachi, Kawaguchi & Saito(2024, Journal of Labor Economics《Robots and Employment: Evidence from Japan 1978–2017》):利用机器人单价、要素需求+任务法识别;机器人价格下降(→采用上升)提高就业与工资——机器人价格降 1% 使就业增约 0.44%,每千工人多 1 台机器人使就业增约 2.2%,工资效应亦为正。对美国「机器人净减就业/压低工资」的跨国反证。
    - conclusion: [supports/medium] 跨国反证:Adachi 等(2024)用机器人单价识别,日本 1978–2017 机器人渗透提高就业与工资——机器人价格降 1% 使就业 +0.44%,每千工人多 1 台机器人使就业 +2.2%,工资效应亦为正。方向与美国(Acemoglu-Restrepo 负)、德国(Dauth 净零)并列,凸显机器人就业效应的国别/识别口径异质:日本几乎全为国产机器人、规模/生产率渠道占优,提示制度与产业结构中介净效应。
    - evidence:
      - Adachi, Kawaguchi & Saito — Robots and Employment: Evidence from Japan (JLE 2024) — https://www.journals.uchicago.edu/doi/abs/10.1086/723205 — "an increase of one robot unit per 1,000 workers increases employment by 2.2%"
  ### L5.5 [orientation: adversarial]
    - statement: Aghion, Antonin, Bunel & Jaravel(2020/2021, CEPR/OFCE《What Are the Labor and Product Market Effects of Automation? New Evidence from France》):法国制造业微观数据 1994–2015,事件研究+shift-share IV;plant/firm/industry 三层自动化对就业影响均为正(含非熟练工业工人),就业弹性 0.28、利润 0.78、价格 -0.05、销售 0.37;行业层面正效应仅见于面对国际竞争的行业(business-stealing)。
    - conclusion: [supports/medium] 跨国/层级反证:Aghion 等(2020/2021)法国制造业微观数据+事件研究/shift-share IV 显示,plant/firm/industry 三层自动化对就业均为正(含非熟练工业工人),就业弹性 0.28(利润 0.78、价格 -0.05、销售 0.37);关键是行业层面正效应仅见于面对国际竞争的行业——business-stealing 机制:自动化企业以更低价格扩规模、抢占外国对手份额而增雇。提示「限制本国自动化保就业」可能弄巧成拙。
    - evidence:
      - Aghion, Antonin, Bunel & Jaravel — Labor and Product Market Effects of Automation: France (CEPR DP 14443) — https://ideas.repec.org/p/cpr/ceprdp/14443.html — "At all levels of analysis - plant, firm, and industry - the estimated impact of automation on employment is positive, even for unskilled industrial workers."
      - Aghion et al. — elasticities — https://ideas.repec.org/p/cpr/ceprdp/14443.html — "The estimated elasticity of employment to automation is 0.28, compared with elasticities of 0.78 for profits, -0.05 for prices, and 0.37 for sales."

### L6 [orientation: adversarial]
  - statement: 对抗线(红队):迄今 AI 对总量劳动力市场的可测量因果影响很小/被夸大——宏观就业与工资未见显著冲击,报道的'冲击'多为选择性样本、短期噪声或叙事驱动。
  - conclusion: [mixed/medium] 红队线(对根假设的最强 steelman)结论:'总量层面 AI 冲击迄今很小'这一半站得住,但'被夸大/叙事驱动/效应虚假'这一半站不住。支持面强而一致:丹麦全国行政数据 DiD 对 AI 的收入/工时因果效应精确为零、排除>2%(〔另一分支〕,含重度用户/入门级);美国全国 CPS 观测显示 ChatGPT 后约 33 个月劳动力市场'stability, not major disruption'(〔另一分支〕);Bick 等全国代表性调查给出机制——采用极快但当前仅 1–5% 工时由 AI 辅助、节省时间仅 1.4%(〔另一分支〕)。三者互证:到 2024–2025 尚无可测的经济体层面就业/工资冲击。但红队的强版本被树的其余部分证伪:任务级 RCT(+14%~+56%)、企业/平台准实验(Azar 相对工资 -4.5%、平台可替代技能 -20~50%、机器人地区级 -0.2pp)都显示真实的局部因果效应。故校准为 mixed:效应真实但'局部/未聚合、当前占用小',而非虚假或夸大——总量之所以不可测,主因当前 AI 对总劳动投入的占用仍小(1.4% 工时),不能等同于长期无冲击。
  ### L6.1 [orientation: adversarial]
    - statement: Humlum & Vestergaard(2025, NBER w33777,丹麦全国行政数据 link 采用调查,约 2.5 万工人/11 职业):双重差分估计 AI 聊天机器人对收入与工时的因果效应精确为零,置信区间排除大于 2% 的平均效应,即便对重度用户与入门级岗位亦然——与 RCT 报告的 >15% 生产率增益形成对比。
    - conclusion: [supports/high] 丹麦全国行政数据 DiD:AI 聊天机器人对收入与工时的因果效应精确为零,排除大于 2% 的平均效应,即便重度用户/入门级亦然——与 RCT 的 >15% 生产率增益并存,是'总量工资/工时冲击尚不可测'反方的最强 steelman。
    - evidence:
      - Humlum & Vestergaard — Still Waters, Rapid Currents (NBER w33777) — https://www.nber.org/papers/w33777 — "We find precisely null effects of AI chatbot use on earnings and hours. Difference-in-differences estimates for earnings, recorded hours, and wages all center on zero, with confidence intervals ruling out average effects larger than 2%."
  ### L6.2 [orientation: adversarial]
    - statement: Yale Budget Lab(2025,基于 CPS 的观测分析):ChatGPT 发布约 33 个月后,整体劳动力市场未见可辨识的经济体层面冲击;各 AI 暴露度分位的就业份额与职业构成变化速率未显著加快,且部分职业构成变动在生成式 AI 之前已在进行——支持'总量冲击迄今不可辨识'的反方。
    - conclusion: [supports/medium] 美国全国 CPS 观测支持'总量冲击迄今不可辨识':ChatGPT 后约 33 个月,劳动力市场整体呈'stability, not major disruption',暴露分位就业份额与职业构成变化速率未显著加快,部分变动更早于生成式 AI——与丹麦行政数据的精确零效应互为印证。
    - evidence:
      - Yale Budget Lab — Evaluating the Impact of AI on the Labor Market (2025) — https://budgetlab.yale.edu/research/evaluating-impact-ai-labor-market-current-state-affairs — "The picture of AI's impact on the labor market that emerges from our data is one that largely reflects stability, not major disruption at an economy-wide level."
  ### L6.3 [orientation: adversarial]
    - statement: Bick, Blandin & Deming(2025,NBER w32966):全国代表性美国调查(2024 年 8 月与 11 月两轮、逾万受访者)显示生成式 AI 采用极快(约 40% 18–64 岁人口使用,工作场景采用速度与 PC 相当),但当前仅 1–5% 的工作时长由生成式 AI 辅助,受访者报告的节省时间仅相当于总工作时长的 1.4%——快采用、小'占用',为'总量层面 AI 足迹迄今很小'的反方提供机制性证据(采用广度≠工时/产出层面的大规模位移)。
    - conclusion: [supports/medium] Bick, Blandin & Deming(2025,全国代表性美国调查,逾万受访者)为红队线补机制证据:生成式 AI 采用极快(约 40% 成年人使用,工作采用速度=PC),但当前仅 1–5% 工作时长由 AI 辅助、报告节省时间仅相当于总工时的 1.4%。这解释了微观 RCT 的大增益为何尚未转化为可测的总量冲击——采用广度≠工时/产出层面的大规模位移;当前 AI 对总劳动投入的'占用'仍小。支持'总量足迹迄今很小'的反方,但作者亦指出这暗示未来生产率增益空间可观(方向不确定)。
    - evidence:
      - Bick, Blandin & Deming — The Rapid Adoption of Generative AI (NBER w32966) — https://www.nber.org/papers/w32966 — "Between 1 and 5 percent of all work hours are currently assisted by generative AI, and respondents report time savings equivalent to 1.4 percent of total work hours."
      - Bick, Blandin & Deming — The Rapid Adoption of Generative AI (NBER w32966) — https://www.nber.org/papers/w32966 — "nearly 40 percent of the U.S. population age 18-64 uses generative AI"

## Root conclusion

[mixed/medium] 根结论(按方法学质量加权,统摄 25 项 2020–2025 一手实证研究):AI/自动化对劳动力市场的效应是『真实但迄今未聚合、且符号随层级/制度/技术类型翻转』。分层校准如下。(1) 最强证据【高置信】:任务级——生成式 AI 以增效为主,≥7 项 RCT/田野实验一致给出 +14%~+56% 生产率/速度增益、且低技能/新手获益更大(压缩不平等),但有条件:仅在能力『前沿内』成立(Dell'Acqua 锯齿前沿界外 -19pp;肯尼亚 RCT 平均≈0 且异质性反向可放大差距);2025 宝洁田野实验further显示『个人+AI=无AI的团队』。机器人自动化——数十年尺度上在部署地稳健压低工资并加剧工资不平等(Acemoglu-Restrepo:每千工人+1台→当地工资-0.42%;任务框架解释美国40年工资结构变化50–70%),因果证据强。(2) 中等证据【中置信】:净就业效应在总量层面符号不定,随分析层级(地区/企业/行业/全国)、国别制度、技术类型翻转——机器人使美国地区级就业-人口比降(-0.2pp/台·千人)但企业级常为正(西班牙采用者+10%、法国弹性0.28,靠 business-stealing 扩规模增雇);德国净零(服务业抵消)、日本为正(+2.2%/台·千人,国产机器人产业)。(3) 新兴且争议【中/低置信】:AI 采用企业内部出现资历偏向(初级相对受损、资深获益;Canaries 22–25岁暴露职业-16%、Hosseini-Lichtinger、Azar 初级起薪-6.3%),平台自由职业是生成式 AI 岗位/收入替代最早显形处(写作/翻译/图像职位-20~50%),伴随互补技能上升——重配还是净毁灭未定。(4) 关键零结果【高置信、识别良好】:全国总量口径,生成式 AI 对收入/工时/就业的因果效应迄今精确近零(丹麦排除>2%;美国CPS『stability, not major disruption』)——机制是当前 AI 对总劳动投入的『占用』仍小(Bick:仅1.4%工时被节省),而非效应虚假。综合:微观增益与局部/企业/平台位移都真实,但因渗透仍浅尚未在全国总量显形;自动化(机器人)有更长的、稳健的分配性工资伤害与层级依赖的就业记录。方向非命定——受任务前沿契合、企业战略(抢单扩张)、国别制度强烈中介。

## Open gaps

  - 滞后/扩散:当前 AI 足迹极小(约1.4%工时),不足3年的窗口能否排除渗透加深后滞后的总量冲击——这是最核心的未决问题
  - 企业内部的资历/入门级偏向(初级受损)能否、何时传导到全国总量?是否仅 2024 后出现(Canaries 稳健性:加 firm-time FE 后显著仅见于2024)
  - 重配 vs 净毁灭:企业相对与平台的真实位移已确立,但被替代岗位与新增互补岗位的净差额在总量口径未定
  - 外部效度:短期、单企业/特定任务的 RCT 增益能否外推到长期、一般均衡、经济体层面的净结果
  - 机器人 vs 生成式 AI 的符号分歧,多少源于真实技术差异,多少源于识别策略(价格 vs shift-share 暴露)与国别产业结构
  - 制度中介的因果化:再培训/在职保护等具体政策如何驱动『德国零 vs 美国负』,尚多为相关而非已识别的因果
  - 生成式 AI 究竟压缩还是扩大不平等取决于条件(前沿契合、用户如何取用建议),净分配效应未解
  - 测量:全国描述性总量指标可能对入门级/局部替代不敏感,需随采用加深部署更强识别的总量设计
