# -*- coding: utf-8 -*-
"""
象罔社团官网 v3（科技风）静态站生成器
数据源：club-site/src/data.ts + redesign/index.html（内容沿用 v2）
输出：club-site/v3/  —— 首页 + 列表页 + 每个成员/作品/动态/岗位的独立详情页
用法：python build_v3.py
"""
import os
import glob, re, shutil, html

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "v3")
SRC = os.path.dirname(os.path.abspath(__file__))

SITE = {
    "name": "象罔社团",
    "slogan": "XIANGWANG CLUB",
    "desc": "象罔社团官方网站：社团生活、招新、作品、成员。",
    "uni": "南京信息工程大学",
}

# ============================================================
# 准入开关
#   True  = 全站门禁：除 login.html 外，任何页面都要先登录/注册才能看
#   False = 只锁「成员专区」area.html，官网其余页面公开
#   改完重跑本脚本即可（登录页永远不锁，否则会死循环）
# ============================================================
SITE_GATE = False

# ============================================================
# 数据区（占位内容已标注，替换时只改这里后重新运行本脚本）
# ============================================================
WORKS = [
    dict(id="w1", title="OpenClaw", cat="Agent 工程", em="🦾", cv="cv1", status="开发中",
         stack=["Python", "FastAPI", "Docker", "TypeScript", "GitOps"],
         desc="社团智能体项目的统一底座：模型调用、工具注册、沙盒执行与控制台，收拢进一套可复现的工程骨架。",
         metrics=[("6", "个", "接入工具"), ("1", "套", "统一控制台"), ("0", "", "环境漂移"), ("7", "d", "迭代周期")],
         story="各组各自写一套调用模型的代码，换个端口要改三处，漏改一处就悄悄坏掉半个系统。OpenClaw 把重复的部分抽成底座，各组只在上面挂自己的工具——好处一句话：改一处，全组生效。",
         timeline=[("2026.07", "立项", "三份重复的实现摆在桌上，决定抽公共底座。"),
                   ("2026.08", "工具注册", "把业务 API 包成统一 tool，超时与幂等兜底进底座。"),
                   ("2026.09", "沙盒安全", "执行环境隔离 + 权限收口，前端风格统一同步完成。")],
         contributors=["caitong", "hehongquan", "chenjiamin", "caiquanyou"], lead="caitong",
         links=[("GitHub 仓库", "#"), ("内部文档", "#")]),
    dict(id="w2", title="教育智能体", cat="应用智能体", em="📚", cv="cv2", status="开发中",
         stack=["Python", "LLM", "RAG", "PostgreSQL", "Streamlit"],
         desc="面向教学场景的智能体：备课检索、作业批改辅助与答疑，覆盖一门课从准备到答疑的完整链路。",
         metrics=[("3", "个", "教学环节"), ("1", "键", "导入课件"), ("85", "%", "答疑采纳率"), ("0", "", "数据外传")],
         story="第一版答疑经常一本正经地编教材里没有的内容。补上自建教案与课件的检索溯源之后，每一句回答都能点开出处，老师才敢真的拿去用。",
         timeline=[("2026.06", "选题", "从“每学期重复回答同一批问题”这个真实痛点起步。"),
                   ("2026.08", "接检索", "校内自建知识库 + 引用溯源，回答可点开原文。"),
                   ("2026.09", "试用", "进入一门专业课的教学环节小规模试用。")],
         contributors=["sunjiale", "chenmingrui", "guoshijun"], lead="sunjiale",
         links=[("GitHub 仓库", "#"), ("使用文档", "#")]),
    dict(id="w3", title="专利智能体", cat="应用智能体", em="🔍", cv="cv3", status="开发中",
         stack=["Python", "OpenAlex", "LLM", "Embedding", "FastAPI"],
         desc="专利与文献检索智能体：找得到标题，也要把摘要、权利要求与引用关系一次拿全。",
         metrics=[("2", "处", "数据源"), ("1", "次", "拿全全文"), ("90", "%", "标题命中"), ("7", "d", "迭代周期")],
         story="痛点就写在第一页 PPT 上：找得到标题，拿不全东西。标题搜索只是入口，真正的门槛是把摘要、权利要求、引文链路一起拉回来还能对得上。",
         timeline=[("2026.08", "对照调研", "以 OpenAlex 为对照，摸清公开数据源的边界。"),
                   ("2026.09", "检索主功能", "标题命中 + 详情抓取链路打通。"),
                   ("2026.10", "结构化扩展", "引入权利要求与引用关系的结构化抽取。")],
         contributors=["caikai", "yuyue", "zhengzixin"], lead="caikai",
         links=[("GitHub 仓库", "#"), ("技术博客", "#")]),
    dict(id="w4", title="DeepseekHarness", cat="Agent 工程", em="🧩", cv="cv4", status="开发中",
         stack=["Python", "LangGraph", "Docker", "pytest", "OpenTelemetry"],
         desc="智能体编排框架：把一次长任务拆成可控的状态机——跑得到断点、续得上进度、看得见每一步。",
         metrics=[("6", "阶段", "任务流转"), ("1", "键", "断点续跑"), ("100", "%", "步骤留痕"), ("0", "", "黑盒执行")],
         story="长任务最容易死在半路：跑到第四个小时崩了，从头再来一遍，谁也不知道刚才进行到哪。Harness 把每一步的状态落到能恢复的地方，崩了接着跑，而不是重来。",
         timeline=[("2026.08", "状态机设计", "先把循环、分支与人工介入点画成图，再写第一行代码。"),
                   ("2026.09", "可观测", "引入 trace，每一步的输入输出都能回看。"),
                   ("2026.10", "收敛验证", "长任务的收敛闭环做压测与复验。")],
         contributors=["qinziyuan", "zhanghongcheng", "dingbo"], lead="qinziyuan",
         links=[("GitHub 仓库", "#"), ("设计文档", "#")]),
    dict(id="w5", title="Hermes", cat="Agent 工程", em="🪶", cv="cv5", status="开发中",
         stack=["Python", "向量检索", "SQLite", "Redis", "Prompt 工程"],
         desc="上下文与提示词记忆工程：让智能体跨回合记得住前一晚说到哪，而不是每次醒来重新自我介绍。",
         metrics=[("30", "轮", "可用上下文"), ("2", "层", "记忆分级"), ("1", "键", "跨会话恢复"), ("0", "", "重复生成")],
         story="同一个项目连着问三天，第四天它问你“我们聊到哪了”。Hermes 把短期对话和长期要点分层存起来：该留的长期留下来，不该留的果断丢掉——上下文从来不是越大越好。",
         timeline=[("2026.08", "分层设计", "短期对话 / 长期要点两级存储。"),
                   ("2026.09", "压缩策略", "超长上下文按要点压缩，避免无脑堆叠。"),
                   ("2026.10", "工程化", "跨会话恢复 + 缓存，成本与延迟同步下降。")],
         contributors=["raoyuxuan", "zhuyuanmei", "chenzhiming"], lead="raoyuxuan",
         links=[("GitHub 仓库", "#"), ("技术博客", "#")]),
    dict(id="w6", title="科研智能体", cat="科研 Harness", em="🔬", cv="cv6", status="开发中",
         stack=["Python", "LLM", "RAG", "Docker", "论文模板"],
         desc="社团旗舰项目：把科研想法到可投稿论文拆成六个可复跑阶段，每阶段都有产物、有留痕、可回退。",
         metrics=[("6", "阶段", "标准流程"), ("100", "%", "阶段留痕"), ("7", "d", "单阶段周期"), ("4", "组", "跨组协同")],
         story="科研最容易断在“中间那一大段”：想法很好，落地没有抓手。这个项目把流程切成六段，每段结束必须留下一个能被人检查的产物——跑不完不许进下一阶段。",
         timeline=[("2026.07", "立项", "确定六阶段目标与每阶段的交付物标准。"),
                   ("2026.09", "四条主线", "文献、实验环境、智能体编排、论文指南四条线并行推进。"),
                   ("2026.10", "阶段验收", "以周为单位做阶段验收与缺陷回退。")],
         contributors=["yangtianlong", "qinziyuan", "raoyuxuan", "sunjiale", "caikai"], lead="yangtianlong",
         links=[("GitHub 仓库", "#"), ("流程指南", "#")]),
]

