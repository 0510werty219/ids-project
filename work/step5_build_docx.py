# -*- coding: utf-8 -*-
"""生成《基于深度学习的入侵检测系统需求说明书与数据准备报告》DOCX。"""
import json
import os

from docx import Document

from docx_helpers import (BODY_EA, BODY_FONT, GRAY, INK, UI_EA, UI_FONT, Builder, num,
                          pct)

WORK = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(WORK, "out")
FIG_DIR = os.path.join(WORK, "fig")
OUTPUT = os.path.join(os.path.dirname(WORK),
                      "基于深度学习的入侵检测系统需求说明书与数据准备报告.docx")

meta = json.load(open(os.path.join(OUT_DIR, "preprocess_meta.json"), encoding="utf-8"))
metrics = json.load(open(os.path.join(OUT_DIR, "metrics.json"), encoding="utf-8"))
over = json.load(open(os.path.join(OUT_DIR, "metrics_oversample.json"), encoding="utf-8"))

doc = Document()
b = Builder(doc)
b.setup_styles()
doc.core_properties.title = "基于深度学习的入侵检测系统需求说明书与数据准备报告"
doc.core_properties.subject = "NSL-KDD 数据集预处理与基线验证"
doc.core_properties.author = "项目组"
doc.core_properties.last_modified_by = "项目组"
doc.core_properties.comments = ""
doc.core_properties.keywords = "入侵检测, NSL-KDD, 深度学习, 数据预处理"

# ---------------------------------------------------------------- 标题区
doc.add_paragraph("基于深度学习的入侵检测系统需求说明书与数据准备报告", style="Title")
sub = doc.add_paragraph()
sub.paragraph_format.space_after = 3
b.add_rich(sub, "NSL-KDD 数据集的预处理、基线验证与后续实施建议", size=11.5, name=UI_FONT,
           east=UI_EA, color=GRAY)
info = doc.add_paragraph()
info.paragraph_format.space_after = 16
b.add_rich(info, "适用对象：大二学生项目团队（2–4 人） ｜ 数据来源：NSL-KDD 四个数据文件 ｜ "
                 "文档版本：1.0 ｜ 日期：2026 年 10 月", size=9.5, name=UI_FONT, east=UI_EA,
           color=GRAY)

b.body("本文档是《基于深度学习的入侵检测系统分阶段实现方案》中阶段一与阶段二的交付物。文档先确定检测目标、"
       "应用场景与验收指标，再完成 NSL-KDD 数据集的清洗、编码、标准化与划分，并用三个基线模型验证处理后的"
       "数据能否直接支撑后续的深度学习训练。文中所有统计数字与实验指标均来自对四个 NSL-KDD 数据文件的实测，"
       "可以直接用于阶段三的模型开发与阶段五的结果撰写。")

# ---------------------------------------------------------------- 一、需求分析
doc.add_paragraph("一、需求分析", style="Heading 1")
b.body("需求分析要回答三个问题：检测什么、在什么条件下使用、做到什么程度算合格。本章把这三项固化为可验证"
       "的指标，并说明指标的评估口径，避免后期因口径不一致而返工。")

doc.add_paragraph("1.1 检测目标", style="Heading 2")
b.body("系统定位为网络入侵检测（NIDS），输入是一条网络连接记录的 41 维特征，输出是类别标签与置信度。"
       "检测目标分两级实现，先易后难。")
b.body("**第一级是二分类**，判断记录属于正常流量还是攻击流量。它结构最简单、训练最快，用于把「数据读取、"
       "预处理、训练、评估、推理」整条链路先跑通，也是后续所有实验的对照组。")
b.body("**第二级是多分类**，在二分类的基础上进一步区分 DoS、Probe、R2L、U2R 四类攻击。多分类的价值在于"
       "报警可解释、可与应急响应流程对接，难度则集中在 R2L 与 U2R：这两类在训练集中分别只有 995 条和 52 条"
       "样本，且测试集中包含大量训练阶段从未出现过的攻击类型。")

doc.add_paragraph("1.2 应用场景与系统边界", style="Heading 2")
b.body("使用场景为**离线检测加简易实时演示**。先用官方划分的训练集与测试集完成训练和评估，再用脚本逐条读取"
       "测试集模拟流量到达，实时输出检测结果并统计运行指标，最终以网页仪表盘的形式呈现。")
b.body("系统按网络流量检测设计，不涉及主机日志、进程行为等主机侧数据。系统不做工业级吞吐与低延迟承诺；"
       "真实抓包接入会引入 pcap 到 78 维特征的特征工程工作量，作为可选的加分项，在时间允许时再做，"
       "并在报告中标注为未来工作。")

