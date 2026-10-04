# -*- coding: utf-8 -*-
"""按方案阶段 2 执行 NSL-KDD 预处理：
去重检查 -> 类别特征 One-Hot -> 数值特征标准化(仅用训练集拟合) -> 标签编码 -> 类别权重。
输出可直接喂给模型的 .npy 数据与可复用的编码器 / 标准化器。
"""
import json
import os

import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.utils.class_weight import compute_class_weight

from step1_explore import (ATTACK_CATEGORY, CATEGORICAL, COLUMNS, DATA_DIR, FILES,
                           to_category)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(BASE_DIR, "work", "out")
os.makedirs(OUT_DIR, exist_ok=True)


def load(name):
    return pd.read_csv(os.path.join(DATA_DIR, FILES[name]), header=None, names=COLUMNS)


train = load("KDDTrain+")
test = load("KDDTest+")

# ---------- 1. 清洗检查 ----------
clean_stats = {}
for name, df in (("train", train), ("test", test)):
    dup = int(df.drop(columns=["difficulty"]).duplicated().sum())
    df.drop_duplicates(subset=[c for c in COLUMNS if c != "difficulty"], inplace=True)
    clean_stats[name] = {
        "rows_after_dedup": int(df.shape[0]),
        "duplicate_rows_removed": dup,
        "missing_cells": int(df.isna().sum().sum()),
        "inf_cells": int(np.isinf(df.drop(columns=CATEGORICAL + ["label"]).to_numpy(
            dtype="float64", na_value=np.nan)).sum()),
    }

# ---------- 2. 标签编码 ----------
train["label_binary"] = (train["label"] != "normal").astype(int)
test["label_binary"] = (test["label"] != "normal").astype(int)
train["label_cat"] = train["label"].map(to_category)
test["label_cat"] = test["label"].map(to_category)

CAT_ORDER = ["Normal", "DoS", "Probe", "R2L", "U2R"]
cat_to_idx = {c: i for i, c in enumerate(CAT_ORDER)}
train["label_multi"] = train["label_cat"].map(cat_to_idx).astype(int)
test["label_multi"] = test["label_cat"].map(cat_to_idx).astype(int)

# ---------- 3. 类别特征 One-Hot（仅用训练集拟合词表） ----------
encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=False, dtype=np.float32)
encoder.fit(train[CATEGORICAL])
cat_names = list(encoder.get_feature_names_out(CATEGORICAL))

train_cat = pd.DataFrame(encoder.transform(train[CATEGORICAL]), columns=cat_names,
                         index=train.index)
test_cat = pd.DataFrame(encoder.transform(test[CATEGORICAL]), columns=cat_names,
                        index=test.index)

# ---------- 4. 数值特征标准化（仅用训练集拟合） ----------
numeric_cols = [c for c in COLUMNS if c not in CATEGORICAL + ["label", "difficulty"]]
scaler = StandardScaler()
scaler.fit(train[numeric_cols])
train_num = pd.DataFrame(scaler.transform(train[numeric_cols]), columns=numeric_cols,
                         index=train.index)
test_num = pd.DataFrame(scaler.transform(test[numeric_cols]), columns=numeric_cols,
                        index=test.index)

# ---------- 5. 合并特征 + 按 difficulty 加权验证集 ----------
X_train_full = pd.concat([train_num, train_cat], axis=1).astype(np.float32)
X_test = pd.concat([test_num, test_cat], axis=1).astype(np.float32)
FEATURE_NAMES = list(X_train_full.columns)

X_tr, X_val, y_tr_m, y_val_m, y_tr_b, y_val_b = train_test_split(
    X_train_full.to_numpy(), train["label_multi"].to_numpy(), train["label_binary"].to_numpy(),
    test_size=0.2, random_state=42, stratify=train["label_multi"].to_numpy())

# ---------- 6. 类别权重（不做 SMOTE，先用方案推荐的 class_weight） ----------
classes = np.arange(len(CAT_ORDER))
weights_multi = compute_class_weight("balanced", classes=classes, y=train["label_multi"].to_numpy())
weights_binary = compute_class_weight("balanced", classes=np.array([0, 1]),
                                      y=train["label_binary"].to_numpy())

# ---------- 7. 落盘 ----------
np.save(os.path.join(OUT_DIR, "X_train.npy"), X_tr)
np.save(os.path.join(OUT_DIR, "X_val.npy"), X_val)
np.save(os.path.join(OUT_DIR, "X_test.npy"), X_test.to_numpy())
np.save(os.path.join(OUT_DIR, "y_train_multi.npy"), y_tr_m)
np.save(os.path.join(OUT_DIR, "y_val_multi.npy"), y_val_m)
np.save(os.path.join(OUT_DIR, "y_train_binary.npy"), y_tr_b)
np.save(os.path.join(OUT_DIR, "y_val_binary.npy"), y_val_b)
np.save(os.path.join(OUT_DIR, "y_test_multi.npy"), test["label_multi"].to_numpy())
np.save(os.path.join(OUT_DIR, "y_test_binary.npy"), test["label_binary"].to_numpy())
joblib.dump(encoder, os.path.join(OUT_DIR, "encoder.joblib"))
joblib.dump(scaler, os.path.join(OUT_DIR, "scaler.joblib"))

meta = {
    "clean_stats": clean_stats,
    "category_order": CAT_ORDER,
    "n_features_numeric": len(numeric_cols),
    "n_features_onehot": len(cat_names),
    "n_features_total": len(FEATURE_NAMES),
    "feature_names": FEATURE_NAMES,
    "onehot_feature_names": cat_names,
    "onehot_source_values": {c: sorted(train[c].unique().tolist()) for c in CATEGORICAL},
    "n_train": int(X_tr.shape[0]),
    "n_val": int(X_val.shape[0]),
    "n_test": int(X_test.shape[0]),
    "class_weight_multi": {CAT_ORDER[i]: round(float(w), 4) for i, w in enumerate(weights_multi)},
    "class_weight_binary": {"normal": round(float(weights_binary[0]), 4),
                            "attack": round(float(weights_binary[1]), 4)},
    "train_category_counts": {k: int(v) for k, v in train["label_cat"].value_counts().items()},
    "test_category_counts": {k: int(v) for k, v in test["label_cat"].value_counts().items()},
    "train_binary_counts": {k: int(v) for k, v in train["label_binary"].value_counts().items()},
    "test_binary_counts": {k: int(v) for k, v in test["label_binary"].value_counts().items()},
    "train_attack_type_counts": {k: int(v) for k, v in train["label"].value_counts().items()},
    "test_attack_type_counts": {k: int(v) for k, v in test["label"].value_counts().items()},
    "scaler_numeric_cols": numeric_cols,
}
with open(os.path.join(OUT_DIR, "preprocess_meta.json"), "w", encoding="utf-8") as f:
    json.dump(meta, f, ensure_ascii=False, indent=2)

train.to_csv(os.path.join(OUT_DIR, "clean_train.csv"), index=False, encoding="utf-8")
test.to_csv(os.path.join(OUT_DIR, "clean_test.csv"), index=False, encoding="utf-8")

print("numeric:", len(numeric_cols), "onehot:", len(cat_names), "total:", len(FEATURE_NAMES))
print("train/val/test:", X_tr.shape, X_val.shape, X_test.shape)
print("class weights multi:", meta["class_weight_multi"])
print("clean stats:", json.dumps(clean_stats, ensure_ascii=False))
