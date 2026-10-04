# -*- coding: utf-8 -*-
"""生成报告用图表。"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(BASE_DIR, "work", "out")
FIG_DIR = os.path.join(BASE_DIR, "work", "fig")
os.makedirs(FIG_DIR, exist_ok=True)

plt.rcParams.update({
    "font.sans-serif": ["Microsoft YaHei", "SimHei", "DejaVu Sans"],
    "axes.unicode_minus": False,
    "font.size": 10.5,
    "axes.edgecolor": "#B8BFC7",
    "axes.labelcolor": "#1F2933",
    "text.color": "#1F2933",
    "xtick.color": "#3E4C59",
    "ytick.color": "#3E4C59",
    "axes.titlesize": 12,
    "figure.dpi": 200,
    "savefig.dpi": 200,
})

CAT_ORDER = ["Normal", "DoS", "Probe", "R2L", "U2R"]
COLORS = {"Normal": "#3D7EA6", "DoS": "#C0504D", "Probe": "#7F9A3C", "R2L": "#7C6BA8",
          "U2R": "#D99100"}

meta = json.load(open(os.path.join(OUT_DIR, "preprocess_meta.json"), encoding="utf-8"))
metrics = json.load(open(os.path.join(OUT_DIR, "metrics.json"), encoding="utf-8"))


def despine(ax):
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)


# ---------- 图 1：五类样本分布（训练集 vs 测试集） ----------
tr = meta["train_category_counts"]
te = meta["test_category_counts"]
x = np.arange(len(CAT_ORDER))
w = 0.38
fig, ax = plt.subplots(figsize=(6.6, 3.3))
b1 = ax.bar(x - w / 2, [tr[c] for c in CAT_ORDER], w, label="训练集 KDDTrain+",
            color="#3D7EA6", edgecolor="white")
b2 = ax.bar(x + w / 2, [te[c] for c in CAT_ORDER], w, label="测试集 KDDTest+",
            color="#9AB8CE", edgecolor="white")
ax.set_yscale("log")
ax.set_xticks(x, CAT_ORDER)
ax.set_ylabel("样本数（对数刻度）")
ax.set_title("五类样本在训练集与测试集中的分布")
for bars in (b1, b2):
    for r in bars:
        ax.annotate(f"{int(r.get_height()):,}", (r.get_x() + r.get_width() / 2, r.get_height()),
                    textcoords="offset points", xytext=(0, 3), ha="center", fontsize=8.5,
                    color="#52606D")
ax.set_ylim(30, 3e5)
ax.legend(frameon=False, ncol=2, loc="upper right")
ax.grid(axis="y", color="#E4E7EB", lw=0.7)
ax.set_axisbelow(True)
despine(ax)
fig.tight_layout()
fig.savefig(os.path.join(FIG_DIR, "fig1_class_distribution.png"))
plt.close(fig)

# ---------- 图 2：攻击类型分布（训练集 vs 测试集，对数横轴） ----------
types = sorted(set(meta["train_attack_type_counts"]) | set(meta["test_attack_type_counts"]))
rows = [{"type": t, "train": meta["train_attack_type_counts"].get(t, 0),
         "test": meta["test_attack_type_counts"].get(t, 0)} for t in types]
tt = pd.DataFrame(rows).sort_values("train", ascending=False).head(14).iloc[::-1]
fig, ax = plt.subplots(figsize=(6.6, 4.5))
y = np.arange(len(tt))
ax.barh(y + 0.2, tt["train"], 0.38, color="#3D7EA6", label="训练集", edgecolor="white")
ax.barh(y - 0.2, tt["test"], 0.38, color="#D99100", label="测试集", edgecolor="white")
ax.set_yticks(y, tt["type"])
ax.set_xscale("log")
ax.set_xlabel("样本数（对数刻度）")
ax.set_title("主要攻击类型样本量对比（按训练集样本量排序，前 14 类）")
ax.legend(frameon=False, loc="lower right")
ax.grid(axis="x", color="#E4E7EB", lw=0.7)
ax.set_axisbelow(True)
despine(ax)
fig.tight_layout()
fig.savefig(os.path.join(FIG_DIR, "fig2_attack_types.png"))
plt.close(fig)

# ---------- 图 3：MLP 五分类混淆矩阵（行归一化） ----------
cm = np.array(metrics["multi"]["MLP"]["test"]["cm"], dtype=float)
cm_norm = cm / cm.sum(axis=1, keepdims=True)
cmap = LinearSegmentedColormap.from_list("ids", ["#FFFFFF", "#BFD7E6", "#3D7EA6", "#1F4E68"])
fig, ax = plt.subplots(figsize=(5.6, 4.5))
im = ax.imshow(cm_norm, cmap=cmap, vmin=0, vmax=1)
ax.set_xticks(range(5), CAT_ORDER)
ax.set_yticks(range(5), CAT_ORDER)
ax.set_xlabel("预测类别")
ax.set_ylabel("真实类别")
ax.set_title("MLP 五分类混淆矩阵（按真实类别归一化）")
for i in range(5):
    for j in range(5):
        val = cm_norm[i, j]
        ax.text(j, i, f"{val*100:.1f}%\n({int(cm[i, j]):,})", ha="center", va="center",
                fontsize=8.2, color="white" if val > 0.55 else "#1F2933")
cb = fig.colorbar(im, ax=ax, fraction=0.045, pad=0.03)
cb.set_label("占真实类别比例")
cb.outline.set_visible(False)
fig.tight_layout()
fig.savefig(os.path.join(FIG_DIR, "fig3_confusion_mlp.png"))
plt.close(fig)

# ---------- 图 4：MLP 训练过程曲线 ----------
fig, axes = plt.subplots(1, 2, figsize=(6.8, 2.9))
for key, label, color in (("binary", "二分类", "#3D7EA6"), ("multi", "五分类", "#C0504D")):
    axes[0].plot(range(1, len(metrics[key]["MLP"]["loss_curve"]) + 1),
                 metrics[key]["MLP"]["loss_curve"], color=color, lw=1.8, label=label)
    axes[1].plot(range(1, len(metrics[key]["MLP"]["val_score_curve"]) + 1),
                 metrics[key]["MLP"]["val_score_curve"], color=color, lw=1.8, label=label)
axes[0].set_xlabel("迭代轮次")
axes[0].set_ylabel("训练损失")
axes[0].set_title("训练损失曲线")
axes[1].set_xlabel("迭代轮次")
axes[1].set_ylabel("内部验证准确率")
axes[1].set_title("内部验证准确率曲线")
for ax in axes:
    ax.grid(color="#E4E7EB", lw=0.7)
    ax.set_axisbelow(True)
    despine(ax)
    ax.legend(frameon=False, fontsize=9)
fig.tight_layout()
fig.savefig(os.path.join(FIG_DIR, "fig4_training_curves.png"))
plt.close(fig)

# ---------- 图 5：二分类 ROC 曲线 ----------
fig, ax = plt.subplots(figsize=(4.9, 4.2))
style = {"LogisticRegression": ("逻辑回归", "#9AB8CE"), "RandomForest": ("随机森林", "#7F9A3C"),
         "MLP": ("MLP", "#3D7EA6")}
for name, (label, color) in style.items():
    d = metrics["binary"][name]["test"]
    ax.plot(d["roc"]["fpr"], d["roc"]["tpr"], color=color, lw=1.8,
            label=f"{label}（AUC={d['roc_auc']:.3f}）")
ax.plot([0, 1], [0, 1], "--", color="#B8BFC7", lw=1)
ax.set_xlabel("误报率 FPR")
ax.set_ylabel("检测率 TPR")
ax.set_title("二分类 ROC 曲线（KDDTest+）")
ax.legend(frameon=False, fontsize=8.8, loc="lower right")
ax.grid(color="#E4E7EB", lw=0.7)
ax.set_axisbelow(True)
despine(ax)
fig.tight_layout()
fig.savefig(os.path.join(FIG_DIR, "fig5_roc_binary.png"))
plt.close(fig)

# ---------- 图 6：各类别召回率对比 ----------
fig, ax = plt.subplots(figsize=(6.6, 3.2))
x = np.arange(len(CAT_ORDER))
w = 0.38
rf_recall = [metrics["multi"]["RandomForest"]["test"]["per_class"][c]["recall"] for c in CAT_ORDER]
mlp_recall = [metrics["multi"]["MLP"]["test"]["per_class"][c]["recall"] for c in CAT_ORDER]
ax.bar(x - w / 2, rf_recall, w, color="#7F9A3C", label="随机森林", edgecolor="white")
ax.bar(x + w / 2, mlp_recall, w, color="#3D7EA6", label="MLP", edgecolor="white")
for xi, v in zip(x - w / 2, rf_recall):
    ax.annotate(f"{v:.3f}", (xi, v), textcoords="offset points", xytext=(0, 3), ha="center",
                fontsize=8.2, color="#52606D")
for xi, v in zip(x + w / 2, mlp_recall):
    ax.annotate(f"{v:.3f}", (xi, v), textcoords="offset points", xytext=(0, 3), ha="center",
                fontsize=8.2, color="#52606D")
ax.set_xticks(x, CAT_ORDER)
ax.set_ylabel("召回率（检测率）")
ax.set_ylim(0, 1.12)
ax.set_title("各类别召回率对比（KDDTest+）")
ax.legend(frameon=False, ncol=2, loc="upper right")
ax.grid(axis="y", color="#E4E7EB", lw=0.7)
ax.set_axisbelow(True)
despine(ax)
fig.tight_layout()
fig.savefig(os.path.join(FIG_DIR, "fig6_recall_by_class.png"))
plt.close(fig)

# ---------- 图 7：difficulty 字段与模型准确率 ----------
rows = metrics["difficulty_analysis"]["rows"]
lv = [r[0] for r in rows]
multi_acc = [r[1] for r in rows]
binary_acc = [r[3] for r in rows]
cnt = [r[2] for r in rows]
fig, ax = plt.subplots(figsize=(6.6, 2.9))
ax2 = ax.twinx()
ax2.bar(lv, cnt, color="#E4E7EB", width=0.75, label="样本数量", zorder=1)
ax.plot(lv, binary_acc, "-o", ms=3.4, color="#3D7EA6", lw=1.6, label="二分类准确率", zorder=3)
ax.plot(lv, multi_acc, "-o", ms=3.4, color="#C0504D", lw=1.6, label="五分类准确率", zorder=3)
ax.set_xlabel("difficulty 字段取值")
ax.set_ylabel("准确率")
ax2.set_ylabel("样本数量", color="#7B8794")
ax.set_ylim(0, 1.05)
ax2.set_ylim(0, max(cnt) * 1.5)
ax.set_xticks(lv, [str(v) for v in lv], fontsize=8)
h1, l1 = ax.get_legend_handles_labels()
h2, l2 = ax2.get_legend_handles_labels()
ax.legend(h1 + h2, l1 + l2, frameon=False, fontsize=9, loc="upper left")
ax.set_title("difficulty 字段取值与基线模型准确率的关系")
ax.grid(color="#E4E7EB", lw=0.7)
ax.set_axisbelow(True)
despine(ax)
ax2.spines["top"].set_visible(False)
fig.tight_layout()
fig.savefig(os.path.join(FIG_DIR, "fig7_difficulty.png"))
plt.close(fig)

print("\n".join(sorted(os.listdir(FIG_DIR))))
