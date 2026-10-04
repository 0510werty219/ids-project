# 基于深度学习的入侵检测系统（IDS）

基于 NSL-KDD 数据集的网络入侵检测系统课程项目：数据预处理 → sklearn 基线 → PyTorch 1D-CNN 主模型 → 评估对比 → 网页实时检测演示。

## 环境

- Python 3.10+（开发机使用 3.11）
- 安装依赖：`pip install -r requirements.txt`（全部为免费开源库，无需 GPU，CPU 即可运行）

## 目录结构

```
ids/
├── README.md / requirements.txt
├── IDS分阶段实现方案.md                        # 项目总体方案
├── 基于深度学习的入侵检测系统需求说明书与数据准备报告.docx  # 阶段 1-2 报告
├── data/b4986-main/NSL-KDD/NSL-KDD/            # NSL-KDD 数据集（txt 原始文件）
├── work/                                       # 代码与实验产物
│   ├── step1_explore.py                        # 数据探查 -> out/explore_report.json
│   ├── step2_preprocess.py                     # 预处理 -> out/*.npy, encoder/scaler.joblib
│   ├── step3_baseline.py                       # sklearn 基线 LR/RF/MLP -> out/metrics.json
│   ├── step3b_resample.py                      # 过采样对照实验 -> out/metrics_oversample.json
│   ├── step4_figures.py                        # 报告图表 -> fig/fig1-7
│   ├── step5_build_docx.py                     # 生成阶段 1-2 Word 报告
│   ├── step6_cnn_model.py                      # PyTorch 1D-CNN / MLP 模型定义
│   ├── step7_train_cnn.py                      # CNN 训练（类别权重+早停+保存最优权重）
│   ├── step8_evaluate_cnn.py                   # CNN 测试集评估 + 与基线对比 + 图表
│   ├── out/                                    # 数据产物、指标、模型权重
│   └── fig/                                    # 全部图表
└── deploy/                                     # 阶段 6：网页实时检测演示
    ├── app.py                                  # 推理服务（仅标准库，无需安装 Flask）
    └── index.html                              # 演示页面
```

## 运行顺序

```bash
cd work
python step1_explore.py        # 数据探查
python step2_preprocess.py     # 预处理（生成 122 维特征 .npy）
python step3_baseline.py       # sklearn 基线（约 5-10 分钟）
python step3b_resample.py      # 可选：过采样对照实验
python step4_figures.py        # 生成报告图表
python step5_build_docx.py     # 可选：重新生成 Word 报告（需 python-docx）
python step7_train_cnn.py      # 训练 1D-CNN（二分类+五分类，CPU 约 30 分钟）
python step8_evaluate_cnn.py   # 测试集评估 + 与基线对比 + 图 8/9
python step9_binary_threshold.py  # 可选：二分类阈值调优实验
```

## 实时检测演示（阶段 6）

```bash
cd deploy
python app.py
# 浏览器打开 http://127.0.0.1:5000 ，点击"开始"即可看到流量逐条检测、攻击红色告警
```

## 主要结果（KDDTest+ 官方测试集）

| 模型 | 二分类 Acc | 二分类 F1 | 二分类 FPR | 五分类 Acc | 五分类 macro-F1 |
|---|---|---|---|---|---|
| Logistic 回归 | 0.754 | 0.744 | 7.5% | — | — |
| 随机森林 | 0.775 | 0.760 | 2.7% | 0.737 | 0.472 |
| sklearn MLP | 0.788 | 0.785 | 6.6% | 0.822 | 0.631 |
| **1D-CNN（本方案主模型）** | 0.745 | 0.730 | 7.3% | 0.768 | 0.613 |

完整实验记录见 `work/EXPERIMENTS.md`；详细指标见 `work/out/metrics.json` 与 `work/out/metrics_cnn.json`。

注：NSL-KDD 测试集包含 17 种训练集中未出现的攻击（3750 条），是业内公认的难测试集；
R2L / U2R 类召回率偏低为该数据集普遍现象，详见报告中的误差分析。