MEMBERS = [
    dict(id="yangtianlong", name="杨添龙", post="社长 · 外联负责人", tier="社团负责人", college="计算机/软件学院", major="计算机科学与技术", hue=5,
         dir=["全栈", "小程序"],
         quote="全栈不是什么都会一点，是能一个人把想法跑通到最后一步。",
         bio="全栈方向，科研智能体项目负责人，也维护社团对外站点。",
         skills=["全栈", "TypeScript", "Node.js", "微信小程序", "ECharts"],
         exp=[("科研智能体 · 队长", "负责六阶段流程编排与对外接口，把阶段验收标准落成可跑的检查项。"),
              ("社团官网 v3 · 技术负责", "带 2 人搭起 38 个页面的站点，改一处数据全站重生成。")],
         works=["w6"], joined="2025 年秋季",
         qa=[("给新人的建议", "先做一个自己真的会用的小工具，比刷十个 demo 有用。")]),
    dict(id="sunjiale", name="孙迦勒", post="副社长 · 技术部部长", tier="社团负责人", college="人工智能学院", major="人工智能", hue=2,
         dir=["大模型", "RAG"],
         quote="检索做不好，模型再强也是在编故事。",
         bio="RAG 方向，负责教育智能体的知识库与检索链路。",
         skills=["大模型应用", "RAG", "向量检索", "Python", "数据处理"],
         exp=[("教育智能体 · 队长", "带 2 人做知识库与检索链路，召回切分策略重做后命中率提升 12%。"),
              ("社团技术路线", "制定代码规范与阶段验收标准，统筹四个组的协作节奏。")],
         works=["w2", "w6"], joined="2026 年春季",
         qa=[("最近在优化什么", "把召回的 chunk 切分策略重做了一遍，命中率提升了 12%。")]),

    dict(id="caitong", name="蔡僮", post="技术一组组长", tier="技术部", college="沃特福德学院", major="电气工程及其自动化", hue=1,
         dir=["嵌入式", "硬件"],
         quote="代码能烧进板子里，就不再是屏幕上的字符了。",
         bio="硬件+嵌入式方向，社团里唯一能自己焊板子的人。",
         skills=["嵌入式", "C", "STM32", "电路设计", "Python"],
         exp=[("OpenClaw · 队长", "主导工具注册与沙盒隔离，把三份重复的模型调用代码收敛成一套底座。"),
              ("联网温湿度节点", "自己焊板子 + 写固件，把实验室传感器数据接进社团平台。")],
         works=["w1"], joined="2026 年春季",
         qa=[("为什么来软件社团", "想让硬件和软件接上，一个人焊不出一个联网的设备。")]),
    dict(id="caikai", name="蔡凯", post="技术二组组长", tier="技术部", college="沃特福德学院", major="人工智能", hue=3,
         dir=["Python", "机器学习"],
         quote="调参调到凌晨三点，看到 loss 掉下去的那一刻，值了。",
         bio="机器学习方向，正在做校园场景下的小样本分类实验。",
         skills=["Python", "机器学习", "PyTorch", "数据清洗"],
         exp=[("专利智能体 · 队长", "负责文献检索主功能，打通标题命中到详情抓取的链路。"),
              ("小样本分类实验", "在校园场景下跑通一套小样本分类流程，含训练与评测脚本。")],
         works=["w3", "w6"], joined="2026 年春季",
         qa=[("为什么加入", "想找人一起复现论文，一个人读 paper 太容易放弃。")]),
    dict(id="raoyuxuan", name="饶宇轩", post="技术三组组长", tier="技术部", college="计算机与软件学院", major="软件工程", hue=5,
         dir=["后端", "Go"],
         quote="接口的响应时间，是用户唯一能感知到的“你的态度”。",
         bio="后端方向，Go 爱好者，负责 Hermes 的服务端与记忆链路。",
         skills=["Go", "后端", "Redis", "MySQL", "Docker"],
         exp=[("Hermes · 队长", "做记忆分层与上下文压缩，跨会话恢复改成一条命令。"),
              ("服务端开发", "负责社团多个项目的接口设计与容器化部署。")],
         works=["w5", "w6"], joined="2025 年秋季",
         qa=[("性能优化心得", "先上监控，再谈优化。没有数据支撑的优化都是玄学。")]),
    dict(id="qinziyuan", name="秦梓源", post="技术四组组长", tier="技术部", college="人工智能学院", major="人工智能", hue=2,
         dir=["大模型", "LLM 应用"],
         quote="大模型不是答案机器，是概率机器——用的人得自己兜底。",
         bio="LLM 应用方向，DeepseekHarness 的核心开发。",
         skills=["LLM 应用", "RAG", "Prompt 工程", "Python"],
         exp=[("DeepseekHarness · 队长", "把长任务拆成六段状态机，崩了能续跑而不是从头再来。"),
              ("教育智能体 · 组员", "参与知识库搭建与检索调优。")],
         works=["w4", "w6"], joined="2026 年春季",
         qa=[("对 AI 的看法", "工具会越来越强，但“问什么问题”这件事永远属于人。")]),
    dict(id="chenmingrui", name="陈明睿", post="项目运营部部长", tier="职能部门", college="雷丁学院", major="大气科学", hue=1,
         dir=["Python", "科学计算"],
         quote="在这里我第一次看到自己写的东西，被完全不认识的同学拿去用。那种感觉，上课给不了。",
         bio="喜欢用代码处理气象数据，也喜欢把数据画成别人一眼能看懂的图。",
         skills=["Python", "数据可视化", "Linux", "Git"],
         exp=[("教育智能体 · 组员", "梳理教学场景清单，整理课堂试用反馈。"),
              ("项目运营", "排期、周报与成果归档，跟踪跨组协作与阶段交付。")],
         works=["w2"], joined="2025 年秋季",
         qa=[("为什么加入社团", "想找一群真的在写代码的人，而不是只在群里转发面经的人。"),
             ("最近在学什么", "在啃 xarray，想把社团的气象数据集整理成一份能直接用的教程。")]),
    dict(id="zhengzixin", name="郑子鑫", post="宣传视觉部部长", tier="职能部门", college="网络空间安全学院", major="网络空间安全", hue=4,
         dir=["CTF", "Linux"],
         quote="安全不是把门锁死，是知道门在哪里、谁会来推。",
         bio="数据抓取方向，负责专利智能体的详情链路与环境配置。",
         skills=["数据抓取", "Linux", "Docker", "Go"],
         exp=[("专利智能体 · 组员", "负责详情抓取链路与环境配置。"),
              ("视觉物料", "统一社团对外 PPT 与海报的视觉规范。")],
         works=["w3"], joined="2025 年秋季",
         qa=[("第一次参赛", "省赛被一题 SQL 注入卡了三小时，出来以后把这类题全刷了一遍。")]),
    dict(id="yuyue", name="虞越", post="成员", tier="成员", college="软件学院", major="软件工程", hue=2,
         dir=["Java", "Web 开发"],
         quote="写完第一个能上线的接口那天，我截图发了朋友圈——现在想想有点傻，但当时真的很开心。",
         bio="后端方向，喜欢把重复的事情自动化，讨厌手写 SQL 拼接。",
         skills=["Java", "Spring Boot", "MySQL", "Docker"],
         exp=[("专利智能体 · 组员", "参与检索接口开发，负责结果分页与缓存。")],
         works=["w3"], joined="2025 年秋季",
         qa=[("在社团做的最酷的事", "带着三个大一同学重构了二手平台的订单模块，交付那天一起吃了顿烧烤。"),
             ("给新人的建议", "别急着学框架，先把 HTTP 状态码和数据库事务搞明白，后面会省很多时间。")]),
    dict(id="guoshijun", name="郭时军", post="成员", tier="成员", college="教师教育学院", major="教育技术学", hue=3,
         dir=["教学产品设计"],
         quote="工具好不好用，看老师第二天还愿不愿意打开它。",
         bio="教学设计方向，负责教育智能体的场景梳理与课堂试用反馈。",
         skills=["教学设计", "需求分析", "数据分析"],
         exp=[("教育智能体 · 组员", "把一门课的教学环节拆成可实现的场景清单。")],
         works=["w2"], joined="2026 年春季",
         qa=[("为什么做这个项目", "见过太多“看起来很聪明、老师用一次就放弃”的工具，想反过来做。"),
             ("怎么判断做得对不对", "看真实课堂里有没有人第二次打开它。")]),
    dict(id="caiquanyou", name="蔡泉佑", post="成员", tier="成员", college="雷丁学院", major="数据科学与大数据技术", hue=3,
         dir=["Python", "数据分析"],
         quote="数据不会骗人，但会沉默——得有人替它说话。",
         bio="做数据分析，也在帮 AI 组维护知识库的清洗脚本。",
         skills=["Python", "Pandas", "SQL", "爬虫"],
         exp=[("OpenClaw · 组员", "写数据清洗脚本，统一各组工具的输入格式。")],
         works=["w1"], joined="2025 年秋季",
         qa=[("为什么选象罔", "因为这里能拿到真实的脏数据，课本上的数据集太干净了。")]),
    dict(id="zhuyuanmei", name="朱芫枚", post="成员", tier="成员", college="计算机/软件学院", major="软件工程", hue=5,
         dir=["前端", "Vue"],
         quote="一个按钮的位置改八遍，不是强迫症，是有人真的会因此少点错一次。",
         bio="前端方向，负责社团多个项目的 UI 实现与组件库维护。",
         skills=["Vue3", "TypeScript", "CSS", "Figma"],
         exp=[("Hermes · 组员", "负责控制台界面与状态可视化。"),
              ("社团组件库", "搭了一套自用组件库，省得每个项目重写一遍按钮。")],
         works=["w5"], joined="2025 年秋季",
         qa=[("最近在折腾什么", "在给社团搭一套自己的组件库，省得每个项目都重写一遍按钮。")]),
    dict(id="chenjiamin", name="陈佳敏", post="成员", tier="成员", college="计算机学院", major="计算机科学与技术", hue=2,
         dir=["算法", "竞赛"],
         quote="题解看懂了不算会，能在白板上写出来才算。",
         bio="算法竞赛方向，负责社团每周算法小讲堂。",
         skills=["C++", "数据结构", "动态规划", "图论"],
         exp=[("OpenClaw · 组员", "负责工具调用的边界用例与单元测试。"),
              ("算法小讲堂", "每周讲一次，从最短路讲到网络流。")],
         works=["w1"], joined="2025 年秋季",
         qa=[("每周讲什么", "从最短路讲到网络流，每次留一道作业，下周一开讲前对答案。")]),
    dict(id="chenzhiming", name="陈致明", post="成员", tier="成员", college="人工智能学院", major="人工智能", hue=3,
         dir=["Python", "机器学习"],
         quote="模型跑出 95% 准确率的时候，我第一反应是：是不是数据漏了。",
         bio="机器学习方向，负责 Hermes 的记忆压缩与要点提炼。",
         skills=["PyTorch", "Python", "机器学习", "数学基础"],
         exp=[("Hermes · 组员", "做要点提炼的评测，对比几种压缩策略的召回损失。")],
         works=["w5"], joined="2025 年秋季",
         qa=[("踩过最大的坑", "训练集和测试集没分开，高兴了整整一天才发现。")]),
    dict(id="yusiyu", name="余思雨", post="成员", tier="成员", college="艺术学院", major="数字媒体艺术", hue=4,
         dir=["UI 设计", "创意编程"],
         quote="技术是骨架，审美是皮肤——只有骨架的东西没人愿意摸第二次。",
         bio="设计 + 创意编程，社团所有海报和官网视觉都出自她手。",
         skills=["Figma", "视觉设计", "p5.js", "动效"],
         exp=[("社团视觉", "招新海报改了五版，对外物料统一从这里出。")],
         works=[], joined="2025 年秋季",
         qa=[("设计之外", "也在学 shader，想把官网首页做成真正能玩的东西。")]),
    dict(id="hehongquan", name="何泓全", post="成员", tier="成员", college="网络空间安全学院", major="网络空间安全", hue=1,
         dir=["CTF", "逆向"],
         quote="逆向就是把别人的故事倒着读一遍。",
         bio="二进制与逆向方向，社团 Writeup 合集的主要贡献者。",
         skills=["逆向工程", "汇编", "Pwn", "Python"],
         exp=[("OpenClaw · 组员", "负责沙盒权限收口与异常输入处理。")],
         works=["w1"], joined="2025 年秋季",
         qa=[("入门建议", "先啃一本《汇编语言》，再刷 50 道 crackme，熬过去就好了。")]),
    dict(id="dingbo", name="丁博", post="成员", tier="成员", college="自动化学院", major="测控技术与仪器", hue=4,
         dir=["嵌入式", "物联网"],
         quote="让设备连上网的那一刻，它才真正开始工作。",
         bio="物联网方向，想把实验室的传感器数据接到社团的平台上。",
         skills=["C", "单片机", "MQTT", "Python"],
         exp=[("DeepseekHarness · 组员", "做执行环境的容器化与资源隔离。")],
         works=["w4"], joined="2026 年春季",
         qa=[("最近在做", "一个温湿度采集节点，数据打算接到社团的公开数据接口上。")]),
    dict(id="zhanghongcheng", name="张洪铖", post="成员", tier="成员", college="计算机与软件学院", major="软件工程", hue=1,
         dir=["前端", "React"],
         quote="动画不是为了炫，是为了让用户知道“刚才发生了什么”。",
         bio="前端方向，React + 动效，官网 v3 的主要开发。",
         skills=["React", "TypeScript", "CSS 动效", "Canvas"],
         exp=[("DeepseekHarness · 组员", "把 trace 日志做成可回看的界面。"),
              ("社团官网 v3", "主导前端动效与 38 个页面的详情页模板。")],
         works=["w4"], joined="2025 年秋季",
         qa=[("这次官网做了什么", "深色科技风 + 粒子网络和悬停光束，每个项目都有独立详情页了。")]),

]

