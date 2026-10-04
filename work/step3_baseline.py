# -*- coding: utf-8 -*-
"""按方案阶段 3-5 的路线跑基线模型（LogisticRegression / RandomForest / MLP），
在官方测试集 KDDTest+ 上评估，输出指标 JSON、混淆矩阵与 ROC 数据。"""
import json
import os
import time

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, confusion_matrix, f1_score,
                             precision_recall_fscore_support, roc_auc_score, roc_curve)
from sklearn.neural_network import MLPClassifier

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(BASE_DIR, "work", "out")
CAT_ORDER = ["Normal", "DoS", "Probe", "R2L", "U2R"]


def load(name):
    return np.load(os.path.join(OUT_DIR, name))


X_tr, X_val, X_te = load("X_train.npy"), load("X_val.npy"), load("X_test.npy")
y_tr_m, y_val_m, y_te_m = (load("y_train_multi.npy"), load("y_val_multi.npy"),
                           load("y_test_multi.npy"))
y_tr_b, y_val_b, y_te_b = (load("y_train_binary.npy"), load("y_val_binary.npy"),
                           load("y_test_binary.npy"))

meta = json.load(open(os.path.join(OUT_DIR, "preprocess_meta.json"), encoding="utf-8"))
N_CLASS = len(CAT_ORDER)


def sample_weights_from_class(y, n_classes):
    counts = np.bincount(y, minlength=n_classes).astype(float)
    w = len(y) / (n_classes * np.maximum(counts, 1))
    return w[y]


def binary_metrics(y_true, y_pred, y_prob=None):
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel()
    out = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(tp / (tp + fp)) if (tp + fp) else 0.0,
        "recall": float(tp / (tp + fn)) if (tp + fn) else 0.0,
        "f1": float(2 * tp / (2 * tp + fp + fn)) if (2 * tp + fp + fn) else 0.0,
        "fpr": float(fp / (fp + tn)) if (fp + tn) else 0.0,
        "cm": cm.tolist(),
    }
    if y_prob is not None:
        out["roc_auc"] = float(roc_auc_score(y_true, y_prob))
        fpr, tpr, _ = roc_curve(y_true, y_prob)
        idx = np.linspace(0, len(fpr) - 1, 60).astype(int)
        out["roc"] = {"fpr": fpr[idx].tolist(), "tpr": tpr[idx].tolist()}
    return out


def multi_metrics(y_true, y_pred):
    p, r, f, s = precision_recall_fscore_support(y_true, y_pred, labels=range(N_CLASS),
                                                 zero_division=0)
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "weighted_f1": float(f1_score(y_true, y_pred, average="weighted", zero_division=0)),
        "per_class": {
            CAT_ORDER[i]: {
                "precision": float(p[i]), "recall": float(r[i]), "f1": float(f[i]),
                "support": int(s[i]),
            } for i in range(N_CLASS)
        },
        "cm": confusion_matrix(y_true, y_pred, labels=range(N_CLASS)).tolist(),
    }


results = {}


def timed(label, fn):
    t0 = time.time()
    value = fn()
    print(f"[{label}] done in {time.time() - t0:.1f}s", flush=True)
    return value


sample_w_b = sample_weights_from_class(y_tr_b, 2)
sample_w_m = sample_weights_from_class(y_tr_m, N_CLASS)

# ---------------- 二分类 ----------------
results["binary"] = {}

lr_b = timed("LR binary", lambda: LogisticRegression(max_iter=500, class_weight="balanced",
                                                     n_jobs=-1).fit(X_tr, y_tr_b))
results["binary"]["LogisticRegression"] = {
    "val": binary_metrics(y_val_b, lr_b.predict(X_val), lr_b.predict_proba(X_val)[:, 1]),
    "test": binary_metrics(y_te_b, lr_b.predict(X_te), lr_b.predict_proba(X_te)[:, 1]),
}

rf_b = timed("RF binary", lambda: RandomForestClassifier(
    n_estimators=200, class_weight="balanced_subsample", n_jobs=-1,
    random_state=42).fit(X_tr, y_tr_b))
results["binary"]["RandomForest"] = {
    "val": binary_metrics(y_val_b, rf_b.predict(X_val), rf_b.predict_proba(X_val)[:, 1]),
    "test": binary_metrics(y_te_b, rf_b.predict(X_te), rf_b.predict_proba(X_te)[:, 1]),
}

mlp_b = timed("MLP binary", lambda: MLPClassifier(
    hidden_layer_sizes=(64, 32), activation="relu", batch_size=256, learning_rate_init=1e-3,
    max_iter=60, early_stopping=True, n_iter_no_change=5, validation_fraction=0.1,
    random_state=42).fit(X_tr, y_tr_b, sample_weight=sample_w_b))