doc.add_paragraph("1.3 验收指标与评估口径", style="Heading 2")
b.body("验收指标统一以**官方测试集 KDDTest+** 为准，同时要求报告训练集内部验证集的结果，用于说明泛化差距。"
       "指标定义与目标值如下。")
b.table_caption("表 1  验收指标与目标值")
b.make_table(
    ["指标", "目标值", "说明"],
    [["二分类准确率", "≥ 85%", "KDDTest+ 上全部样本的判对比例"],
     ["二分类 F1", "≥ 0.85", "精确率与召回率的调和平均"],
     ["二分类误报率 FPR", "≤ 10%", "正常流量被误判为攻击的比例，IDS 工程核心痛点"],
     ["五分类 macro-F1", "≥ 0.75", "四个攻击类与正常类等权平均，避免大类主导结果"],
     ["未知攻击检出率", "单独报告", "测试集中 17 类训练阶段未见过的攻击，不设硬性门槛"]],
    [3.4, 2.6, 10.0], ["left", "center", "left"])
b.spacer(2)
b.body("**评估口径必须先说清楚，否则数字没有意义。**本轮实验显示，同一组模型的表现在两个口径下差距极大："
       "在从 KDDTrain+ 随机分层划分出的验证集上，随机森林准确率为 99.88%、MLP 为 99.61%；而在官方测试集"
       "KDDTest+ 上，两者分别只有 77.52% 和 78.80%。原因有两个：测试集包含 17 类训练阶段未见过的攻击类型，"
       "共 3,750 条（占测试集 16.6%）；测试集的类别比例也与训练集明显不同。网络上大量「NSL-KDD 准确率 99%」"
       "的教程，多数是在 KDDTrain+ 内部随机划分上评估的，不能与本项目的指标直接比较。本项目统一以 KDDTest+ "
       "为验收口径，并要求所有实验同时给出两个口径的数字。")

doc.add_paragraph("1.4 团队分工与进度", style="Heading 2")
b.table_caption("表 2  阶段进度与里程碑")
b.make_table(
    ["周次", "阶段", "里程碑"],
    [["第 1 周", "需求分析", "需求说明书、验收指标与分工确定"],
     ["第 2–3 周", "数据准备", "预处理脚本、训练/验证/测试数据、类别分布报告"],
     ["第 4 周", "模型设计", "MLP 基线跑通、1D-CNN 主模型代码完成"],
     ["第 5–6 周", "训练与调优", "收敛模型、实验记录表、损失曲线"],
     ["第 7 周", "模型评估", "双口径指标对比表、混淆矩阵与误差分析"],
     ["第 7–8 周", "部署与收尾", "检测演示系统、项目报告、答辩 PPT"]],
    [2.2, 3.0, 10.8], ["center", "left", "left"])
b.spacer(2)
b.body("三人团队按数据与评估、模型与训练、部署与统筹三条线分工，每周一次 30 分钟例会同步进度；"
       "两人团队则由一人兼顾数据与评估、另一人兼顾模型与部署。")

# ---------------------------------------------------------------- 二、数据准备
doc.add_paragraph("二、数据准备", style="Heading 1")
b.body("阶段二的目标是产出可直接喂给模型的数据，并让每一步处理都可复现。本章依次说明数据来源、质量检查结果、"
       "类别分布、预处理流程与最终产物。")

doc.add_paragraph("2.1 数据来源与文件清单", style="Heading 2")
b.table_caption("表 3  NSL-KDD 数据文件清单与实测样本量")
b.make_table(
    ["文件名", "样本数", "用途"],
    [["KDDTrain+.txt", num(125973), "官方训练集，用于训练与内部验证"],
     ["KDDTest+.txt", num(22544), "官方测试集，含 17 类未见过的攻击，作为唯一验收基准"],
     ["KDDTrain+_20Percent.txt", num(25192), "训练集的 20% 抽样，供快速试跑与调试"],
     ["KDDTest-21.txt", num(11850), "从 KDDTest+ 中剔除 difficulty 取值为 21 的记录"]],
    [5.6, 2.4, 8.2], ["left", "right", "left"])
b.spacer(2)
b.body("四个文件均为 43 列、以逗号分隔且不带表头，依次是 41 维特征、标签列 label 与难度列 difficulty。"
       "预处理脚本按公开的标准特征名补齐列名后处理，41 维特征的定义见附录 A。")

doc.add_paragraph("2.2 数据质量检查", style="Heading 2")
b.table_caption("表 4  数据质量检查结果与处理方式")
b.make_table(
    ["检查项", "实测结果", "处理方式"],
    [["缺失值", "0 个", "无需填充或删除"],
     ["无穷值 Inf", "0 个", "无需处理"],
     ["单个文件内完全重复记录", "0 条", "无需去重"],
     ["训练集与测试集交叉重复", "610 条（占测试集 2.7%）", "评测前建议剔除，避免高估效果"],
     ["测试集未出现过的 service 取值", "6 种（aol、harvest 等）", "编码器按未知取值处理"],
     ["测试集未出现过的攻击类型", "17 种，共 3,750 条", "单独统计检出率，不并入整体指标"]],
    [5.2, 4.6, 6.4], ["left", "center", "left"])