ACTIVITIES = [
    dict(id="a1", date="2026.09.14", weekday="星期一", title="各组进度汇报会：做了什么、卡在哪、下周做什么",
         tags=["组会", "进度汇报", "秋季学期"], em="📊", cv="cv1",
         summary="本学期第一次正式进度汇报，五个组轮流上台，每组 8 分钟，只讲三件事：做完了什么、卡在什么地方、下周打算做什么。",
         body=["周一晚 19:00，工科楼 A-302，本学期第一次全员进度汇报会。社长把规则定得很死：每组 8 分钟，不许念稿，代码和截图直接投屏，讲完当场演示。",
               "AI 组最先交卷：RAG 检索链路已经能跑通“提问—召回—带出处回答”，卡点是召回回来的段落经常被截断；后端组把工具注册接口合并进了 OpenClaw 底座，但幂等兜底还没补测试；前端组的详情页骨架搭完了，正等着真实照片替换占位图；项目组把新手任务重出了一遍。",
               "汇报里被提到最多的一个词是“卡在哪”。社长要求每个卡点都必须写清“试过什么、为什么没成”，方便下一个接手的人不用从头踩一遍。散会前他在黑板上留下一句话：下周汇报，必须能当场跑起来，不接受只讲计划。"],
         photos=[("📊", "五组进度表 · A-302", "cv1"), ("🖥️", "当场演示环节", "cv2"), ("📌", "黑板上的下周待办", "cv3")],
         participants=["yangtianlong", "sunjiale", "chenmingrui", "yuyue", "caiquanyou", "zhengzixin", "zhuyuanmei", "caitong", "chenjiamin", "chenzhiming", "yusiyu", "raoyuxuan", "hehongquan", "qinziyuan", "caikai", "dingbo", "zhanghongcheng", "guoshijun"]),
    dict(id="a2", date="2026.09.07", weekday="星期一", title="各组自行开会：把学期目标拆成一周能做完的小块",
         tags=["小组会", "分工", "异步协作"], em="🧭", cv="cv2",
         summary="这一周不开全员大会，五个组自己找时间碰——图书馆讨论区、实验室、线上会议室，各开各的。",
         body=["开学第一周没有全员会，社长在群里只发了一句话：各组自己找时间碰一下，别等到第二周才开始。于是五个组在图书馆讨论区、实验室和线上会议室各开各的。",
               "AI 组把剩下的任务切成三块——向量库建库、召回评测、论文复现，每人认领一块并写下交付标准；后端组先在白板上把调用链路画清楚才动手写代码，避免了先写后改；前端组把页面拆成组件清单，谁做哪块一目了然；项目组把新手任务重写了一遍，删掉了那些“跟着教程做也能过”的题目。",
               "小组会的好处是没人端着，卡住的问题当场就能问到旁边的人。所有组的会议记录统一放回资料库的同一个目录，按“日期 + 组名”命名，错过了的人自己补一遍就能跟上。"],
         photos=[("🧭", "各组分工白板", "cv2"), ("📝", "会议记录归档", "cv4"), ("💬", "线上小组会", "cv5")],
         participants=["yangtianlong", "sunjiale", "yuyue", "zhuyuanmei", "raoyuxuan", "zhanghongcheng", "qinziyuan", "caitong", "hehongquan", "chenjiamin", "caiquanyou"]),
    dict(id="a3", date="2026.08.16", weekday="星期日", title="暑期论文研读会：从读得懂，到能对着白板讲出来",
         tags=["论文", "研读", "暑期"], em="📑", cv="cv3",
         summary="每周日晚一次的线上研读，这期精读 RAG 与向量检索的两篇经典工作，读完要能讲清“解决了什么问题、怎么解决的、我们哪块能用”。",
         body=["暑期的论文研读固定在每周日晚线上进行，规矩是主讲人提前三天把论文和自己的批注发到群里，会上只讲三件事：这篇论文要解决什么问题、用了什么办法、我们哪一块能用上。",
               "这期精读的是检索增强生成与向量检索的两篇经典工作。最有价值的一段讨论来自一个很具体的问题——“为什么明明召回对了，答案还是错的”。大家在白板上把召回、重排、生成三段拆开逐段验证，最后发现瓶颈不在模型，而在切分策略把一句完整的话切成了两半。",
               "会后直接产出了一份切分与重排的实验清单，成了 AI 组接下来两周的待办。研读笔记统一按“问题—方法—结论—能不能用”四栏整理，归档进资料库，后来新同学入门基本都是先从这几份笔记读起。"],
         photos=[("📑", "本期精读的两篇论文", "cv3"), ("🧑‍🏫", "白板推导现场", "cv1"), ("🗂️", "四栏研读笔记", "cv5")],
         participants=["sunjiale", "qinziyuan", "yuyue", "caitong", "hehongquan", "chenjiamin", "yangtianlong", "dingbo"]),
    dict(id="a4", date="2026.08.02", weekday="星期日", title="智能体小组中期检查：三个方向，各跑通一条完整链路",
         tags=["智能体", "中期检查", "暑期"], em="🤖", cv="cv4",
         summary="暑期过半，各智能体方向集中演示，要求不是“讲思路”，而是当场从输入跑到输出；跑不通的当场决定砍掉或降级。",
         body=["暑期过半做了一次中期检查，三个智能体方向各给 15 分钟，唯一的要求是当场演示从输入到输出的完整链路，不接受只讲设计。",
               "教育智能体演示了从导入课件到带出处答疑的全过程，老师最关心的“这句话从哪来”终于能点开看；科研智能体跑通了从文献检索到生成研究提纲的一段；硬件方向的采集节点第一次把真实传感器数据写进了公开接口。另一个跑不通的方向，当场决定降级为技术预研，不再占用人手。",
               "社长给出的判断标准只有两条：有没有真实数据、有没有端到端跑通。他说，演示能跑通一半，比讲十页 PPT 有用——这也成了后面每次检查的固定口径。"],
         photos=[("🤖", "三个方向轮流演示", "cv4"), ("🔗", "端到端链路图", "cv2"), ("📡", "采集节点首条真实数据", "cv5")],
         participants=["yangtianlong", "sunjiale", "yuyue", "zhuyuanmei", "raoyuxuan", "caitong", "zhengzixin", "qinziyuan", "zhanghongcheng"]),
    dict(id="a5", date="2026.07.26", weekday="星期日", title="向量数据库专项：先把它装起来，再想办法查得准",
         tags=["向量数据库", "技术专项", "暑期"], em="🗄️", cv="cv5",
         summary="集中一天把向量库的选型、建库和评测跑顺，最大的收获是发现“查得到”和“查得准”必须分开测。",
         body=["暑期学习任务推进到第二周，技术部组织了一次向量数据库专项：上午做选型对比，下午各自把自己那部分数据灌进去，晚上一起写评测脚本。",
               "最反直觉的收获是：召回率提上去了，答案质量却没什么变化。把评测拆成“查得到”（召回）和“查得准”（排序）两个指标分开测之后才看清，问题出在切分粒度，而不是模型能力。",
               "当天沉淀下一份建库 checklist：数据清洗、切分策略、向量模型选择、索引参数、评测集。之后新同学接手，照着这份清单走一遍就能把库跑起来，不用再从头问一遍。"],
         photos=[("🗄️", "建库流水线", "cv5"), ("📐", "召回 / 排序双指标", "cv1"), ("✅", "建库 checklist", "cv3")],
         participants=["sunjiale", "qinziyuan", "caitong", "hehongquan", "caikai", "dingbo", "yuyue"]),
    dict(id="a6", date="2026.07.11", weekday="星期六", title="暑期学习任务启动：RAG、向量数据库与各智能体全面铺开",
         tags=["暑期", "学习任务", "RAG", "启动"], em="🚩", cv="cv2",
         summary="社长在群里发出暑期学习任务清单，定下三条主线——RAG 检索、向量数据库、各智能体方向，明确负责人、节点和检查方式。",
         body=["7 月 11 日晚，社长在群里发出一份暑期学习任务清单，暑期计划正式启动。三条主线同时铺开：RAG 检索链路、向量数据库实践，以及已有的各智能体方向继续往前推。",
               "任务不是“自己找本书看”，每条主线都有必须交出来的东西：RAG 要能跑通一次带出处的问答，向量库要有建库脚本和一套评测集，智能体要有一个能端到端演示的真实场景。负责人、时间节点、检查方式一次写清，避免假期开头热三天就没了下文。",
               "为了不让人掉队，同时定下三条规矩：每周各组自行碰一次，每周日晚线上研读一次论文，开学第二周做一次全员进度汇报。暑期结束时，三条主线都拿出了自己的第一版产物——这也是 9 月 14 日那场汇报会的来处。"],
         photos=[("🚩", "暑期任务清单", "cv2"), ("🧾", "三条主线分工", "cv4"), ("🗓️", "每周节奏安排", "cv1")],
         participants=["yangtianlong", "sunjiale", "yuyue", "zhuyuanmei", "raoyuxuan", "zhanghongcheng", "qinziyuan", "caitong", "hehongquan", "chenjiamin", "caiquanyou", "zhengzixin", "yusiyu", "caikai", "dingbo", "chenmingrui", "guoshijun"]),
]
JOBS = [
    dict(id="j1", title="前端开发方向", org="前端组 · 校内", status="open", status_text="报名中",
         intro="参与真实产品的前端迭代开发，与设计师、后端工程师协作联调，写的组件会被成千上万的用户用到。",
         duty=["参与真实产品的前端迭代开发", "与设计师、后端工程师协作联调", "编写可复用、可维护的组件"],
         reqs=["熟悉 HTML / CSS / JavaScript 基础", "了解 Vue 或 React 任一框架", "大二大三优先，每周能投入 3 天以上时间（占位）"],
         plus=["有自己完整做过并上线的项目", "了解 TypeScript", "对动效 / 交互细节有追求"],
         mentor="zhanghongcheng", team="前端组"),
    dict(id="j2", title="后端开发方向", org="后端组 · 校内", status="open", status_text="报名中",
         intro="参与服务端接口设计与开发，优化数据库查询与接口性能，参与代码评审与技术分享。",
         duty=["参与服务端接口设计与开发", "优化数据库查询与接口性能", "参与代码评审与技术分享"],
         reqs=["熟悉 Java 或 Go 任一语言", "了解 MySQL / Redis 常用操作", "有社团项目经验者优先"],
         plus=["写过单元测试", "用过 Docker 部署过自己的项目", "读过至少一个开源项目的源码"],
         mentor="raoyuxuan", team="后端组"),
    dict(id="j3", title="算法方向（AI）", org="AI 组 · 校内", status="soon", status_text="即将开放",
         intro="参与机器学习 / 大模型应用研发，复现论文并做工程化落地，搭建与维护实验评测流程。",
         duty=["参与机器学习 / 大模型应用研发", "复现论文并做工程化落地", "搭建与维护实验评测流程"],
         reqs=["Python 熟练，了解 PyTorch", "读过至少一个经典模型/论文", "对 LLM 应用方向有兴趣"],
         plus=["有 RAG / 向量检索实践经验", "会用 W&B 或 MLflow 管理实验", "在 Kaggle 等平台有参赛经历"],
         mentor="qinziyuan", team="AI 组"),
    dict(id="j4", title="社团项目组 · 核心开发", org="校内 · 社团自研项目", status="open", status_text="长期招募",
         intro="参与官网、小程序等自研项目开发，带教新成员完成新手任务，优秀者可获合作企业内推。",
         duty=["参与官网、小程序等自研项目开发", "带教新成员完成新手任务", "优秀者可获合作企业内推"],
         reqs=["社团正式成员", "每周可投入 4 小时以上", "有责任心，能坚持交付"],
         plus=["能至少坚持一个完整学期", "愿意写文档，而不只是写代码", "愿意在组会上讲自己踩过的坑"],
         mentor="yuyue", team="项目组"),
]

TECH = ["TypeScript", "Vue 3", "React", "Node.js", "Go", "Python", "PyTorch", "LLM / RAG",
        "Docker", "MySQL", "Redis", "Nginx", "Canvas", "WebGL", "Git", "Linux", "Figma", "ECharts"]

LIFE_ROWS = ["从需求评审到上线运维", "走完整一遍生产流程", "18 位成员 · 7 个学院", "每周五 19:00 固定组会",
             "自研项目全部开源", "写文档也算交付物", "工科楼 A-302", "2026 秋季招新进行中"]
life_phrases = LIFE_ROWS

BENTO = [
    dict(ic="🌐", t="Web 全栈", d="从需求评审到上线运维，完整走一遍生产流程，而不是停在 demo。", cls="w2", no="01"),
    dict(ic="🤖", t="人工智能", d="LLM 应用、RAG 检索、模型工程化落地。", cls="", no="02"),
    dict(ic="🦾", t="Agent 工程", d="模型调用、工具注册、沙盒执行，把重复的部分抽成底座。", cls="", no="03"),
    dict(ic="🔬", t="科研全流程", d="想法到可投稿论文，六阶段每步都要留下能被检查的产物。", cls="", no="04"),
    dict(ic="🧩", t="开源实践", d="所有自研项目均开源，PR 与 Code Review 全流程实战。", cls="w2", no="05"),
    dict(ic="🎨", t="设计与前端", d="设计与工程一起做决定，拒绝“设计师画图开发照抄”。", cls="", no="06"),
]

STATS = [("120", "+", "在册成员"), ("30", "+", "完成项目"), ("15", "", "竞赛奖项"), ("98", "%", "就业 / 升学")]

PROCESS = [("09.15 - 09.30", "线上报名", "扫码或通过页面底部 QQ 群提交报名表"),
           ("10.01 - 10.10", "宣讲会 & 面谈", "聊聊你想做什么，而不是你考了多少分（占位）"),
           ("10.11 - 10.20", "新手任务", "一个小作业，看的是热情和潜力，不是现在的水平"),
           ("10.25", "公布名单", "欢迎仪式 & 首次组会，正式加入")]

CONTACT = [("💬", "招新 QQ 群", "123-456-789（占位）"),
           ("📮", "合作邮箱", "xiangwang@club.edu.cn（占位）"),
           ("📍", "活动室", "工科楼 A-302（占位）"),
           ("🐙", "GitHub", "github.com/xiangwang-club（占位）")]

# ============================================================
# 工具函数
# ============================================================
def esc(s):
    return html.escape(str(s), quote=True)

def m(id_):
    for x in MEMBERS:
        if x["id"] == id_:
            return x
    return None

def w(id_):
    for x in WORKS:
        if x["id"] == id_:
            return x
    return None

def member_url(id_):
    return "member-%s.html" % id_

def work_url(id_):
    return "work-%s.html" % id_

def life_url(id_):
    return "life-%s.html" % id_

def job_url(id_):
    return "job-%s.html" % id_

TIER_ORDER = ['社团负责人', '技术部', '职能部门', '成员']
TIER_DESC = {'社团负责人': '定方向、管对外、把技术路线落到验收标准', '技术部': '四大组长各带一组，拆任务、跑代码、沉淀文档', '职能部门': '立项排期与对外视觉，让项目能持续推进、成果看得出去', '成员': '在各项目里按「队长 / 组员」的角色参与开发'}

TIER_STYLE = {
    "社团负责人": "color:#04070f;background:linear-gradient(135deg,#35e6ff,#8b5cf6);padding:2px 10px;border-radius:999px;font-weight:700",
    "技术部":     "color:var(--cy);border:1px solid rgba(53,230,255,.38);padding:2px 10px;border-radius:999px;font-weight:600",
    "职能部门":   "color:var(--vi);border:1px solid rgba(139,92,246,.38);padding:2px 10px;border-radius:999px;font-weight:600",
    "成员":       "color:var(--dim-2)",
}

def post_chip(x):
    return f'<span class="mpost" style="{TIER_STYLE[x["tier"]]}">{esc(x["post"])}</span>'

def initial(name):
    return name[0]

# ---- 项目分工：队长 / 组员（与社团职位相互独立）-------------------------
def lead_of(x):
    """作品队长。没配 lead 时默认取 contributors 第一个。"""
    return x.get("lead") or (x["contributors"][0] if x.get("contributors") else None)

def team_order(x):
    """成员排序：队长第一，其余保持原顺序。"""
    ld = lead_of(x)
    rest = [c for c in x.get("contributors", []) if c != ld]
    return ([ld] if ld else []) + rest

def role_of(x, cid):
    """某人在某作品里的角色。"""
    return "队长" if cid == lead_of(x) else "组员"

