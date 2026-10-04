# -*- coding: utf-8 -*-
"""按方案阶段 5 在官方测试集 KDDTest+ 上评估 PyTorch 1D-CNN，
并与 step3 的 sklearn 基线（LR / RF / MLP）对比。
产出：out/metrics_cnn.json、fig/fig8_cnn_training_curves.png、fig/fig9_cnn_confusion.png。
"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch
from sklearn.metrics import (accuracy_score, confusion_matrix, f1_score,
                             precision_recall_fscore_support, roc_auc_score)

from step6_cnn_model import CNN1D

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(BASE_DIR, "work", "out")
FIG_DIR = os.path.join(BASE_DIR, "work", "fig")
os.makedirs(FIG_DIR, exist_ok=True)
CAT_ORDER = ["Normal", "DoS", "Probe", "R2L", "U2R"]

plt.rcParams.update({"font.sans-serif": ["Microsoft YaHei", "SimHei", "DejaVu Sans"],
                     "axes.unicode_minus": False, "savefig.dpi": 200})
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def load(name):
    return np.load(os.path.join(OUT_DIR, name))


def load_model(tag):
    ckpt = torch.load(os.path.join(OUT_DIR, f"cnn_{tag}_best.pth"), map_location=device,
                      weights_only=False)
    model = CNN1D(input_dim=ckpt["input_dim"], num_classes=ckpt["num_classes"]).to(device)
    model.load_state_dict(ckpt["model_state_dict"])
    model.eval()
    return model


def predict(model, X, batch=4096):
    outs = []
    with torch.no_grad():
        for i in range(0, len(X), batch):
            xb = torch.from_numpy(X[i:i + batch]).to(device)
            outs.append(torch.softmax(model(xb), dim=1).cpu().numpy())
    return np.concatenate(outs)


X_te = load("X_test.npy")
results = {}

# ---------------- 二分类 ----------------
prob_b = predict(load_model("binary"), X_te)[:, 1]
y_te_b, y_pr_b = load("y_test_binary.npy"), (prob_b >= 0.5).astype(int)
tn, fp, fn, tp = confusion_matrix(y_te_b, y_pr_b, labels=[0, 1]).ravel()
results["binary"] = {
    "accuracy": float(accuracy_score(y_te_b, y_pr_b)),
    "precision": float(tp / (tp + fp)), "recall": float(tp / (tp + fn)),
    "f1": float(2 * tp / (2 * tp + fp + fn)), "fpr": float(fp / (fp + tn)),
    "roc_auc": float(roc_auc_score(y_te_b, prob_b)),
    "cm": [[int(tn), int(fp)], [int(fn), int(tp)]],
}

# ---------------- 五分类 ----------------
prob_m = predict(load_model("multi"), X_te)
y_te_m, y_pr_m = load("y_test_multi.npy"), prob_m.argmax(1)
p, r, f, s = precision_recall_fscore_support(y_te_m, y_pr_m, labels=range(5),
                                             zero_division=0)
results["multi"] = {
    "accuracy": float(accuracy_score(y_te_m, y_pr_m)),
    "macro_f1": float(f1_score(y_te_m, y_pr_m, average="macro", zero_division=0)),
    "weighted_f1": float(f1_score(y_te_m, y_pr_m, average="weighted", zero_division=0)),
    "per_class": {CAT_ORDER[i]: {"precision": float(p[i]), "recall": float(r[i]),
                                 "f1": float(f[i]), "support": int(s[i])}
                  for i in range(5)},
    "cm": confusion_matrix(y_te_m, y_pr_m, labels=range(5)).tolist(),
}

# ---------------- 与 sklearn 基线对比 ----------------
base = json.load(open(os.path.join(OUT_DIR, "metrics.json"), encoding="utf-8"))
results["comparison"] = {
    "binary_test": {
        "LR":  {k: round(base["binary"]["LogisticRegression"]["test"][k], 4)
                for k in ("accuracy", "f1", "fpr")},
        "RF":  {k: round(base["binary"]["RandomForest"]["test"][k], 4)
                for k in ("accuracy", "f1", "fpr")},
        "sklearn_MLP": {k: round(base["binary"]["MLP"]["test"][k], 4)
                        for k in ("accuracy", "f1", "fpr")},
        "CNN1D": {k: round(results["binary"][k], 4) for k in ("accuracy", "f1", "fpr")},
    },
    "multi_test": {
        "RF":  {k: round(base["multi"]["RandomForest"]["test"][k], 4)
                for k in ("accuracy", "macro_f1")},
        "sklearn_MLP": {k: round(base["multi"]["MLP"]["test"][k], 4)
                        for k in ("accuracy", "macro_f1")},
        "CNN1D": {k: round(results["multi"][k], 4) for k in ("accuracy", "macro_f1")},
    },
}

with open(os.path.join(OUT_DIR, "metrics_cnn.json"), "w", encoding="utf-8") as fp_:
    json.dump(results, fp_, ensure_ascii=False, indent=2)

# ---------------- 图 8：训练曲线 ----------------
hist = json.load(open(os.path.join(OUT_DIR, "cnn_history.json"), encoding="utf-8"))
fig, axes = plt.subplots(1, 2, figsize=(11, 4))
for ax, tag, title in zip(axes, ("binary", "multi"), ("二分类", "五分类")):
    h = hist[tag]
    ax.plot(h["train_loss"], label="train loss")
    ax.plot(h["val_loss"], label="val loss")
    ax2 = ax.twinx()
    ax2.plot(h["val_acc"], color="#639922", ls="--", alpha=0.7, label="val acc")
    ax2.set_ylabel("val acc")
    ax.set_xlabel("epoch"); ax.set_ylabel("loss")
    ax.set_title(f"1D-CNN {title}训练曲线")
    ax.legend(loc="upper right")
fig.tight_layout()
fig.savefig(os.path.join(FIG_DIR, "fig8_cnn_training_curves.png"))
plt.close(fig)

# ---------------- 图 9：混淆矩阵 ----------------
fig, axes = plt.subplots(1, 2, figsize=(11, 4.6))
for ax, cm, labels, title in (
        (axes[0], results["binary"]["cm"], ["normal", "attack"], "二分类"),
        (axes[1], results["multi"]["cm"], CAT_ORDER, "五分类")):
    cm = np.array(cm)
    im = ax.imshow(cm, cmap="Blues")
    ax.set_xticks(range(len(labels)), labels)
    ax.set_yticks(range(len(labels)), labels)
    ax.set_xlabel("predicted"); ax.set_ylabel("true")
    ax.set_title(f"1D-CNN {title}混淆矩阵（KDDTest+）")
    for i in range(len(labels)):
        for j in range(len(labels)):
            ax.text(j, i, cm[i, j], ha="center", va="center", fontsize=8,
                    color="white" if cm[i, j] > cm.max() / 2 else "black")
    fig.colorbar(im, ax=ax, fraction=0.046)
fig.tight_layout()
fig.savefig(os.path.join(FIG_DIR, "fig9_cnn_confusion.png"))
plt.close(fig)

print(json.dumps(results["comparison"], ensure_ascii=False, indent=2))
print("binary:", {k: round(v, 4) for k, v in results["binary"].items() if k != "cm"})
print("multi macro_f1:", round(results["multi"]["macro_f1"], 4),
      "| acc:", round(results["multi"]["accuracy"], 4))
print("figures saved ->", FIG_DIR)
