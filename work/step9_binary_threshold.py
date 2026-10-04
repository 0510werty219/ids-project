# -*- coding: utf-8 -*-
"""二分类判定阈值调优：在验证集上搜索使 F1 最大的阈值，再应用到测试集。
 IDS 场景常需要在"误报/漏报"之间权衡，默认 0.5 阈值不一定最优。
结果追加写入 out/metrics_cnn.json 的 binary_threshold_tuned 字段。
"""
import json
import os

import numpy as np
import torch
from sklearn.metrics import accuracy_score, confusion_matrix, roc_auc_score

from step6_cnn_model import CNN1D

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(BASE_DIR, "work", "out")
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

ckpt = torch.load(os.path.join(OUT_DIR, "cnn_binary_best.pth"), map_location=device,
                  weights_only=False)
model = CNN1D(input_dim=ckpt["input_dim"], num_classes=ckpt["num_classes"]).to(device)
model.load_state_dict(ckpt["model_state_dict"])
model.eval()


def probs(X, batch=8192):
    outs = []
    with torch.no_grad():
        for i in range(0, len(X), batch):
            xb = torch.from_numpy(X[i:i + batch]).to(device)
            outs.append(torch.softmax(model(xb), dim=1)[:, 1].cpu().numpy())
    return np.concatenate(outs)


def metrics_at(y_true, prob, thr):
    pred = (prob >= thr).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, pred, labels=[0, 1]).ravel()
    return {
        "threshold": round(float(thr), 3),
        "accuracy": float(accuracy_score(y_true, pred)),
        "precision": float(tp / (tp + fp)) if tp + fp else 0.0,
        "recall": float(tp / (tp + fn)) if tp + fn else 0.0,
        "f1": float(2 * tp / (2 * tp + fp + fn)) if 2 * tp + fp + fn else 0.0,
        "fpr": float(fp / (fp + tn)) if fp + tn else 0.0,
    }


val_prob = probs(np.load(os.path.join(OUT_DIR, "X_val.npy")))
y_val = np.load(os.path.join(OUT_DIR, "y_val_binary.npy"))
test_prob = probs(np.load(os.path.join(OUT_DIR, "X_test.npy")))
y_test = np.load(os.path.join(OUT_DIR, "y_test_binary.npy"))

# 在验证集上搜索最优 F1 阈值
best = max((metrics_at(y_val, val_prob, t) for t in np.arange(0.05, 0.95, 0.01)),
           key=lambda m: m["f1"])
thr = best["threshold"]
print(f"验证集最优阈值: {thr} (val F1={best['f1']:.4f})")

tuned = metrics_at(y_test, test_prob, thr)
tuned["roc_auc"] = float(roc_auc_score(y_test, test_prob))
tuned["val_best_threshold"] = thr
print("测试集（调阈值后）:", {k: round(v, 4) for k, v in tuned.items()})

path = os.path.join(OUT_DIR, "metrics_cnn.json")
data = json.load(open(path, encoding="utf-8"))
data["binary_threshold_tuned"] = tuned
json.dump(data, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("已追加写入 metrics_cnn.json -> binary_threshold_tuned")