b.spacer(2)
b.body("数据整体非常干净，不需要常规的缺失值填充与去重。以下两处需要特别说明。")
b.body("**训练集与测试集之间存在 610 条完全相同的记录**，41 维特征与标签全部一致。这部分记录会让测试结果"
       "略偏乐观，正式评估前应把它们从测试集中剔除，或至少在报告中说明其存在。")
b.body("**测试集包含 17 种训练阶段未见过的攻击类型**，例如 apache2、mscan、saint、processtable、"
       "snmpgetattack 等，合计 3,750 条。另外有 6 种 service 取值只出现在训练集，编码器若直接对测试集"
       "调用拟合会报错或产生错位，因此本次采用只对训练集拟合、把未知取值编码为全零的方式处理。")
b.body("难度列 difficulty 的取值范围是 0 到 21。实测发现它与模型准确率呈负相关：取值越高越容易被正确分类，"
       "取值 21 的 10,694 条记录中有 70.7% 是正常流量或 neptune、smurf 这类典型 DoS，基线模型在这部分的"
       "准确率超过 97.5%。KDDTest-21 恰好等于 KDDTest+ 去掉这部分记录后的结果，因此它的攻击占比达到 81.8%，"
       "是更难、更贴近实战的子集。使用该字段下结论时必须同时说明口径，本报告统一以 KDDTest+ 为准。")

doc.add_paragraph("2.3 类别分布与不平衡程度", style="Heading 2")
b.figure(os.path.join(FIG_DIR, "fig1_class_distribution.png"),
         "图 1  五类样本在训练集与测试集中的分布（纵轴为对数刻度）", 15.2)
b.figure(os.path.join(FIG_DIR, "fig2_attack_types.png"),
         "图 2  主要攻击类型的样本量对比（按训练集样本量排序，前 14 类）", 15.2)
b.table_caption("表 5  五类样本分布与训练权重")
tr_c, te_c = meta["train_category_counts"], meta["test_category_counts"]
wt = meta["class_weight_multi"]
tot_tr, tot_te = sum(tr_c.values()), sum(te_c.values())
b.make_table(
    ["类别", "训练集样本数", "训练集占比", "测试集样本数", "测试集占比", "训练权重"],
    [[c, num(tr_c[c]), pct(tr_c[c] / tot_tr, 2), num(te_c[c]), pct(te_c[c] / tot_te, 2),
      f"{wt[c]:.3f}"] for c in ["Normal", "DoS", "Probe", "R2L", "U2R"]],
    [2.2, 3.0, 2.6, 3.0, 2.6, 2.4], ["left", "right", "right", "right", "right", "right"])
b.spacer(2)
b.body("训练集中正常流量占 53.5%，U2R 只有 52 条（0.04%），R2L 只有 995 条（0.79%），类别不平衡非常严重。"
       "若不做处理，模型会倾向把所有少数类判为 Normal，整体准确率仍然好看，但安全场景最关心的召回率会很低。"
       "训练时按类别加权后，U2R 的权重达到 484.5，R2L 为 25.3。")
b.body("还需要注意训练分布与测试分布并不一致：R2L 在训练集中占 0.79%，在测试集中占 12.80%；"
       "U2R 从 0.04% 上升到 0.30%。也就是说，测试集对少数类施加了比训练集大得多的权重，"
       "这正是官方测试集指标远低于内部验证指标的重要原因之一。")

doc.add_paragraph("2.4 预处理流程", style="Heading 2")
b.body("预处理按以下七步执行，每一步都在脚本中固化，训练、验证、测试三份数据共用同一套流程。")
b.numbered(1, "**列名补齐与格式统一。**按 41 维标准特征名补齐列名，把 label 作为标签列、difficulty 单独"
              "保留，避免把难度列误当作特征输入模型。")
b.numbered(2, "**去重与异常值检查。**删除完全重复记录并统计缺失值与无穷值。本数据集三项检查均为零，"
              "该步骤同时保证换用 CIC-IDS2017 等其他数据集时流程仍然成立。")
b.numbered(3, "**标签映射。**把 23 种攻击类型归并为 DoS、Probe、R2L、U2R 四类，加上 Normal 共五类，"
              "用于多分类任务；同时生成 normal / attack 二值标签用于二分类任务，完整映射见附录 B。")
b.numbered(4, "**类别特征 One-Hot 编码。**protocol_type（3 种取值）、service（训练集 70 种）、"
              "flag（11 种）三列做 One-Hot，共展开为 84 维；词表只用训练集拟合，测试集的未知取值编码为全零。")