ROLE_STYLE = {
    "队长": "display:inline-block;margin-left:8px;padding:1px 8px;border-radius:999px;"
            "background:linear-gradient(135deg,#35e6ff,#8b5cf6);color:#05070e;"
            "font-size:11.5px;font-weight:700;line-height:1.7;vertical-align:middle;letter-spacing:.02em",
    "组员": "display:inline-block;margin-left:8px;padding:1px 8px;border-radius:999px;"
            "background:rgba(255,255,255,.10);color:var(--dim);border:1px solid rgba(255,255,255,.16);"
            "font-size:11.5px;font-weight:600;line-height:1.7;vertical-align:middle;letter-spacing:.02em",
}

def role_badge(role):
    return '<span style="%s">%s</span>' % (ROLE_STYLE[role], role)
# -----------------------------------------------------------------------

def av(hue):
    return "av-%d" % ((hue - 1) % 5 + 1)

def avatar(mem, cls="av", size=None):
    style = ' style="width:%spx;height:%spx;font-size:%spx"' % (size, size, int(size) * 0.36) if size else ""
    return '<span class="%s %s"%s>%s</span>' % (cls, av(mem["hue"]), style, esc(initial(mem["name"])))

def split_chars(text):
    """把中文标题拆成逐字 span（| 换行）"""
    out, i = [], 0
    for line in text.split("|"):
        for ch in line:
            out.append('<span class="w" style="--i:%d">%s</span>' % (i, esc(ch)))
            i += 1
        out.append("<br>")
    out.pop()
    return "".join(out)

# ============================================================
# 页面骨架
# ============================================================
def head(title, desc=None, active="", gated=None):
    gated = SITE_GATE if gated is None else gated
    return f"""<!DOCTYPE html>
<html lang="zh-CN"{' class="gated"' if gated else ''}>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc or SITE['desc'])}">
<link rel="icon" type="image/png" href="assets/logo.png">
<link rel="stylesheet" href="assets/site.css">
<link rel="stylesheet" href="assets/auth.css">
<style>.sk-wrap{{display:flex;flex-wrap:wrap;gap:0}}
.sk-chip{{display:inline-block;margin:0 8px 8px 0;padding:4px 13px;border-radius:999px;background:rgba(53,230,255,.10);border:1px solid rgba(53,230,255,.30);color:#e8f6ff;font-size:14px;font-weight:600;line-height:1.7}}
.exp-list{{list-style:none;padding:0;margin:0}}
.exp-list li{{padding:13px 0;border-bottom:1px dashed rgba(255,255,255,.10)}}
.exp-list li:last-child{{border-bottom:none;padding-bottom:4px}}
.exp-list b{{display:block;font-size:15px;color:#fff;font-weight:600;margin-bottom:5px}}
.exp-list span{{font-size:14px;color:var(--dim);line-height:1.8;display:block}}
.cv6{{background:linear-gradient(135deg,#38bdf8,#0f766e)}}</style>
<noscript><style>html.gated body{{opacity:1}}</style></noscript>
<script src="assets/auth.js"></script>
</head>
<body>
<div id="prog"></div>
<div class="bg-layers"><span class="blob b1"></span><span class="blob b2"></span><span class="blob b3"></span><span class="grid"></span></div>
<nav>
  <div class="nav-in">
    <a class="logo" href="index.html"><span class="seal">象</span><span class="logo-txt"><b>象罔社团</b><small>{esc(SITE['slogan'])}</small></span></a>
    <ul class="nav-links">
      <li><a href="index.html#about">我们是谁</a></li>
      <li><a href="life.html">社团动态</a></li>
      <li><a href="members.html">成员</a></li>
      <li><a href="projects.html">作品</a></li>
      <li><a href="index.html#recruit">招新</a></li>
      <li><a href="index.html#contact">联系</a></li>
      <li><a href="area.html">成员专区</a></li>
    </ul>
    <div class="nav-right">
      <span class="nav-status"><i></i>2026 秋招进行中</span>
      <div class="nav-auth" id="navAuth"></div>
      <a class="nav-cta" href="index.html#recruit">加入我们 <i>→</i></a>
      <button class="burger" aria-label="菜单">☰</button>
    </div>
  </div>
</nav>
<main>
"""

def foot():
    return """
</main>
<footer>
  <div class="foot-in">
    <span class="motto">// 象罔得之 —— 无心而求，反而得之</span>
    <span class="foot-links">
      <a href="index.html">首页</a>
      <a href="projects.html">作品</a>
      <a href="members.html">成员</a>
      <a href="life.html">动态</a>
      <a href="index.html#recruit">招新</a>
    </span>
    <span>© 2026 象罔社团 · 内容占位，上线前替换</span>
  </div>
</footer>
<button id="top-btn" aria-label="回到顶部">↑</button>
<script src="assets/site.js"></script>
</body>
</html>
"""

def kicker(t):
    return '<p class="kicker">%s</p>' % esc(t)

def sec_head(k, h, p=None, num=None):
    return f"""<div class="sec-head rv">
      {('<span class="sec-num">' + esc(num) + '</span>') if num else ''}
      {kicker(k)}
      <h2>{h}</h2>
      {'<p>%s</p>' % esc(p) if p else ''}
    </div>"""

def beam_start(extra=""):
    return f'<div class="beam {extra}"><div class="beam-in">'

def beam_end():
    return "</div></div>"

# ============================================================
# 首页
# ============================================================
def build_index():
    p = [head("象罔社团 · 知索不得，象罔得之")]

    # Hero
    term_lines = [
        ('<span class="c">$</span> <span class="k">club</span> status', ""),
        ('  <span class="s">✓</span> 在册成员 <span class="v">120</span> · 在研项目 <span class="v">6</span>', ""),
        ('  <span class="s">✓</span> 本周组会 <span class="v">周五 19:00</span> @ A-302', ""),
        ('  <span class="s">✓</span> 招新状态 <span class="v">进行中</span> · 报名至 09.30', ""),
        ('<span class="c">$</span> <span class="k">ls</span> projects/', ""),
        ('  OpenClaw/       教育智能体/', ""),
        ('  专利智能体/     DeepseekHarness/', ""),
        ('  Hermes/        科研智能体/', ""),
        ('<span class="c">$</span> <span class="k">next</span> --events 2', ""),
        ('  &gt; 09.19 19:00 迎新分享会「如何读源码」', ""),
        ('  &gt; 09.26 19:00 算法小讲堂「最短路」', ""),
        ('<span class="c">$</span> <span class="k">join</span> --now  <span class="s">_</span>', ""),
    ]
    tl = "".join('<div class="ln">%s</div>' % a for a, _ in term_lines)

    stats = "".join(
        f'<div class="hstat"><b><span data-count="{v}">0</span>{s}</b><span>{esc(l)}</span></div>'
        for v, s, l in STATS)

    p.append(f"""
<header class="hero" id="top">
  <div class="wrap hero-grid">
    <div class="hero-left">
      <span class="pill"><i class="dot-live"></i> 2026 秋季招新 · 进行中</span>
      <h1>{split_chars('知索不得，|象罔得之。')}</h1>
      <p class="hero-sub">在象罔，从第一个页面、接口或模型开始，把想法做成能真正运行的项目。</p>
      <div class="btn-row">
        <a class="btn btn-p" href="#recruit">我想加入 →</a>
        <a class="btn btn-g" href="projects.html">看看我们做过什么</a>
      </div>
      <div class="hero-stats rv">{stats}</div>
    </div>
    <div class="hero-side" aria-label="交互终端">
      <div class="cliterm" data-term>
        <div class="clit-top">
          <span class="clit-dots"><i></i><i></i><i></i></span>
          <span class="clit-title">xiangwang@club ~/site</span>
        </div>
        <div class="clit-body" data-term-out></div>
        <div class="clit-in">
          <span class="clit-prompt">$</span>
          <input data-term-in autocomplete="off" spellcheck="false" autocapitalize="off"
                 placeholder="输入 help 然后回车 ↵"/>
        </div>
      </div>
    </div>
  </div>
</header>
""")

    # 作品（先展示真实交付，作为技术能力的证据）
    cards = "".join(f"""
      <a class="beam tilt rv" href="{work_url(x['id'])}" data-cat="{esc(x['cat'])}"><div class="beam-in wk spot">
        <div class="cover {x['cv']}"><span class="st">{esc(x['status'])}</span><span class="em">{x['em']}</span></div>
        <div class="body">
          <span class="cat">{esc(x['cat'])}</span>
          <h3>{esc(x['title'])}</h3>
          <p>{esc(x['desc'][:58])}…</p>
          <div class="stack">{''.join(f'<span>{esc(s)}</span>' for s in x['stack'][:4])}</div>
          <span class="more">查看项目详情 <span>→</span></span>
        </div>
      </div></a>""" for x in WORKS)
    p.append(f"""
<section id="works">
  <div class="wrap">
    {sec_head("PORTFOLIO · 作品背后是人", "先看我们真正做过什么", "不讲技术栈罗列，讲谁做的、踩了什么坑、现在什么状态。每一个项目都有独立详情页。", "01")}
    <div class="work-grid">{cards}</div>
    <div style="text-align:center;margin-top:34px"><a class="btn btn-g" href="projects.html">查看全部作品 →</a></div>
  </div>
</section>
""")

    # 方向（Bento）
    bento_parts = []
    for b in BENTO:
        bento_parts.append('<div class="bt %s rv"><span class="ic">%s</span><h3>%s</h3><p>%s</p><span class="no">%s</span></div>'
                           % (b["cls"], b["ic"], esc(b["t"]), esc(b["d"]), b["no"]))
    bento = "".join(bento_parts)
    p.append(f"""
<section id="about">
  <div class="wrap">
    <div class="sec-head rv">
      <span class="sec-num">02</span>
      {kicker("WHAT WE DO · 我们是谁")}
      <h2>我们的方向</h2><p>象罔，出自《庄子·天地》，借这个名字提醒自己——最好的东西往往不是刷题刷出来的，是在动手折腾的过程中撞见的。</p>
    </div>
    <div class="bento">{bento}</div>
    <p class="rv" style="margin-top:26px;font-family:var(--mono);font-size:14.5px;color:var(--dim-2)">
      // 方向持续扩充中，也欢迎你带来一个全新的方向</p>
  </div>
</section>
""")

    # 成长路径
    growth_steps = [
        ("第 1 周", "跑通一脚，熟悉仓库、工具和协作方式。"),
        ("第 2–4 周", "领一个边界清楚的小任务，改第一行真实代码并提交。"),
        ("第 1 个月", "参与一次评审或上线，看见自己的代码被别人用到。"),
        ("第 1 个学期", "参与一个完整项目；之后可负责模块、带新人或参赛。"),
    ]
    gsteps = "".join(f'<li><p class="t">{esc(t)}</p><p class="d">{esc(d)}</p></li>' for t, d in growth_steps)
    p.append(f"""
<section id="growth">
  <div class="wrap">
    {sec_head("GROWTH PATH · 加入之后", "你会怎样一步步做出东西", "我们不看你现在会多少，看你想不想做点东西。加入后有明确的成长路线，而不是自生自灭。", "03")}
    <ol class="steps rv">{gsteps}</ol>
    <div style="text-align:center;margin-top:12px"><a class="btn btn-p" href="#recruit">我准备好了，看看怎么加入 →</a></div>
  </div>
</section>
""")

    # 成员
    qs = [m("chenmingrui"), m("yuyue"), m("yusiyu")]
    quotes = "".join(f"""
      <div class="beam tilt rv"><div class="beam-in spot qc">
        <span class="qm">"</span>
        <p>{esc(x['quote'])}</p>
        <a class="who" href="{member_url(x['id'])}">{avatar(x, 'av-sm', 38)}<span><b>{esc(x['name'])}</b><span>{esc(x['college'])} · {esc(x['major'])} · {esc(x['id'])}</span></span></a>
      </div></div>""" for x in qs)
    roster = "".join(f"""
      <a class="beam tilt rv" href="{member_url(x['id'])}"><div class="beam-in mem spot">
        {avatar(x, 'av', 62)}<b>{esc(x['name'])}</b>
        <span class="mj">{esc(x['major'])}</span>
        {post_chip(x)}
      </div></a>""" for x in MEMBERS[:8])
    p.append(f"""
<section id="members" style="padding-top:20px">
  <div class="wrap">
    {sec_head("MEMBERS · 先听听他们说", "成员，18 种来这儿的理由", "隐私说明：本页仅展示姓名·学院·专业·职位，其他个人信息一律不上网。", "04")}
    <div class="quote-grid">{quotes}</div>
    <div class="mem-grid" style="margin-bottom:34px">{roster}</div>
    <div style="text-align:center"><a class="btn btn-g" href="members.html">查看全部成员 →</a></div>
  </div>
</section>
""")

    # 招新
    steps = "".join(f'<li><p class="t">{esc(t)}</p><p class="h">{esc(h)}</p><p class="d">{esc(d)}</p></li>' for t, h, d in PROCESS)
    jobs = "".join(f"""
      <div class="beam tilt rv"><div class="beam-in job spot">
        <div class="top"><div><h3>{esc(j['title'])}</h3><p class="org">{esc(j['org'])}</p></div>
          <span class="badge {'b-open' if j['status']=='open' else 'b-soon'}">{'● ' if j['status']=='open' else '○ '}{esc(j['status_text'])}</span></div>
        <p style="font-size:14px;color:var(--dim);line-height:1.75">{esc(j['intro'][:52])}…</p>
        <ul>{''.join(f'<li>{esc(r)}</li>' for r in j['reqs'][:2])}</ul>
        <a class="more" style="font-family:var(--mono);font-size:14px;color:var(--cy)" href="{job_url(j['id'])}">查看岗位详情 →</a>
      </div></div>""" for j in JOBS)
    p.append(f"""
<section id="recruit" style="padding-top:20px">
  <div class="wrap">
    {sec_head("JOIN US · 2026 秋季招新", '招新进行中 <span style="color:var(--cy)">●</span>', "面向全校，不限专业、不限年级。", "05")}
    <div class="bento" style="grid-template-columns:1fr 1fr;grid-auto-rows:auto;margin-bottom:40px">
      <div class="bt rv"><span class="ic">🎯</span><h3>报名要求</h3>
        <ul style="margin-top:10px">{''.join(f'<li style="font-size:14px;color:var(--dim);padding:5px 0">{esc(x)}</li>' for x in ["零基础可入——只要肯学，学长学姐从头带","不限专业——技术面前人人平等","每周至少 4 小时——投入才有产出","一台自己的电脑——配置不限，热爱不限"])}</ul></div>
      <div class="bt rv"><span class="ic">🎁</span><h3>你将获得</h3>
        <ul style="margin-top:10px">{''.join(f'<li style="font-size:14px;color:var(--dim);padding:5px 0">{esc(x)}</li>' for x in ["真实项目经验——简历不再空白","一路同行的伙伴——和靠谱的人一起做事","内推机会——毕业直通合作企业","开源主页——你的代码会被别人用到"])}</ul></div>
    </div>
    <div class="job-grid">{jobs}</div>
    <h2 style="margin:54px 0 6px;font-size:22px">招新时间线</h2>
    <ol class="steps rv">{steps}</ol>
    <div style="text-align:center;margin-top:30px"><a class="btn btn-p" href="#contact">报名 / 联系我们 →</a></div>
  </div>
</section>
""")

    # 动态
    items = "".join(f"""
      <div class="tl-item rv">
        <a class="tl-card spot" href="{life_url(a['id'])}">
          <span class="d">{esc(a['date'])} · {esc(a['weekday'])}</span>
          <h3>{esc(a['title'])}</h3>
          <p>{esc(a['summary'])}</p>
          <span class="go">查看详情 <span>→</span></span>
        </a>
      </div>""" for a in ACTIVITIES[:4])
    p.append(f"""
<section id="life" style="padding-top:20px">
  <div class="wrap">
    {sec_head("CLUB LIFE · 最近在干嘛", "社团不是一排链接，是每周都在发生的事", "每条动态都有独立详情页：现场照片、完整复盘、到场的人。", "06")}
    <div class="tl">{items}</div>
    <div style="text-align:center;margin-top:34px"><a class="btn btn-g" href="life.html">查看全部动态 →</a></div>
  </div>
</section>
""")

    # 联系
    cc = "".join(f'<div class="cc rv"><div class="ic">{e}</div><b>{esc(t)}</b><span>{esc(v)}</span></div>' for e, t, v in CONTACT)
    p.append(f"""
<section id="contact" style="padding-top:20px">
  <div class="wrap">
    {sec_head("CONTACT · 找到我们", "随时来活动室坐坐", None, "07")}
    <div class="contact-grid">{cc}</div>
  </div>
</section>
""")

    p.append(foot())
    return "".join(p)

