# -*- coding: utf-8 -*-
"""按方案阶段 4 训练 PyTorch 1D-CNN（二分类 + 五分类）。
策略：Adam(lr=1e-3, weight_decay=1e-4)，batch=256，交叉熵 + 类别权重，
Early Stopping（patience=8），保存验证集 loss 最优的权重。
用法：python step7_train_cnn.py [lr] [batch_size] [max_epochs]
结果写入 out/cnn_history.json，权重写入 out/cnn_{binary,multi}_best.pth。
"""
import json
import os
import sys
import time

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

from step6_cnn_model import CNN1D

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(BASE_DIR, "work", "out")

LR = float(sys.argv[1]) if len(sys.argv) > 1 else 1e-3
BATCH = int(sys.argv[2]) if len(sys.argv) > 2 else 256
MAX_EPOCHS = int(sys.argv[3]) if len(sys.argv) > 3 else 50
PATIENCE = 8

torch.manual_seed(42)
np.random.seed(42)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"device={device} lr={LR} batch={BATCH} max_epochs={MAX_EPOCHS}", flush=True)


def load(name):
    return np.load(os.path.join(OUT_DIR, name))


def class_weights(y, n_classes):
    counts = np.bincount(y, minlength=n_classes).astype(np.float64)
    w = len(y) / (n_classes * np.maximum(counts, 1.0))
    return torch.tensor(w, dtype=torch.float32, device=device)


def train_one(tag, num_classes, y_tr, y_val):
    X_tr = load("X_train.npy")
    X_val = load("X_val.npy")
    train_loader = DataLoader(
        TensorDataset(torch.from_numpy(X_tr), torch.from_numpy(y_tr)),
        batch_size=BATCH, shuffle=True)
    val_x = torch.from_numpy(X_val).to(device)
    val_y = torch.from_numpy(y_val).to(device)

    model = CNN1D(input_dim=X_tr.shape[1], num_classes=num_classes).to(device)
    criterion = nn.CrossEntropyLoss(weight=class_weights(y_tr, num_classes))
    optimizer = torch.optim.Adam(model.parameters(), lr=LR, weight_decay=1e-4)

    best_loss, wait, best_state = float("inf"), 0, None
    hist = {"train_loss": [], "val_loss": [], "val_acc": []}
    t0 = time.time()
    for epoch in range(1, MAX_EPOCHS + 1):
        model.train()
        total = 0.0
        for xb, yb in train_loader:
            xb, yb = xb.to(device), yb.to(device)
            loss = criterion(model(xb), yb)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            total += loss.item() * len(xb)
        train_loss = total / len(train_loader.dataset)

        model.eval()
        with torch.no_grad():
            logits = model(val_x)
            val_loss = criterion(logits, val_y).item()
            val_acc = (logits.argmax(1) == val_y).float().mean().item()
        hist["train_loss"].append(train_loss)
        hist["val_loss"].append(val_loss)
        hist["val_acc"].append(val_acc)
        print(f"[{tag}] epoch {epoch:02d} | train {train_loss:.4f} | "
              f"val {val_loss:.4f} | val_acc {val_acc:.4f} | {time.time()-t0:.0f}s",
              flush=True)

        if val_loss < best_loss:
            best_loss, wait = val_loss, 0
            best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
        else:
            wait += 1
            if wait >= PATIENCE:
                print(f"[{tag}] early stopping at epoch {epoch}", flush=True)
                break

    path = os.path.join(OUT_DIR, f"cnn_{tag}_best.pth")
    torch.save({"model_state_dict": best_state,
                "input_dim": int(X_tr.shape[1]),
                "num_classes": num_classes,
                "config": {"lr": LR, "batch": BATCH, "weight_decay": 1e-4},
                "best_val_loss": best_loss}, path)
    hist["best_val_loss"] = best_loss
    hist["epochs_run"] = len(hist["train_loss"])
    hist["train_seconds"] = round(time.time() - t0, 1)
    print(f"[{tag}] saved -> {path}", flush=True)
    return hist


if __name__ == "__main__":
    history = {}
    history["binary"] = train_one("binary", 2,
                                  load("y_train_binary.npy"), load("y_val_binary.npy"))
    history["multi"] = train_one("multi", 5,
                                 load("y_train_multi.npy"), load("y_val_multi.npy"))
    with open(os.path.join(OUT_DIR, "cnn_history.json"), "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
    print("DONE", flush=True)