results["binary"]["MLP"] = {
    "epochs_run": int(mlp_b.n_iter_),
    "loss_curve": [float(v) for v in mlp_b.loss_curve_],
    "val_score_curve": [float(v) for v in mlp_b.validation_scores_],
    "val": binary_metrics(y_val_b, mlp_b.predict(X_val), mlp_b.predict_proba(X_val)[:, 1]),
    "test": binary_metrics(y_te_b, mlp_b.predict(X_te), mlp_b.predict_proba(X_te)[:, 1]),
}

# ---------------- 五分类 ----------------
results["multi"] = {}

rf_m = timed("RF multi", lambda: RandomForestClassifier(
    n_estimators=200, class_weight="balanced_subsample", n_jobs=-1,
    random_state=42).fit(X_tr, y_tr_m))
results["multi"]["RandomForest"] = {
    "val": multi_metrics(y_val_m, rf_m.predict(X_val)),
    "test": multi_metrics(y_te_m, rf_m.predict(X_te)),
}

mlp_m = timed("MLP multi", lambda: MLPClassifier(
    hidden_layer_sizes=(128, 64), activation="relu", batch_size=256, learning_rate_init=1e-3,
    max_iter=80, early_stopping=True, n_iter_no_change=6, validation_fraction=0.1,
    random_state=42).fit(X_tr, y_tr_m, sample_weight=sample_w_m))
results["multi"]["MLP"] = {
    "epochs_run": int(mlp_m.n_iter_),
    "loss_curve": [float(v) for v in mlp_m.loss_curve_],
    "val_score_curve": [float(v) for v in mlp_m.validation_scores_],
    "val": multi_metrics(y_val_m, mlp_m.predict(X_val)),
    "test": multi_metrics(y_te_m, mlp_m.predict(X_te)),
}

# ---------------- 误差分析 ----------------
test_raw = pd.read_csv(os.path.join(OUT_DIR, "clean_test.csv"), encoding="utf-8")
test_raw["pred_multi"] = mlp_m.predict(X_te)
test_raw["pred_binary"] = mlp_b.predict(X_te)
test_raw["correct_multi"] = (test_raw["pred_multi"] == test_raw["label_multi"]).astype(int)
test_raw["correct_binary"] = (test_raw["pred_binary"] == test_raw["label_binary"]).astype(int)

diff_table = test_raw.groupby("difficulty").agg(
    multi_accuracy=("correct_multi", "mean"), count=("correct_multi", "size"),
    binary_accuracy=("correct_binary", "mean"))
results["difficulty_analysis"] = {
    "header": ["difficulty", "multi_accuracy", "count", "binary_accuracy"],
    "rows": [[int(i), round(float(r.multi_accuracy), 4), int(r["count"]),
              round(float(r.binary_accuracy), 4)] for i, r in diff_table.iterrows()],
}

known_attacks = set(meta["train_attack_type_counts"].keys())
test_raw["is_novel"] = test_raw["label"].apply(lambda x: x != "normal" and x not in known_attacks)
novel = test_raw[test_raw["is_novel"]]
results["novel_attack"] = {
    "rows": int(novel.shape[0]),
    "binary_detection_rate": round(float(1 - novel["correct_binary"].mean()), 4) if len(novel) else None,
    "per_type": {
        k: {"count": int(g.shape[0]), "detected": int((g["correct_binary"] == 0).sum())}
        for k, g in novel.groupby("label")
    },
}

importances = rf_m.feature_importances_
names = meta["feature_names"]
order = np.argsort(importances)[::-1][:15]
results["feature_importance_top15"] = [
    {"feature": names[i], "importance": round(float(importances[i]), 4)} for i in order
]

results["runtime_note"] = {
    "n_features": int(X_tr.shape[1]),
    "n_train": int(X_tr.shape[0]),
    "n_val": int(X_val.shape[0]),
    "n_test": int(X_te.shape[0]),
}

with open(os.path.join(OUT_DIR, "metrics.json"), "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(json.dumps({
    "binary_test_acc": {k: round(v["test"]["accuracy"], 4) for k, v in results["binary"].items()},
    "binary_test_f1": {k: round(v["test"]["f1"], 4) for k, v in results["binary"].items()},
    "multi_test_acc": {k: round(v["test"]["accuracy"], 4) for k, v in results["multi"].items()},
    "multi_test_macroF1": {k: round(v["test"]["macro_f1"], 4) for k, v in results["multi"].items()},
}, ensure_ascii=False, indent=2))