# ============================================================
# 列表页
# ============================================================
def build_projects():
    p = [head("作品 · 象罔社团")]
    cats = ["全部"] + sorted({x["cat"] for x in WORKS})
    btns = "".join(f'<button class="{"on" if i==0 else ""}" data-f="{"all" if i==0 else esc(c)}">{esc(c)}</button>'
                   for i, c in enumerate(cats))
    cards = "".join(f"""
      <a class="beam tilt rv" href="{work_url(x['id'])}" data-cat="{esc(x['cat'])}"><div class="beam-in wk spot">
        <div class="cover {x['cv']}"><span class="st">{esc(x['status'])}</span><span class="em">{x['em']}</span></div>
        <div class="body">
          <span class="cat">{esc(x['cat'])}</span>
          <h3>{esc(x['title'])}</h3>
          <p>{esc(x['desc'])}</p>
          <div class="stack">{''.join(f'<span>{esc(s)}</span>' for s in x['stack'])}</div>
          <p style="font-size:13.5px;color:var(--dim);margin:12px 0 0">队长 <b style="color:#fff">{esc(m(lead_of(x))['name']) if m(lead_of(x)) else '—'}</b> · {len(x['contributors'])} 人参与</p>
          <span class="more">查看项目详情 <span>→</span></span>
        </div>
      </div></a>""" for x in WORKS)
    p.append(f"""
<section style="padding-top:60px">
  <div class="wrap">
    {sec_head("PORTFOLIO", '全部作品 <span class="grad">%d 个</span>' % len(WORKS), "每个项目都有独立详情页：完整故事、时间线、参与成员、技术栈与成果数据。")}
    <div class="filters">{btns}</div>
    <div class="work-grid">{cards}</div>
  </div>
</section>
""")
    p.append(foot())
    return "".join(p)

def build_members():
    p = [head("成员 · 象罔社团")]
    def card(x):
        return f"""
      <a class="beam tilt rv" href="{member_url(x['id'])}"><div class="beam-in mem spot">
        {avatar(x, 'av', 62)}<b>{esc(x['name'])}</b>
        <span class="mj">{esc(x['major'])}</span>
        {post_chip(x)}
      </div></a>"""
    groups = []
    for tier in TIER_ORDER:
        sub = [x for x in MEMBERS if x["tier"] == tier]
        if not sub:
            continue
        groups.append(f"""
      <div class="tier-bar"><span class="tn">{esc(tier)}</span><h3>{esc(tier)}</h3>
        <span class="cnt">{len(sub)} 人</span><span class="td">{esc(TIER_DESC[tier])}</span></div>
      <div class="mem-grid" style="margin-bottom:8px">{''.join(card(x) for x in sub)}</div>""")
    p.append(f"""
<section style="padding-top:60px">
  <div class="wrap">
    {sec_head("MEMBERS", '在册成员 <span class="grad">%d 位</span>' % len(MEMBERS), "按社团职位分层：社团负责人 → 技术部四大组长 → 职能部门部长 → 成员。点击任意成员查看详情页：语录、方向、技能、参与的项目。隐私说明：仅展示姓名·学院·专业·职位，其他个人信息一律不上网。")}
    {''.join(groups)}
  </div>
</section>
""")
    p.append(foot())
    return "".join(p)


def build_life():
    p = [head("社团动态 · 象罔社团")]
    items = "".join(f"""
      <div class="tl-item rv">
        <a class="tl-card spot" href="{life_url(a['id'])}">
          <span class="d">{esc(a['date'])} · {esc(a['weekday'])}</span>
          <h3>{esc(a['title'])}</h3>
          <p>{esc(a['summary'])}</p>
          <span class="go">查看详情 <span>→</span></span>
        </a>
      </div>""" for a in ACTIVITIES)
    p.append(f"""
<section style="padding-top:60px">
  <div class="wrap">
    {sec_head("CLUB LIFE", '社团动态 <span class="grad">%d 条</span>' % len(ACTIVITIES), "组会、分享会、比赛、上线前夜——社团每周都在发生的事。")}
    <div class="tl">{items}</div>
  </div>
</section>
""")
    p.append(foot())
    return "".join(p)

# ============================================================
# 详情页
# ============================================================
def pager(prev, nxt):
    a = f'<a href="{prev[0]}"><span class="lb">← PREV</span>{esc(prev[1])}</a>' if prev else "<span></span>"
    b = f'<a class="r" href="{nxt[0]}"><span class="lb">NEXT →</span>{esc(nxt[1])}</a>' if nxt else "<span></span>"
    return f'<div class="pager">{a}{b}</div>'

def build_work(x, prev, nxt):
    contrib = "".join(
        f'<a href="{member_url(cid)}"><span>{esc(m(cid)["name"])}{role_badge(role_of(x, cid))}</span>'
        f'<span class="ar">{esc(m(cid)["dir"][0])} →</span></a>'
        for cid in team_order(x) if m(cid))
    metrics = "".join(f'<div class="metric"><b><span data-count="{v}">0</span>{s}</b><span>{esc(l)}</span></div>'
                      for v, s, l in x["metrics"])
    steps = "".join(f'<li><p class="t">{esc(t)}</p><p class="h">{esc(h)}</p><p class="d">{esc(d)}</p></li>'
                    for t, h, d in x["timeline"])
    links = "".join(f'<a href="{u}" target="_blank"><span>{esc(t)}</span><span class="ar">↗</span></a>' for t, u in x["links"])
    others = [y for y in WORKS if y["id"] != x["id"]][:3]
    rel = "".join(f"""
      <a class="beam tilt" href="{work_url(y['id'])}"><div class="beam-in wk spot">
        <div class="cover {y['cv']}" style="height:96px"><span class="em" style="font-size:34px">{y['em']}</span></div>
        <div class="body" style="padding:15px 18px 18px"><span class="cat">{esc(y['cat'])}</span><h3 style="font-size:16px">{esc(y['title'])}</h3></div>
      </div></a>""" for y in others)
    meta = "".join(f"<span>{esc(s)}</span>" for s in [x["cat"], x["status"]] + x["stack"])
    return head(f'{x["title"]} · 象罔社团作品') + f"""
<div class="wrap crumb"><a href="index.html">首页</a> / <a href="projects.html">作品</a> / {esc(x['title'])}</div>
<section class="d-hero">
  <div class="wrap">
    <p class="kind">{esc(x['cat'].upper())} · {esc(x['status'])}</p>
    <h1>{esc(x['title'])}</h1>
    <p class="sub">{esc(x['desc'])}</p>
    <div class="d-meta">{meta}</div>
    <div class="d-cover {x['cv']}"><span class="em">{x['em']}</span></div>
  </div>
</section>
<div class="wrap d-body">
  <div>
    <h2>背后的故事</h2>
    <p>{esc(x['story'])}</p>
    <div class="metrics rv">{metrics}</div>
    <h2>项目时间线</h2>
    <ol class="steps rv">{steps}</ol>
    <div class="card" style="margin-top:6px">
      <h4>我们学到了什么</h4>
      <ul>{''.join(f'<li style="font-size:14px;color:var(--dim);padding:7px 0 7px 18px;position:relative"><span style="position:absolute;left:0;color:var(--cy)">▸</span>{esc(t)}</li>' for t in ["生产环境和本地跑通是两件事","上线前一定要有监控和回滚方案","文档写给自己看的，也写给下一届看的"])}</ul>
    </div>
    {pager(prev, nxt)}
  </div>
  <aside class="side">
    <div class="card">
      <h4>项目档案</h4>
      <div class="spec"><span class="k">分类</span><span class="v">{esc(x['cat'])}</span></div>
      <div class="spec"><span class="k">状态</span><span class="v">{esc(x['status'])}</span></div>
      <div class="spec"><span class="k">技术栈</span><span class="v">{esc(' / '.join(x['stack']))}</span></div>
      <div class="spec"><span class="k">队长</span><span class="v">{esc(m(lead_of(x))["name"]) if m(lead_of(x)) else "—"}</span></div>
      <div class="spec"><span class="k">参与成员</span><span class="v">{len(x['contributors'])} 人（1 名队长 + {max(len(x['contributors']) - 1, 0)} 名组员）</span></div>
    </div>
    <div class="card">
      <h4>他们做了这个项目</h4>
      <div class="side-links">{contrib}</div>
    </div>
    <div class="card">
      <h4>相关链接</h4>
      <div class="side-links">{links}</div>
    </div>
  </aside>
</div>
<section style="padding-top:0">
  <div class="wrap">
    <h2 style="font-size:20px;margin-bottom:20px">看看其他作品</h2>
    <div class="rel-grid">{rel}</div>
  </div>
</section>
""" + foot()