b.numbered(5, "**数值特征标准化。**其余 38 列做零均值单位方差的标准化，标准化器只用训练集拟合。"
              "两步都采用「训练集拟合、测试集变换」的方式，避免数据泄露。")
b.numbered(6, "**数据划分。**训练与评估沿用官方划分：KDDTrain+ 作为训练集、KDDTest+ 作为测试集。"
              "再从训练集中按标签分层抽取 20% 作为内部验证集，得到 100,778 条训练样本与 25,195 条验证样本。")
b.numbered(7, "**类别不平衡处理。**训练时按类别加权（class_weight），把少数类的损失权重按样本量倒数放大；"
              "过采样作为进阶方案在阶段三的模型上再做对照。")
b.spacer(2)
b.body("经过以上步骤，每条记录被转换为 **122 维**特征向量：38 维标准化后的数值特征加 84 维 One-Hot 特征。"
       "标准化器与编码器均已保存为文件，推理时必须复用，以保证离线评估与在线检测的特征变换完全一致。")

doc.add_paragraph("2.5 预处理产物清单", style="Heading 2")
b.table_caption("表 6  预处理产物清单")
b.make_table(
    ["文件", "内容", "形状或说明"],
    [["X_train.npy / X_val.npy / X_test.npy", "特征矩阵",
      "100,778 × 122 / 25,195 × 122 / 22,544 × 122"],
     ["y_train_multi.npy 等", "五分类标签", "取值 0–4，对应 Normal、DoS、Probe、R2L、U2R"],
     ["y_train_binary.npy 等", "二分类标签", "0 为正常、1 为攻击"],
     ["encoder.joblib", "One-Hot 编码器", "仅用训练集拟合，未知取值编码为全零"],
     ["scaler.joblib", "标准化器", "仅用训练集拟合，覆盖 38 维数值特征"],
     ["preprocess_meta.json", "处理元数据", "特征名顺序、类别顺序、样本量与类别权重"],
     ["clean_train.csv / clean_test.csv", "清洗后原始数据", "保留原始特征与标签，便于核对与画图"]],
    [5.4, 3.4, 7.4], ["left", "left", "left"])
b.spacer(2)
b.body("其中 preprocess_meta.json 记录了特征顺序与类别顺序，推理脚本必须按同一顺序组织输入特征；"
       "顺序错位是「离线指标正常、在线结果异常」最常见的成因。")

# ---------------------------------------------------------------- 三、数据可用性验证
doc.add_paragraph("三、数据可用性验证", style="Heading 1")
b.body("在进入阶段三之前，先用逻辑回归、随机森林与 MLP 三个基线跑通全流程，确认数据管线可用，"
       "并观察指标量级与误差结构，为 1D-CNN 主模型设定合理预期。")

doc.add_paragraph("3.1 实验设置", style="Heading 2")
b.bullet("特征与样本：122 维特征；训练 100,778 条、内部验证 25,195 条、官方测试 22,544 条。")
b.bullet("二分类模型：逻辑回归（类别权重平衡）、随机森林（200 棵树，类别权重平衡）、"
         "MLP（隐藏层 64–32，Adam，学习率 1e-3，批大小 256，早停）。")
b.bullet("五分类模型：随机森林（200 棵树）与 MLP（隐藏层 128–64，其余设置同上）。")
b.bullet("类别加权：MLP 通过样本权重实现类别加权，权重按训练集样本量倒数计算，与随机森林的类别权重口径一致。")
b.bullet("评估：同时在内部验证集与官方测试集 KDDTest+ 上计算准确率、精确率、召回率、F1、误报率与 AUC。")

doc.add_paragraph("3.2 二分类结果", style="Heading 2")
bm = metrics["binary"]
b.table_caption("表 7  二分类模型指标对比")
b.make_table(
    ["模型", "内部验证准确率", "测试集准确率", "精确率", "召回率", "F1", "误报率", "AUC"],
    [[zh, f"{bm[key]['val']['accuracy']:.4f}", f"{bm[key]['test']['accuracy']:.4f}",
      f"{bm[key]['test']['precision']:.4f}", f"{bm[key]['test']['recall']:.4f}",
      f"{bm[key]['test']['f1']:.4f}", f"{bm[key]['test']['fpr']:.4f}",
      f"{bm[key]['test']['roc_auc']:.4f}"]
     for zh, key in [("逻辑回归", "LogisticRegression"), ("随机森林", "RandomForest"),
                     ("MLP", "MLP")]],
    [2.1, 2.5, 2.2, 1.8, 1.7, 1.6, 1.7, 1.6],
    ["left", "right", "right", "right", "right", "right", "right", "right"])
