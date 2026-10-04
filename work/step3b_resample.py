# -*- coding: utf-8 -*-
"""对照实验：随机过采样（SMOTE 的简化替代）对少数类召回率的影响。"""
import json
import os
import time

import numpy as np
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score
from sklearn.neural_network import MLPClassifier

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(BASE_DIR, "work", "out")
CAT_ORDER = ["Normal", "DoS", "Probe", "R2L", "U2R"]
RNG = np.random.default_rng(42)

X_tr = np.load(os.path.join(OUT_DIR, "X_train.npy"))
X_te = np.load(os.path.join(OUT_DIR, "X_test.npy"))
y_tr = np.load(os.path.join(OUT_DIR, "y_train_multi.npy"))
y_te = np.load(os.path.join(OUT_DIR, "y_test_multi.npy"))

TARGET = 6000  # 每个类别的目标样本量
idx_parts = []
for c in range(len(CAT_ORDER)):
    idx = np.where(y_tr == c)[0]
    if len(idx) >= TARGET:
        idx_parts.append(idx)
    else:
        idx_parts.append(RNG.choice(idx, size=TARGET, replace=True))
idx = np.concatenate(idx_parts)
RNG.shuffle(idx)
X_res, y_res = X_tr[idx], y_tr[idx]

t0 = time.time()
clf = MLPClassifier(hidden_layer_sizes=(128, 64), activation="relu", batch_size=256,
                    learning_rate_init=1e-3, max_iter=80, early_stopping=True,
                    n_iter_no_change=6, validation_fraction=0.1,
                    random_state=42).fit(X_res, y_res)
print(f"oversampled MLP trained in {time.time() - t0:.1f}s, epochs={clf.n_iter_}")

pred = clf.predict(X_te)
from sklearn.metrics import precision_recall_fscore_support
p, r, f, s = precision_recall_fscore_support(y_te, pred, labels=range(5), zero_division=0)
out = {
    "resampled_train_size": int(X_res.shape[0]),
    "epochs": int(clf.n_iter_),
    "accuracy": float(accuracy_score(y_te, pred)),
    "macro_f1": float(f1_score(y_te, pred, average="macro", zero_division=0)),
    "per_class": {CAT_ORDER[i]: {"precision": float(p[i]), "recall": float(r[i]),
                                 "f1": float(f[i]), "support": int(s[i])} for i in range(5)},
    "cm": confusion_matrix(y_te, pred, labels=range(5)).tolist(),
}
json.dump(out, open(os.path.join(OUT_DIR, "metrics_oversample.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)
print(json.dumps({"acc": round(out["accuracy"], 4), "macro_f1": round(out["macro_f1"], 4),
                  "recall": {k: round(v["recall"], 3) for k, v in out["per_class"].items()}},
                 ensure_ascii=False))