def build_member(x, prev, nxt):
    skills = "".join(f'<span class="sk-chip">{esc(s)}</span>' for s in x["skills"])
    exp = "".join(f'<li><b>{esc(t)}</b><span>{esc(d)}</span></li>' for t, d in x.get("exp", []))
    _ws = sorted([wid for wid in x["works"] if w(wid)],
                 key=lambda i: (role_of(w(i), x["id"]) != "队长", i))
    works = "".join(f"""
      <a href="{work_url(wid)}"><span>{esc(w(wid)['title'])}{role_badge(role_of(w(wid), x['id']))}</span><span class="ar">{esc(w(wid)['cat'])} →</span></a>"""
                    for wid in _ws) or '<span style="font-size:14px;color:var(--dim-2)">暂无（占位）</span>'
    lead_cnt = sum(1 for wid in x["works"] if w(wid) and role_of(w(wid), x["id"]) == "队长")
    member_cnt = len([i for i in x["works"] if w(i)]) - lead_cnt
    qa = "".join(f'<div style="margin-bottom:18px"><p style="font-family:var(--mono);font-size:14.5px;color:var(--cy);margin-bottom:5px">Q · {esc(q)}</p><p style="font-size:14.5px;color:var(--dim);line-height:1.85">{esc(a)}</p></div>' for q, a in x["qa"])
    rel = [y for y in MEMBERS if y["id"] != x["id"] and y["dir"][0] == x["dir"][0]][:3]
    if len(rel) < 3:
        rel += [y for y in MEMBERS if y["id"] != x["id"] and y not in rel][:3 - len(rel)]
    relc = "".join(f"""
      <a class="beam tilt" href="{member_url(y['id'])}"><div class="beam-in mem spot">
        {avatar(y, 'av', 54)}<b>{esc(y['name'])}</b><span class="mj">{esc(y['major'])}</span>{post_chip(y)}
      </div></a>""" for y in rel)
    tags = "".join(f"<span>{esc(d)}</span>" for d in x["dir"])
    return head(f'{x["name"]} · 象罔社团成员') + f"""
<div class="wrap crumb"><a href="index.html">首页</a> / <a href="members.html">成员</a> / {esc(x['name'])}</div>
<section class="d-hero">
  <div class="wrap">
    <p class="kind">MEMBER · {esc(x['tier'])} / {esc(x['post'])}</p>
    <h1>{esc(x['name'])}</h1>
    <p class="sub">{esc(x['college'])} · {esc(x['major'])} —— {esc(x['bio'])}</p>
    <div class="d-meta">{tags}<span>{esc(x['joined'])} 加入</span></div>
    <div class="d-cover cv{((x['hue'] - 1) % 5) + 1}">
      <div style="position:relative;z-index:3;text-align:center;padding:0 24px">
        {avatar(x, 'av', 96)}
        <p style="font-size:19px;margin-top:18px;line-height:1.8;color:#fff;max-width:34em">“{esc(x['quote'])}”</p>
      </div>
    </div>
  </div>
</section>
<div class="wrap d-body">
  <div>
    <h2>关于 {esc(x['name'])}</h2>
    <p>{esc(x['bio'])}（占位内容，上线前由本人补充）</p>
    <p>方向：<b>{esc(' / '.join(x['dir']))}</b>。{esc(x['joined'])} 加入象罔社团，参与项目 {len(x['works'])} 个。</p>
    <h2>擅长什么</h2>
    <div class="card sk-wrap">{skills}</div>
    <h2>做过什么</h2>
    <div class="card"><ul class="exp-list">{exp}</ul></div>
    <h2>问答 · 两句真心话</h2>
    <div class="card">{qa}</div>
    {pager(prev, nxt)}
  </div>
  <aside class="side">
    <div class="card">
      <h4>档案</h4>
      <div class="spec"><span class="k">职位</span><span class="v">{esc(x['post'])}</span></div>
      <div class="spec"><span class="k">层级</span><span class="v">{esc(x['tier'])}</span></div>
      <div class="spec"><span class="k">学院</span><span class="v">{esc(x['college'])}</span></div>
      <div class="spec"><span class="k">专业</span><span class="v">{esc(x['major'])}</span></div>
      <div class="spec"><span class="k">方向</span><span class="v">{esc(' / '.join(x['dir']))}</span></div>
      <div class="spec"><span class="k">加入</span><span class="v">{esc(x['joined'])}</span></div>
      <div class="spec"><span class="k">项目角色</span><span class="v">队长 {lead_cnt} · 组员 {member_cnt}</span></div>
    </div>
    <div class="card">
      <h4>参与的项目</h4>
      <div class="side-links">{works}</div>
    </div>
  </aside>
</div>
<section style="padding-top:0">
  <div class="wrap">
    <h2 style="font-size:20px;margin-bottom:20px">同方向 / 其他成员</h2>
    <div class="rel-grid">{relc}</div>
  </div>
</section>
""" + foot()

def build_activity(a, prev, nxt):
    photos = "".join(f'<div class="ph {cv}"><span>{em}</span><span class="cap">{esc(cap)}</span></div>' for em, cap, cv in a["photos"])
    tags = "".join(f"<span>#{esc(t)}</span>" for t in a["tags"])
    pps = "".join(f'<a href="{member_url(cid)}" title="{esc(m(cid)['name'])}">{avatar(m(cid), 'av', 40)}</a>'
                  for cid in a["participants"] if m(cid))
    others = [y for y in ACTIVITIES if y["id"] != a["id"]][:3]
    rel = "".join(f"""
      <a class="beam tilt" href="{life_url(y['id'])}"><div class="beam-in spot" style="padding:22px">
        <span class="cat" style="font-family:var(--mono);font-size:14.5px;color:var(--cy)">{esc(y['date'])}</span>
        <h3 style="font-size:16px;margin:8px 0 6px">{esc(y['title'])}</h3>
        <p style="font-size:14px;color:var(--dim)">{esc(y['summary'][:40])}…</p>
      </div></a>""" for y in others)
    body = "".join(f"<p>{esc(t)}</p>" for t in a["body"])
    return head(f'{a["title"]} · 象罔社团动态') + f"""
<div class="wrap crumb"><a href="index.html">首页</a> / <a href="life.html">社团动态</a> / {esc(a['date'])}</div>
<section class="d-hero">
  <div class="wrap">
    <p class="kind">CLUB LIFE · {esc(a['date'])} · {esc(a['weekday'])}</p>
    <h1>{esc(a['title'])}</h1>
    <p class="sub">{esc(a['summary'])}</p>
    <div class="d-meta">{tags}</div>
    <div class="d-cover {a['cv']}"><span class="em">{a['em']}</span></div>
  </div>
</section>
<div class="wrap d-body">
  <div>
    <h2>现场回顾</h2>
    {body}
    <h2>现场照片</h2>
    <div class="photo-grid">{photos}</div>
    <p style="font-family:var(--mono);font-size:14.5px;color:var(--dim-2)">// 占位图，上线前替换为真实照片</p>
    {pager(prev, nxt)}
  </div>
  <aside class="side">
    <div class="card">
      <h4>活动信息</h4>
      <div class="spec"><span class="k">日期</span><span class="v">{esc(a['date'])}</span></div>
      <div class="spec"><span class="k">星期</span><span class="v">{esc(a['weekday'])}</span></div>
      <div class="spec"><span class="k">地点</span><span class="v">工科楼 A-302（占位）</span></div>
      <div class="spec"><span class="k">标签</span><span class="v">{esc(' / '.join(a['tags']))}</span></div>
    </div>
    <div class="card">
      <h4>到场的人（{len(a['participants'])}）</h4>
      <div style="display:flex;flex-wrap:wrap;gap:8px">{pps}</div>
    </div>
  </aside>
</div>
<section style="padding-top:0">
  <div class="wrap">
    <h2 style="font-size:20px;margin-bottom:20px">其他动态</h2>
    <div class="rel-grid">{rel}</div>
  </div>
</section>
""" + foot()

def build_job(j):
    mentor = m(j["mentor"])
    return head(f'{j["title"]} · 象罔社团招新') + f"""
<div class="wrap crumb"><a href="index.html">首页</a> / <a href="index.html#recruit">招新</a> / {esc(j['title'])}</div>
<section class="d-hero">
  <div class="wrap">
    <p class="kind">JOIN US · {esc(j['team'])}</p>
    <h1>{esc(j['title'])}</h1>
    <p class="sub">{esc(j['intro'])}</p>
    <div class="d-meta">
      <span>{esc(j['org'])}</span>
      <span class="badge {'b-open' if j['status']=='open' else 'b-soon'}" style="border-radius:999px">{'● ' if j['status']=='open' else '○ '}{esc(j['status_text'])}</span>
      <span>带教：{esc(mentor['name']) if mentor else '待定'}</span>
    </div>
    <div class="d-cover cv2"><span class="em">💼</span></div>
  </div>
</section>
<div class="wrap d-body">
  <div>
    <h2>你会做什么</h2>
    <ul class="steps">{''.join(f'<li><p class="h">{esc(d)}</p></li>' for d in j['duty'])}</ul>
    <h2>我们希望你</h2>
    <ul class="steps">{''.join(f'<li><p class="h">{esc(r)}</p></li>' for r in j['reqs'])}</ul>
    <h2>加分项</h2>
    <ul class="steps">{''.join(f'<li><p class="h">{esc(r)}</p></li>' for r in j['plus'])}</ul>
    <h2>报名流程</h2>
    <ol class="steps">{''.join(f'<li><p class="t">{esc(t)}</p><p class="h">{esc(h)}</p><p class="d">{esc(d)}</p></li>' for t, h, d in PROCESS)}</ol>
  </div>
  <aside class="side">
    <div class="card">
      <h4>岗位档案</h4>
      <div class="spec"><span class="k">团队</span><span class="v">{esc(j['team'])}</span></div>
      <div class="spec"><span class="k">所属</span><span class="v">{esc(j['org'])}</span></div>
      <div class="spec"><span class="k">状态</span><span class="v">{esc(j['status_text'])}</span></div>
      <div class="spec"><span class="k">带教</span><span class="v">{esc(mentor['name']) if mentor else '待定'}</span></div>
    </div>
    <div class="card">
      <h4>联系方式</h4>
      <div class="side-links">
        <a href="index.html#contact"><span>招新 QQ 群</span><span class="ar">123-456-789</span></a>
        <a href="index.html#contact"><span>合作邮箱</span><span class="ar">→</span></a>
      </div>
    </div>
    {'<a class="btn btn-p" style="width:100%;justify-content:center" href="index.html#contact">现在报名 →</a>'}
  </aside>
</div>
""" + foot()