b.spacer(2)
b.figure(os.path.join(FIG_DIR, "fig5_roc_binary.png"), "图 3  二分类 ROC 曲线（KDDTest+）", 9.8)
b.body("表 7 中三个模型依次为逻辑回归、随机森林与三层 MLP，均使用同一套 122 维特征；"
       "「内部验证准确率」一列为 KDDTrain+ 分层抽样得到的 20% 验证集结果。")
b.body("三个模型呈现同一模式：内部验证集接近满分，官方测试集只有 75% 到 79%。随机森林的误报率最低"
       "（2.73%），但召回率只有 62.6%，属于偏保守的判定策略，会漏掉大量攻击；MLP 在两者之间取得较好的"
       "平衡，召回率 68.0%、误报率 6.95%。")
b.body("随机森林的 AUC 达到 0.961，明显高于准确率所反映的水平，说明它的决策分数本身具备很强的区分能力，"
       "短板主要来自默认的 0.5 判定阈值。这提示阶段四除了调整网络结构，还应把「按代价选择阈值」作为一项"
       "独立的优化手段：安全场景通常更看重召回率，适当降低阈值可以把漏报换成可接受的误报增加。")

doc.add_paragraph("3.3 五分类结果", style="Heading 2")
mm = metrics["multi"]["MLP"]["test"]
b.table_caption("表 8  MLP 五分类各类别指标（KDDTest+）")
b.make_table(
    ["类别", "测试集样本数", "精确率", "召回率", "F1"],
    [[c, num(mm["per_class"][c]["support"]), f"{mm['per_class'][c]['precision']:.3f}",
      f"{mm['per_class'][c]['recall']:.3f}", f"{mm['per_class'][c]['f1']:.3f}"]
     for c in ["Normal", "DoS", "Probe", "R2L", "U2R"]] +
    [["整体（macro 平均）", num(sum(mm["per_class"][c]["support"] for c in
                              ["Normal", "DoS", "Probe", "R2L", "U2R"])),
      "—", "—", f"{mm['macro_f1']:.3f}"]],
    [4.8, 3.1, 2.8, 2.8, 2.7], ["left", "right", "right", "right", "right"])
b.spacer(2)
b.body("MLP 五分类整体准确率 82.23%、macro-F1 为 0.631。正常流量与 DoS 的表现接近可用水平（召回率 96.6% 与"
       " 87.6%），Probe 为 72.7%，而 R2L 与 U2R 明显偏低。")
b.body("R2L 的精确率 0.948、召回率只有 0.288：模型一旦判为 R2L 基本正确，但 2,885 条真实 R2L 中有 1,792 条"
       "（62.1%）被误判为正常流量。U2R 只有 67 条测试样本，精确率 0.107，说明报出的 U2R 里约九成是误报，"
       "但召回率 44.8% 已属中等水平。这两类的困难源于样本极少、攻击行为与正常流量高度相似，在公开文献中是"
       "公认难点，如实报告并解释原因比强行拉高数字更有价值。")
b.body("随机森林在五分类上的 macro-F1 仅 0.472，主要原因是它为保证大类精度几乎完全放弃了少数类："
       "R2L 召回率 0.4%、U2R 召回率 1.5%。这说明树模型在不平衡多分类上需要额外的重采样或代价敏感改造，"
       "也说明本项目选取神经网络作为主模型方向是合理的。")
b.figure(os.path.join(FIG_DIR, "fig3_confusion_mlp.png"),
         "图 4  MLP 五分类混淆矩阵（按真实类别归一化）", 11.6)
b.figure(os.path.join(FIG_DIR, "fig6_recall_by_class.png"),
         "图 5  各类别召回率对比（KDDTest+）", 12.8)

doc.add_paragraph("3.4 类别不平衡处理对照实验", style="Heading 2")
b.table_caption("表 9  类别权重与随机过采样的效果对比（MLP 五分类）")
b.make_table(
    ["不平衡处理方案", "测试集准确率", "macro-F1", "R2L 召回率", "U2R 召回率"],
    [["类别权重（本轮采用）", f"{mm['accuracy']:.4f}", f"{mm['macro_f1']:.4f}",
      f"{mm['per_class']['R2L']['recall']:.3f}", f"{mm['per_class']['U2R']['recall']:.3f}"],
     ["随机过采样至每类 6,000 条", f"{over['accuracy']:.4f}", f"{over['macro_f1']:.4f}",
      f"{over['per_class']['R2L']['recall']:.3f}", f"{over['per_class']['U2R']['recall']:.3f}"]],
    [5.0, 2.9, 2.7, 2.8, 2.8], ["left", "right", "right", "right", "right"])
b.spacer(2)
b.body("结果与直觉相反：把 U2R 从 52 条直接复制到 6,000 条后，准确率从 82.23% 降到 76.82%，macro-F1 从"
       " 0.631 降到 0.569，R2L 召回率甚至从 0.288 降到 0.126。原因是简单复制只是让模型记住那 52 条记录，"
       "对未见过的 U2R 攻击没有帮助，反而挤占了大类的学习容量。")
b.body("由此得到两条可执行的结论：当前阶段继续使用类别权重，不引入随机过采样；把重采样留到阶段三的 1D-CNN"
       "主模型上，配合 SMOTE 或 ADASYN 再做一次对照实验，并且比较时必须看 macro-F1 与各类召回率，"
       "而不是只看准确率。")

doc.add_paragraph("3.5 训练过程与过拟合判断", style="Heading 2")
b.figure(os.path.join(FIG_DIR, "fig4_training_curves.png"),
         "图 6  MLP 训练损失与内部验证准确率曲线", 12.6)
b.body(f"二分类 MLP 在 {metrics['binary']['MLP']['epochs_run']} 轮、五分类 MLP 在 "
       f"{metrics['multi']['MLP']['epochs_run']} 轮后触发早停。训练损失持续下降，内部验证准确率趋于平稳，"
       "没有出现「训练损失下降、验证损失上升」的过拟合特征。")
b.body("这说明阶段四的三件套（Dropout、早停、权重衰减）中，早停已经生效；真正的泛化差距出现在官方测试集上，"
       "属于训练分布与测试分布不一致导致的问题，无法通过加深网络或延长训练解决，需要从特征表达与阈值策略入手。")

doc.add_paragraph("3.6 误差来源分析", style="Heading 2")
novel = metrics["novel_attack"]
sel = ["apache2", "mscan", "processtable", "saint", "snmpguess", "snmpgetattack", "mailbomb",
       "httptunnel"]
n_rows = [[k, num(novel["per_type"][k]["count"]), num(novel["per_type"][k]["detected"]),
           pct(novel["per_type"][k]["detected"] / novel["per_type"][k]["count"], 1)] for k in sel]
rest_cnt = novel["rows"] - sum(novel["per_type"][k]["count"] for k in sel)
rest_det = sum(v["detected"] for k, v in novel["per_type"].items() if k not in sel)
n_rows.append(["其余 9 类合计", num(rest_cnt), num(rest_det), pct(rest_det / rest_cnt, 1)])
n_rows.append(["合计", num(novel["rows"]),
               num(sum(v["detected"] for v in novel["per_type"].values())),
               pct(novel["binary_detection_rate"], 1)])
b.table_caption("表 10  训练阶段未见过的攻击类型的二分类检出情况（KDDTest+）")
b.make_table(["攻击类型", "样本数", "被检出数", "检出率"], n_rows,
             [5.0, 3.2, 3.2, 4.8], ["left", "right", "right", "right"])
b.spacer(2)
b.figure(os.path.join(FIG_DIR, "fig7_difficulty.png"),
         "图 7  difficulty 字段取值与基线模型准确率的关系", 15.2)
b.body("模型在 3,750 条未见攻击上的整体二分类检出率为 50.9%。各类型之间分歧很大：snmpguess、mailbomb、"
       "snmpgetattack 的检出率在 97% 以上，因为它们的流量特征与训练集中已有的 R2L 攻击相似；"
       "而 apache2（5.0%）与 saint（1.9%）几乎检测不到，因为它们的行为模式在训练集中没有任何对应样本。")
b.body("这组数字说明模型的主要短板是「识别已知模式」，而不是「发现未知模式」，也解释了为什么二分类与五分类"
       "指标都会在官方测试集上明显下降。阶段五的报告应把未知攻击检出率作为独立小节，并说明要改善这部分需要"
       "无监督的异常检测路线（自编码器）或更贴近真实流量的训练数据。")

doc.add_paragraph("3.7 结论与后续阶段建议", style="Heading 2")
b.table_caption("表 11  验收指标的基线实测值与阶段三、四的迭代目标")
b.make_table(
    ["指标", "方案原目标", "本轮基线实测", "阶段三、四建议目标"],
    [["二分类准确率", "≥ 85%", f"{bm['MLP']['test']['accuracy'] * 100:.1f}%", "≥ 82%"],
     ["二分类 F1", "≥ 0.85", f"{bm['MLP']['test']['f1']:.3f}", "≥ 0.80"],
     ["二分类误报率", "≤ 10%", f"{bm['MLP']['test']['fpr'] * 100:.2f}%", "≤ 6%"],
     ["五分类 macro-F1", "≥ 0.75", f"{mm['macro_f1']:.3f}", "≥ 0.70（1D-CNN）"],
     ["未知攻击检出率", "单独报告", pct(novel["binary_detection_rate"], 1),
      "单独报告并做趋势对比"]],
    [3.4, 3.0, 4.0, 5.8], ["left", "center", "center", "center"])