# ============================================================
# 登录 / 注册（邀请码准入）
# ============================================================
def build_login():
    return head("登录 · 注册 · 象罔社团",
                "象罔社团成员登录与注册入口：注册需要一枚社团成员邀请码。",
                gated=False) + r"""
<main class="auth-main">
  <div class="auth-wrap">

    <aside class="auth-brand">
      <canvas id="net"></canvas>
      <span class="auth-mark">准入</span>
      <div class="ab-in">
        <a class="logo" href="index.html"><span class="seal">象</span><span class="logo-txt"><b>象罔社团</b><small>XIANGWANG CLUB</small></span></a>
        <h1>这扇门，<br><em>只对拿到钥匙的人开。</em></h1>
        <p>整个站点只对社团成员开放——第一次来要先用邀请码注册，之后直接登录就能进。邀请码找社团里任何一位伙伴要一枚就行，他们当场就能给你。</p>
        <ul class="ab-list">
          <li><b>01</b><span>邀请码决定身份：普通成员，或者管理员，注册之后不能自己改</span></li>
          <li><b>02</b><span>大部分码限定人数，用完即止；谁用过、谁发的，码上都记着</span></li>
          <li><b>03</b><span>登录后进成员专区：组会安排、内部文档、任务看板、邀请码签发</span></li>
        </ul>

        <div class="ab-note open" id="noteBox">
          <button type="button" id="noteBtn"><i>DEMO</i><span>演示用邀请码</span><u>▾</u></button>
          <div class="ab-body">
            <p>这一版是前端演示，下面几枚是内置的测试邀请码，可以直接拿去把整个流程走一遍。</p>
            <div class="code-row account">
              <code>demo</code>
              <span>测试账号 · 口令 <b>xw2026</b> · 管理员 · 仅本机（localhost）演示可用</span>
              <button type="button" data-fillacc="demo">一键进</button>
            </div>
            <div id="demoCodes"></div>
          </div>
        </div>
      </div>
    </aside>

    <section class="auth-card">
      <div class="ac-glow"></div>
      <div class="aflash" id="flash"></div>

      <div class="atabs" id="tabs" data-on="login">
        <span class="atab-in"></span>
        <button class="atab on" type="button" data-tab="login">登录</button>
        <button class="atab" type="button" data-tab="reg">注册 · 需邀请码</button>
      </div>

      <form class="apanel on" id="paneLogin" novalidate>
        <div class="afield">
          <label>账号 <em>注册时填的那个</em></label>
          <div class="ain" data-for="lu"><i>@</i><input type="text" id="lu" placeholder="你的账号" autocomplete="username" spellcheck="false"></div>
          <p class="aerr" data-err="lu"></p>
        </div>
        <div class="afield">
          <label>密码</label>
          <div class="ain" data-for="lp"><i>✦</i><input type="password" id="lp" placeholder="至少 6 位" autocomplete="current-password"><button class="atail" type="button" data-eye="lp">显示</button></div>
          <p class="aerr" data-err="lp"></p>
        </div>
        <div class="arow">
          <label class="acheck"><input type="checkbox" id="lkeep" checked><u></u><span>记住我（7 天免登录）</span></label>
          <a href="#" id="forgot">忘记密码？</a>
        </div>
        <button class="asub" type="submit" id="lsub">登录并进入站点</button>
        <div class="aor"><i></i><span>或者</span><i></i></div>
        <button class="aguest" type="button" id="demoBtn">
          <span class="gd">🚪</span>
          <span class="gt"><b>用测试账号一键进入</b><small>demo / xw2026 · 管理员 · 仅本机演示可用</small></span>
          <span class="ga">→</span>
        </button>
        <p class="aalt">还没有账号？<button type="button" data-goto="reg">用邀请码注册 →</button></p>
      </form>

      <form class="apanel" id="paneReg" novalidate>
        <div class="afield">
          <label>邀请码 <u>*</u> <em>没有码注册不了</em></label>
          <div class="ain code" data-for="rc"><i>⚿</i><input type="text" id="rc" placeholder="XW2026-XXXXXX" autocomplete="off" spellcheck="false" maxlength="24"><span class="astat" id="rcIco"></span></div>
          <div class="cstate" id="rcState"></div>
          <p class="aerr" data-err="rc"></p>
        </div>
        <div class="a2col">
          <div class="afield">
            <label>昵称 <u>*</u></label>
            <div class="ain" data-for="rn"><i>✦</i><input type="text" id="rn" placeholder="社团里怎么称呼你" maxlength="20"></div>
            <p class="aerr" data-err="rn"></p>
          </div>
          <div class="afield">
            <label>账号 <u>*</u></label>
            <div class="ain" data-for="ru"><i>@</i><input type="text" id="ru" placeholder="字母开头 3-20 位" maxlength="20" autocomplete="username" spellcheck="false"></div>
            <p class="aerr" data-err="ru"></p>
          </div>
        </div>
        <div class="afield">
          <label>密码 <u>*</u></label>
          <div class="ain" data-for="rp"><i>✦</i><input type="password" id="rp" placeholder="至少 6 位，别用纯数字" autocomplete="new-password"><button class="atail" type="button" data-eye="rp">显示</button></div>
          <div class="strength" id="str" data-lv="0"><i></i><i></i><i></i><i></i></div>
          <p class="strength-txt" id="strTxt">密码强度 —</p>
          <p class="aerr" data-err="rp"></p>
        </div>
        <div class="afield">
          <label>确认密码 <u>*</u></label>
          <div class="ain" data-for="rp2"><i>✦</i><input type="password" id="rp2" placeholder="再输一遍" autocomplete="new-password"></div>
          <p class="aerr" data-err="rp2"></p>
        </div>
        <div class="arow" style="margin-bottom:20px">
          <label class="acheck"><input type="checkbox" id="ragree"><u></u><span>我确认邀请码是社团伙伴本人给我的，账号只用于社团内部站点</span></label>
        </div>
        <button class="asub" type="submit" id="rsub">用邀请码注册</button>
        <p class="aalt">已经有账号？<button type="button" data-goto="login">直接登录 →</button></p>
      </form>

      <div class="aok" id="aok">
        <div class="ring">✓</div>
        <h3 id="aokT">欢迎加入，象罔。</h3>
        <p id="aokP"></p>
        <div class="bar"><i></i></div>
      </div>

      <p class="afoot" style="margin-top:24px;text-align:center;font-size:13.5px;line-height:1.8;color:var(--dim-2)">
        演示版：账号和邀请码存在这台浏览器里，换设备或清缓存就没了。<br>
        正式上线要把校验搬到后端，前端这套只负责界面与流程。
      </p>
    </section>

  </div>
<script>
(function () {
  var A = window.XWAUTH, $ = function (s) { return document.querySelector(s); },
      $$ = function (s) { return Array.prototype.slice.call(document.querySelectorAll(s)); };
  var el = function (id) { return document.getElementById(id); };
  var box = function (id) { return document.querySelector('.ain[data-for="' + id + '"]'); };

  /* 目标页：只接受同目录下的 xxx.html，防开放重定向 */
  var next = (function () {
    var m = /[?&]next=([^&]+)/.exec(location.search);
    var v = m ? decodeURIComponent(m[1]) : 'index.html';
    return /^[A-Za-z0-9_\-]+\.html([?#].*)?$/.test(v) ? v : 'index.html';
  })();

  /* ---------- 提示条 / toast ---------- */
  var toastEl = null;
  function toast(msg, ms) {
    if (!toastEl) { toastEl = document.createElement('div'); toastEl.className = 'toast'; document.body.appendChild(toastEl); }
    toastEl.textContent = msg; toastEl.classList.add('on');
    clearTimeout(toastEl._t);
    toastEl._t = setTimeout(function () { toastEl.classList.remove('on'); }, ms || 2600);
  }
  function flash(msg, kind) {
    var f = $('#flash');
    if (!msg) { f.className = 'aflash'; f.textContent = ''; return; }
    f.className = 'aflash on ' + (kind || 'info');
    f.textContent = msg;
  }

  /* ---------- 字段错误 ---------- */
  function setErr(id, msg) {
    var e = document.querySelector('.aerr[data-err="' + id + '"]'), b = box(id);
    if (e) { e.textContent = msg || ''; e.classList.toggle('on', !!msg); }
    if (b) b.classList.toggle('bad', !!msg);
    return !msg;
  }
  function clearErr() {
    $$('.aerr').forEach(function (e) { e.classList.remove('on'); });
    $$('.ain').forEach(function (b) { b.classList.remove('bad'); });
  }

  /* ---------- 标签页 ---------- */
  function goto(tab) {
    $('#tabs').dataset.on = tab;
    $$('.atab').forEach(function (b) { b.classList.toggle('on', b.dataset.tab === tab); });
    $('#paneLogin').classList.toggle('on', tab === 'login');
    $('#paneReg').classList.toggle('on', tab === 'reg');
    clearErr();
    setTimeout(function () { var f = tab === 'login' ? el('lu') : el('rc'); if (f) f.focus(); }, 70);
  }
  $$('.atab').forEach(function (b) { b.addEventListener('click', function () { goto(b.dataset.tab); }); });
  $$('[data-goto]').forEach(function (b) { b.addEventListener('click', function () { goto(b.dataset.goto); }); });

  /* ---------- 密码显隐 ---------- */
  $$('[data-eye]').forEach(function (b) {
    b.addEventListener('click', function () {
      var i = el(b.dataset.eye), show = i.type === 'password';
      i.type = show ? 'text' : 'password';
      b.textContent = show ? '隐藏' : '显示';
    });
  });

  /* ---------- 邀请码实时校验 ---------- */
  var rcState = $('#rcState'), rcIco = $('#rcIco');
  function codeLive(live) {
    var v = el('rc').value.trim(), b = box('rc');
    if (!v) {
      rcState.className = 'cstate'; rcState.innerHTML = ''; rcIco.textContent = '';
      b.classList.remove('good', 'bad');
      if (!live) setErr('rc', '注册必须有邀请码，这是唯一入口');
      return false;
    }
    var r = A.checkCode(v);
    rcState.className = 'cstate on ' + (r.ok ? 'ok' : 'no');
    if (r.ok) {
      rcState.innerHTML = '✓ <b>' + A.esc(r.def.code) + '</b> · ' + A.esc(r.msg)
        + (r.def.owner && r.def.owner !== '社团' ? '<br>由 ' + A.esc(r.def.owner) + ' 发出' : '');
      rcIco.textContent = '✓';
    } else {
      rcState.innerHTML = '✕ ' + A.esc(r.msg);
      rcIco.textContent = '✕';
    }
    b.classList.toggle('good', r.ok); b.classList.toggle('bad', !r.ok);
    if (r.ok) setErr('rc', '');
    return r.ok;
  }
  el('rc').addEventListener('input', function () {
    var v = this.value.toUpperCase().replace(/[^A-Z0-9\-]/g, '');
    if (v !== this.value) this.value = v;
    codeLive(true);
  });
  el('rc').addEventListener('blur', function () { if (this.value.trim()) codeLive(false); });

  /* ---------- 密码强度 ---------- */
  var LV = ['—', '太弱 · 只有长度撑着', '一般 · 再混上字母和数字', '不错 · 加个符号更稳', '很稳 · 记牢它'];
  el('rp').addEventListener('input', function () {
    var p = this.value, s = 0;
    if (p.length >= 6) s++;
    if (p.length >= 10) s++;
    if (/[A-Za-z]/.test(p) && /[0-9]/.test(p)) s++;
    if (/[^A-Za-z0-9]/.test(p)) s++;
    if (!p) s = 0;
    $('#str').dataset.lv = s;
    $('#strTxt').textContent = '密码强度 ' + LV[Math.min(s, 4)];
    if (p) setErr('rp', '');
  });
  el('rp2').addEventListener('input', function () { if (this.value === el('rp').value) setErr('rp2', ''); });

  /* ---------- 成功态 ---------- */
  function succeed(title, sub) {
    $$('.apanel').forEach(function (p) { p.classList.remove('on'); });
    $('#tabs').style.display = 'none';
    $('.afoot').style.display = 'none';
    $('#aokT').textContent = title;
    $('#aokP').textContent = sub;
    $('#aok').classList.add('on');
    setTimeout(function () { location.href = next; }, 1300);
  }

  /* ---------- 登录 ---------- */
  $('#paneLogin').addEventListener('submit', function (e) {
    e.preventDefault(); clearErr(); flash('');
    var u = el('lu').value.trim(), pw = el('lp').value;
    if (!u) return setErr('lu', '账号不能空着');
    if (!pw) return setErr('lp', '密码不能空着');
    var b = $('#lsub'); b.disabled = true; b.textContent = '正在校验…';
    A.login(u, pw).then(function (r) {
      if (!r.ok) { b.disabled = false; b.textContent = '登录并进入站点'; return setErr(r.field, r.msg); }
      succeed('欢迎回来，' + r.user.name + '。',
        A.roleLabel(r.user.role) + ' · 邀请码 ' + (r.user.code || '—') + ' · 正在进入站点');
    });
  });

  /* ---------- 注册 ---------- */
  $('#paneReg').addEventListener('submit', function (e) {
    e.preventDefault(); clearErr(); flash('');
    if (!codeLive(false)) return;
    if (!el('rn').value.trim()) return setErr('rn', '填个昵称，方便其他成员认人');
    var u = el('ru').value.trim();
    if (!/^[A-Za-z][A-Za-z0-9_]{2,19}$/.test(u)) return setErr('ru', '账号 3-20 位，字母开头，只能字母 / 数字 / 下划线');
    var pw = el('rp').value;
    if (pw.length < 6) return setErr('rp', '密码至少 6 位');
    if (pw !== el('rp2').value) return setErr('rp2', '两次输入的密码不一致');
    if (!el('ragree').checked) { flash('先勾一下最下面那行确认，再提交。', 'warn'); return; }

        var b = $('#rsub'); b.disabled = true; b.textContent = '正在校验邀请码…';
        A.register({ code: el('rc').value, name: el('rn').value, u: u, pw: pw, pw2: el('rp2').value })
          .then(function (r) {
            if (!r.ok) {
              b.disabled = false; b.textContent = '用邀请码注册';
              if (r.field === 'code') { codeLive(false); setErr('rc', r.msg); }
              else setErr(r.field, r.msg);
              return;
            }
            succeed('欢迎加入，' + r.user.name + '。',
              '邀请码 ' + r.def.code + ' 生效 · 身份 ' + A.roleLabel(r.user.role) + ' · 正在进入站点');
          });
  });

  /* ---------- 忘记密码 ---------- */
  $('#forgot').addEventListener('click', function (e) {
    e.preventDefault();
    flash('这个站还没有邮件服务。忘记密码就找发邀请码给你的那位伙伴，让他帮你重置；或者换个账号重新用邀请码注册。', 'info');
  });

  /* ---------- 测试账号：一键进入 ----------
     预置测试账号只在本地演示时可用（判定逻辑见 assets/auth.js 的 DEMO_ON）。
     公网访问时把登录页上的相关入口整个摘掉，免得把一个「公开口令的管理员
     账号」摆在门口。注意：摘掉入口只是减少暴露面，不等于安全 —— 详见 README。 */
  if (!A.demoAvailable()) {
    ['.ab-note .code-row.account', '#demoBtn', '.auth-card .aor'].forEach(function (sel) {
      var n = document.querySelector(sel);
      if (n && n.parentNode) n.parentNode.removeChild(n);
    });
  }

  function demoEnter(btn, label) {
    clearErr(); flash('');
    var old = label || (btn ? btn.textContent : '');
    if (btn) { btn.disabled = true; btn.textContent = '正在进入…'; }
    A.demoLogin().then(function (r) {
      if (!r.ok) {
        if (btn) { btn.disabled = false; btn.textContent = old; }
        flash(r.msg || '测试账号暂时进不去，请稍后再试。', 'warn');
        return;
      }
      succeed('欢迎回来，' + r.user.name + '。',
        A.roleLabel(r.user.role) + ' · 内置测试账号 · 正在进入站点');
    });
  }
  /* 元素可能已被上面的逻辑摘掉，取到再加监听 */
  if ($('#demoBtn')) $('#demoBtn').addEventListener('click', function () { demoEnter(this); });

  /* ---------- 演示邀请码清单 ---------- */
  $('#noteBtn').addEventListener('click', function () { $('#noteBox').classList.toggle('open'); });
  $('#demoCodes').innerHTML = A.codes().map(function (c) {
    var st = A.codeState(c);
    return '<div class="code-row' + (st.ok ? '' : ' dead') + '">'
      + '<code>' + A.esc(c.code) + '</code>'
      + '<span>' + A.esc(c.group || '') + (c.quota > 0 ? ' · 限 ' + c.quota + ' 次' : ' · 不限次') + '</span>'
      + '<button type="button" data-fill="' + A.esc(c.code) + '">' + (st.ok ? '填入' : '已失效') + '</button></div>';
  }).join('');
  $('#noteBox').addEventListener('click', function (e) {
    var acc = e.target.closest('[data-fillacc]');
    if (acc) { demoEnter(acc, '一键进'); return; }
    var b = e.target.closest('[data-fill]');
    if (!b) return;
    goto('reg');
    el('rc').value = b.dataset.fill;
    codeLive(true);
    toast('邀请码已填好，接着写昵称和密码就行');
  });

  /* ---------- 进入页面时的状态提示 ---------- */
  (function boot() {
    var q = location.search;
    if (/[?&]need=1/.test(q)) flash('整个站点只对社团成员开放，先登录或注册。', 'warn');
    else if (/[?&]bye=1/.test(q)) flash('已退出登录，会话清掉了。', 'info');
    var s = A.session();
    if (s) flash('当前已登录为 ' + s.name + '（' + A.roleLabel(s.role) + '）。想换账号，直接登录另一个即可。', 'info');
    var pre = /[?&]code=([^&]+)/.exec(q);
    if (pre) { goto('reg'); el('rc').value = decodeURIComponent(pre[1]).toUpperCase(); codeLive(true); }
  })();
})();
</script>
""" + foot()