b.spacer(2)
b.body("阶段三到阶段五的工作可以按以下四条建议展开。")
b.bullet("**数据管线可以直接进入阶段三。**122 维特征对 MLP 与 1D-CNN 都适用，1D-CNN 的输入只需把特征向量"
         " reshape 成 (batch, 1, 122)。")
b.bullet("**主模型选 1D-CNN。**它的目标是在保持正常流量与 DoS 表现的前提下，把 R2L 与 U2R 的召回率提上去，"
         "macro-F1 提高 5 到 7 个百分点即可视为有效改进。")
b.bullet("**类别不平衡继续用类别权重。**SMOTE 或 ADASYN 的对照实验放到 1D-CNN 上做，并固定随机种子保证"
         "可复现。")
b.bullet("**评估坚持双口径并单列未知攻击。**验收看 KDDTest+，同时报告内部验证集数字说明泛化差距；"
         "对未知攻击的检出情况单独成节，这是答辩中很可能被追问的部分。")

# ---------------------------------------------------------------- 四、后续阶段
doc.add_paragraph("四、后续阶段实施要点", style="Heading 1")
b.table_caption("表 12  阶段三至阶段六的关键任务与产出")
b.make_table(
    ["阶段", "关键任务", "里程碑与产出"],
    [["阶段三  模型设计",
      "实现 MLP 基线；实现 1D-CNN 主模型（卷积、池化、全连接结构不超过 80 行）",
      "model.py、模型结构图"],
     ["阶段四  训练与调优",
      "Adam 学习率 1e-3、批大小 128；Dropout、早停、权重衰减；学习率与批大小的小网格搜索",
      "best_model.pth、损失曲线、实验记录表"],
     ["阶段五  模型评估",
      "双口径指标、混淆矩阵、ROC 与 AUC；未知攻击检出率专项；与基线做对比表",
      "evaluate.py、指标对比表与结果分析"],
     ["阶段六  部署集成",
      "先做脚本式准实时检测，再做 Flask 接口与网页仪表盘；录制演示视频",
      "检测演示系统、演示视频、项目仓库"]],
    [3.2, 7.4, 5.6], ["left", "left", "left"])
b.spacer(2)
b.body("时间安排沿用方案中的 6–8 周计划。进入阶段三之前，建议先按表 11 调整验收指标，使目标与 KDDTest+ 的"
       "实际难度匹配，避免用内部验证集的 99% 去对标官方测试集的 78% 而得出错误结论。")

# ---------------------------------------------------------------- 附录 A
doc.add_paragraph("附录 A  41 维特征清单", style="Heading 1")
feat_rows = [
    ("duration", "数值", "连接持续时间（秒）"),
    ("protocol_type", "类别", "协议类型，取值 tcp、udp、icmp"),
    ("service", "类别", "目标端网络服务，训练集共 70 种取值"),
    ("flag", "类别", "连接状态标志，共 11 种取值"),
    ("src_bytes", "数值", "源端发送的字节数"),
    ("dst_bytes", "数值", "目的端发送的字节数"),
    ("land", "数值", "源与目的的地址、端口是否相同"),
    ("wrong_fragment", "数值", "错误分片数量"),
    ("urgent", "数值", "紧急数据包数量"),
    ("hot", "数值", "敏感目录或命令访问等指示器计数"),
    ("num_failed_logins", "数值", "登录失败次数"),
    ("logged_in", "数值", "是否成功登录"),
    ("num_compromised", "数值", "被攻陷相关的条件计数"),
    ("root_shell", "数值", "是否获得 root shell"),
    ("su_attempted", "数值", "是否尝试 su 提权"),
    ("num_root", "数值", "以 root 身份访问的次数"),
    ("num_file_creations", "数值", "创建文件操作次数"),
    ("num_shells", "数值", "打开 shell 的次数"),
    ("num_access_files", "数值", "访问控制文件的次数"),
    ("num_outbound_cmds", "数值", "出站命令次数，该数据集中恒为 0"),
    ("is_host_login", "数值", "是否属于主机登录"),
    ("is_guest_login", "数值", "是否属于访客登录"),
    ("count", "数值", "过去 2 秒内到同一主机的连接数"),
    ("srv_count", "数值", "过去 2 秒内到同一服务的连接数"),
    ("serror_rate", "数值", "同主机连接中 SYN 错误的比例"),
    ("srv_serror_rate", "数值", "同服务连接中 SYN 错误的比例"),
    ("rerror_rate", "数值", "同主机连接中 REJ 错误的比例"),
    ("srv_rerror_rate", "数值", "同服务连接中 REJ 错误的比例"),
    ("same_srv_rate", "数值", "同主机连接中相同服务的比例"),
    ("diff_srv_rate", "数值", "同主机连接中不同服务的比例"),
    ("srv_diff_host_rate", "数值", "同服务连接中不同主机的比例"),
    ("dst_host_count", "数值", "目的主机的连接数"),
    ("dst_host_srv_count", "数值", "目的主机上相同服务的连接数"),
    ("dst_host_same_srv_rate", "数值", "目的主机上相同服务的比例"),
    ("dst_host_diff_srv_rate", "数值", "目的主机上不同服务的比例"),
    ("dst_host_same_src_port_rate", "数值", "目的主机上相同源端口的比例"),
    ("dst_host_srv_diff_host_rate", "数值", "相同服务下不同主机的比例"),
    ("dst_host_serror_rate", "数值", "目的主机的 SYN 错误比例"),
    ("dst_host_srv_serror_rate", "数值", "目的主机相同服务的 SYN 错误比例"),
    ("dst_host_rerror_rate", "数值", "目的主机的 REJ 错误比例"),
    ("dst_host_srv_rerror_rate", "数值", "目的主机相同服务的 REJ 错误比例"),
]
b.table_caption("表 A1  NSL-KDD 的 41 维特征")
b.make_table(["序号", "特征名", "类型", "含义"],
             [[str(i + 1), n, t, d] for i, (n, t, d) in enumerate(feat_rows)],
             [1.4, 6.2, 1.6, 6.8], ["center", "left", "center", "left"], font_size=9)