# ============================================================
# 成员专区（需邀请码注册并登录后才能进）
# ============================================================
def build_area():
    return head("成员专区 · 象罔社团",
                "象罔社团成员专区：组会安排、内部文档、任务看板与邀请码管理。",
                gated=True) + r"""
<header class="area-head">
  <div class="wrap">
    <p class="kicker">MEMBERS ONLY · 成员专区</p>
    <h1>欢迎回来，<em id="whoName">成员</em></h1>
    <p>这里的东西不对官网访客开放：组会安排、内部文档、任务看板，以及整套邀请码。</p>
    <div class="area-badges" id="badges"></div>
  </div>
</header>

<section style="padding-top:0">
  <div class="wrap"><div class="agrid" id="cards"></div></div>
</section>

<section id="codes" style="padding-top:56px">
  <div class="wrap">
    <div class="sec-head" style="margin-bottom:28px">
      <span class="sec-num">02</span>
      <p class="kicker">INVITE · 邀请码</p>
      <h2>谁能进来，由这里决定</h2>
      <p>每枚邀请码都记着归属人、可用次数和实际用量。管理员可以现场签发新码。</p>
    </div>

    <div class="acard" id="issueCard" style="margin-bottom:18px">
      <h3><span>⌘</span>签发新邀请码</h3>
      <div class="issue-form">
        <div><label>邀请码</label><input type="text" id="ic" placeholder="XW2026-XIAOWANG" maxlength="24"></div>
        <div><label>身份</label><select id="irole"><option value="member">社团成员</option><option value="admin">管理员</option></select></div>
        <div><label>可用次数（0 不限）</label><input type="text" id="iquota" value="1" maxlength="3"></div>
        <div><label>归属 / 备注</label><input type="text" id="igroup" placeholder="技术一组" maxlength="16"></div>
        <div><button type="button" id="ibtn">签发</button></div>
      </div>
      <div class="issue-msg" id="imsg"></div>
    </div>

    <div class="locked" id="lockTip">
      <b>🔒 只读模式</b>
      <p>你的身份是社团成员，可以查看邀请码的使用情况；签发新码需要管理员权限。</p>
    </div>

    <div class="acard" style="padding:6px 10px 10px">
      <table class="code-table" id="codeTable"></table>
    </div>
    <p style="margin-top:14px;font-size:13.5px;line-height:1.8;color:var(--dim-2)">
      // 提醒：邀请码表和账号表都存在这台浏览器里，换台设备看到的不是同一份；正式版应由后端统一管理并校验。
    </p>
  </div>
</section>
<script>
(function () {
  var A = window.XWAUTH, $ = function (s) { return document.querySelector(s); };
  var s = A.session();
  if (!s) return;                       /* 兜底：auth.js 已经拦过一次 */

  var toastEl = null;
  function toast(msg, ms) {
    if (!toastEl) { toastEl = document.createElement('div'); toastEl.className = 'toast'; document.body.appendChild(toastEl); }
    toastEl.textContent = msg; toastEl.classList.add('on');
    clearTimeout(toastEl._t);
    toastEl._t = setTimeout(function () { toastEl.classList.remove('on'); }, ms || 2400);
  }

  /* ---------- 身份徽章 ---------- */
  var mine = A.findCode(s.code);
  $('#whoName').textContent = s.name;
  var badges = [
    { t: '@' + s.u, c: '' },
    { t: A.roleLabel(s.role), c: 'hot' },
    { t: s.group || '社团' },
    { t: '会话有效至 ' + A.fmtDate(s.exp), c: 'ok' },
    { t: '邀请人 ' + (mine && mine.owner ? mine.owner : '—') }
  ];
  $('#badges').innerHTML = badges.map(function (b) {
    return '<span class="abadge ' + (b.c || '') + '">' + A.esc(b.t) + '</span>';
  }).join('');

  /* ---------- 专区四张卡 ---------- */
  var users = A.users();
  var remote = users.filter(function (u) { return u.u !== s.u; });
  var cards = [
    { ic: '📅', h: '本周安排', rows: [
      ['周五 19:00', '全体组会 @ 工科楼 A-302'],
      ['周六 14:00', '技术一组 · 代码评审'],
      ['周日 20:00', '论文研读（线上）']
    ] },
    { ic: '📁', h: '内部文档', rows: [
      ['提交规范', '分支命名 / 提交信息 / Code Review 流程'],
      ['模板', '周报模板 · 进度汇报模板'],
      ['归档', '历次组会纪要与决议']
    ] },
    { ic: '🧭', h: '任务看板', rows: [
      ['进行中', 'OpenClaw 工具注册层重构'],
      ['待认领', '官网 v3 移动端细节走查'],
      ['已完成', '成员档案页改简历式模块']
    ] },
    { ic: '👥', h: '其他已注册成员', rows: remote.length
      ? remote.slice(-6).map(function (u) { return ['@' + u.u, u.name + ' · ' + A.roleLabel(u.role)]; })
      : [['—', '暂时只有你自己，去下面签一枚码拉个人进来']] }
  ];
  $('#cards').innerHTML = cards.map(function (c) {
    return '<div class="acard"><h3><span>' + c.ic + '</span>' + c.h + '</h3><ul>'
      + c.rows.map(function (r) {
          return '<li><b>' + A.esc(r[0]) + '</b><span>' + A.esc(r[1]) + '</span></li>';
        }).join('')
      + '</ul></div>';
  }).join('');

  /* ---------- 邀请码表 ---------- */
  function renderCodes() {
    var head = '<thead><tr><th>邀请码</th><th>身份</th><th>归属</th><th>用量</th><th>状态</th><th></th></tr></thead><tbody>';
    var body = A.codes().map(function (c) {
      var st = A.codeState(c);
      var cls = st.state !== 'ok' ? 'none' : (c.quota > 0 && st.left <= 1 ? 'some' : 'free');
      var txt = st.state !== 'ok' ? (st.state === 'expired' ? '已过期' : '已用尽')
                                  : (c.quota > 0 ? '剩余 ' + st.left + ' 次' : '不限次');
      return '<tr><td><code>' + A.esc(c.code) + '</code></td>'
        + '<td>' + (c.role === 'admin' ? '管理员' : '社团成员') + '</td>'
        + '<td>' + A.esc(c.owner || '—')
          + (c.group ? '<br><span style="font-size:13.5px;color:var(--dim-2)">' + A.esc(c.group) + '</span>' : '')
          + '</td>'
        + '<td>' + st.used + ' 人已用'
          + (c.quota > 0 ? '<br><span style="font-size:13.5px;color:var(--dim-2)">上限 ' + c.quota + '</span>' : '')
          + '</td>'
        + '<td><span class="pill ' + cls + '">' + txt + '</span></td>'
        + '<td><button class="mini" type="button" data-copy="' + A.esc(c.code) + '">复制</button></td></tr>';
    }).join('');
    $('#codeTable').innerHTML = head + body + '</tbody>';
  }
  renderCodes();

  $('#codeTable').addEventListener('click', function (e) {
    var b = e.target.closest('[data-copy]');
    if (!b) return;
    var t = b.dataset.copy;
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(t).catch(function () {});
    } else {
      var i = document.createElement('textarea');
      i.value = t; document.body.appendChild(i); i.select();
      try { document.execCommand('copy'); } catch (err) {}
      document.body.removeChild(i);
    }
    toast('已复制 ' + t);
  });

  /* ---------- 签发（仅管理员） ---------- */
  if (s.role === 'admin') {
    $('#ibtn').addEventListener('click', function () {
      var m = $('#imsg');
      var r = A.issueCode({
        code: $('#ic').value, role: $('#irole').value,
        quota: $('#iquota').value, group: $('#igroup').value
      });
      m.className = 'issue-msg on ' + (r.ok ? 'ok' : 'no');
      m.textContent = r.ok ? ('签发成功：' + r.code + ' —— 把这一串发给要拉进来的同学就行。') : r.msg;
      if (r.ok) { $('#ic').value = ''; renderCodes(); toast('新邀请码已签发'); }
    });
  } else {
    $('#issueCard').style.display = 'none';
    $('#lockTip').classList.add('on');
  }

  if (/[?&]denied=1/.test(location.search)) toast('那个区域需要管理员权限');
})();
</script>
""" + foot()


# ============================================================
# 输出
# ============================================================
def write(name, content):
    path = os.path.join(OUT, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path

def main():
    os.makedirs(os.path.join(OUT, "assets"), exist_ok=True)
    # 清理上一版页面，避免改了 id 之后留下孤儿文件
    for stale in glob.glob(os.path.join(OUT, "*.html")):
        os.remove(stale)
    src_logo = os.path.join(SRC, "assets", "logo.png")
    if os.path.exists(src_logo):
        shutil.copy(src_logo, os.path.join(OUT, "assets", "logo.png"))

    n = 0
    write("index.html", build_index()); n += 1
    write("projects.html", build_projects()); n += 1
    write("members.html", build_members()); n += 1
    write("life.html", build_life()); n += 1
    write("login.html", build_login()); n += 1
    write("area.html", build_area()); n += 1

    for i, x in enumerate(WORKS):
        prev = (work_url(WORKS[i - 1]["id"]), WORKS[i - 1]["title"]) if i > 0 else None
        nxt = (work_url(WORKS[i + 1]["id"]), WORKS[i + 1]["title"]) if i < len(WORKS) - 1 else None
        write(work_url(x["id"]), build_work(x, prev, nxt)); n += 1

    for i, x in enumerate(MEMBERS):
        prev = (member_url(MEMBERS[i - 1]["id"]), MEMBERS[i - 1]["name"]) if i > 0 else None
        nxt = (member_url(MEMBERS[i + 1]["id"]), MEMBERS[i + 1]["name"]) if i < len(MEMBERS) - 1 else None
        write(member_url(x["id"]), build_member(x, prev, nxt)); n += 1

    for i, a in enumerate(ACTIVITIES):
        prev = (life_url(ACTIVITIES[i - 1]["id"]), ACTIVITIES[i - 1]["title"]) if i > 0 else None
        nxt = (life_url(ACTIVITIES[i + 1]["id"]), ACTIVITIES[i + 1]["title"]) if i < len(ACTIVITIES) - 1 else None
        write(life_url(a["id"]), build_activity(a, prev, nxt)); n += 1

    for j in JOBS:
        write(job_url(j["id"]), build_job(j)); n += 1

    print("generated %d pages -> %s" % (n, OUT))

if __name__ == "__main__":
    main()