# ---------------------------------------------------------------- 附录 B
doc.add_paragraph("附录 B  攻击类型到攻击类别的映射", style="Heading 1")
attack_map = [
    ("DoS", ["back", "land", "neptune", "pod", "smurf", "teardrop", "mailbomb", "apache2",
             "processtable", "udpstorm", "worm"]),
    ("Probe", ["satan", "ipsweep", "nmap", "portsweep", "mscan", "saint"]),
    ("R2L", ["guess_passwd", "ftp_write", "imap", "phf", "multihop", "warezmaster",
             "warezclient", "spy", "xlock", "xsnoop", "snmpguess", "snmpgetattack",
             "httptunnel", "sendmail", "named"]),
    ("U2R", ["buffer_overflow", "loadmodule", "rootkit", "perl", "sqlattack", "xterm", "ps"]),
]
tr_t, te_t = meta["train_attack_type_counts"], meta["test_attack_type_counts"]
rows_b = []
for cat, types in attack_map:
    for i, t in enumerate(types):
        rows_b.append([cat if i == 0 else "", t, num(tr_t.get(t, 0)), num(te_t.get(t, 0))])
b.table_caption("表 B1  攻击类型映射与样本分布（训练集 / 测试集）")
b.make_table(["攻击类别", "攻击类型", "训练集样本数", "测试集样本数"], rows_b,
             [2.6, 5.4, 4.1, 4.1], ["left", "left", "right", "right"], font_size=9)
b.spacer(2)
b.body("表中测试集样本数为 0 的类型表示该攻击在训练集中有样本但未出现在官方测试集中；"
       "反向情况（测试集有、训练集没有）已在表 10 中单独列出。")

# ---------------------------------------------------------------- 附录 C
doc.add_paragraph("附录 C  复现说明", style="Heading 1")
b.body("**运行环境。**Python 3.10 及以上版本，依赖 numpy、pandas、scikit-learn、matplotlib 与 joblib。"
       "本报告的统计与实验在 Python 3.14、scikit-learn 1.9.1 上完成，全部为 CPU 计算，"
       "四个基线模型的总训练时间在 3 分钟量级，不需要 GPU。")
b.body("**执行顺序。**按下列顺序运行脚本即可复现全部数字与图表。")
b.table_caption("表 C1  脚本与产物对应关系")
b.make_table(
    ["脚本", "作用", "主要产物"],
    [["step1_explore.py", "统计数据规模、缺失与重复、类别分布", "explore_report.json"],
     ["step2_preprocess.py", "清洗、编码、标准化、划分与类别权重计算",
      "X_*.npy、y_*.npy、encoder.joblib、scaler.joblib"],
     ["step3_baseline.py", "训练三个基线模型并评估，含误差分析", "metrics.json"],
     ["step3b_resample.py", "随机过采样对照实验", "metrics_oversample.json"],
     ["step4_figures.py", "生成报告中的七张图表", "fig 目录下的 PNG 文件"]],
    [4.4, 6.4, 5.4], ["left", "left", "left"], font_size=9)
b.spacer(2)
b.body("**随机性控制。**数据划分、模型初始化与过采样抽样均固定随机种子为 42，重复运行应得到一致结果；"
       "若更换随机种子，指标会有约 1 个百分点以内的波动，比较模型时应固定同一种子。")

doc.save(OUTPUT)
print("saved:", OUTPUT)
