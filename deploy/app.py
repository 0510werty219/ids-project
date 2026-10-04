# -*- coding: utf-8 -*-
"""阶段 6：实时检测演示服务（仅使用 Python 标准库，无需安装 Flask）。
启动：python app.py，然后浏览器打开 http://127.0.0.1:5000
原理：从 clean_test.csv 逐条读取流量记录模拟"流量实时到达"，
复用训练时保存的 encoder / scaler 做完全一致的特征预处理，
用训练好的 1D-CNN（二分类）实时判定 正常/攻击。
"""
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import joblib
import numpy as np
import pandas as pd
import torch

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK_DIR = os.path.join(BASE_DIR, "work")
OUT_DIR = os.path.join(WORK_DIR, "out")
sys.path.insert(0, WORK_DIR)
from step6_cnn_model import CNN1D  # noqa: E402

CATEGORICAL = ["protocol_type", "service", "flag"]
HOST, PORT = "127.0.0.1", 5000

# ---------- 加载预处理对象与模型 ----------
meta = json.load(open(os.path.join(OUT_DIR, "preprocess_meta.json"), encoding="utf-8"))
encoder = joblib.load(os.path.join(OUT_DIR, "encoder.joblib"))
scaler = joblib.load(os.path.join(OUT_DIR, "scaler.joblib"))
FEATURE_NAMES = meta["feature_names"]
NUMERIC_COLS = meta["scaler_numeric_cols"]

ckpt = torch.load(os.path.join(OUT_DIR, "cnn_binary_best.pth"), map_location="cpu",
                  weights_only=False)
model = CNN1D(input_dim=ckpt["input_dim"], num_classes=ckpt["num_classes"])
model.load_state_dict(ckpt["model_state_dict"])
model.eval()

# ---------- 加载测试流量，模拟实时到达 ----------
flows = pd.read_csv(os.path.join(OUT_DIR, "clean_test.csv"), encoding="utf-8")
state = {"cursor": 0, "total": 0, "alerts": 0, "hits": 0}
print(f"已加载 {len(flows)} 条流量，模型输入维度 {ckpt['input_dim']}")


def preprocess_one(row):
    """单条流量 -> 122 维特征向量（与训练时预处理完全一致）"""
    num = scaler.transform(pd.DataFrame([row[NUMERIC_COLS].to_dict()]))[0]
    cat = encoder.transform(pd.DataFrame([row[CATEGORICAL].to_dict()]))[0]
    values = dict(zip(NUMERIC_COLS, num))
    values.update(dict(zip(meta["onehot_feature_names"], cat)))
    return np.array([values[n] for n in FEATURE_NAMES], dtype=np.float32)


def detect_next():
    i = state["cursor"] % len(flows)
    state["cursor"] += 1
    row = flows.iloc[i]
    x = torch.from_numpy(preprocess_one(row)).unsqueeze(0)
    with torch.no_grad():
        prob = torch.softmax(model(x), dim=1)[0]
    pred = int(prob.argmax())
    true_binary = int(row["label_binary"])
    state["total"] += 1
    if pred == 1:
        state["alerts"] += 1
    if pred == true_binary:
        state["hits"] += 1
    return {
        "id": int(i),
        "prediction": "attack" if pred == 1 else "normal",
        "confidence": round(float(prob[pred]), 4),
        "ground_truth": str(row["label"]),
        "correct": bool(pred == true_binary),
        "total": state["total"],
        "alerts": state["alerts"],
        "accuracy_so_far": round(state["hits"] / state["total"], 4),
    }


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self._send(200, "text/html; charset=utf-8",
                       open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                         "index.html"), "rb").read())
        elif self.path.startswith("/next"):
            self._send(200, "application/json; charset=utf-8",
                       json.dumps(detect_next()).encode("utf-8"))
        else:
            self._send(404, "text/plain", b"not found")

    def _send(self, code, ctype, body):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):  # 关闭访问日志刷屏
        pass


if __name__ == "__main__":
    print(f"演示服务已启动: http://{HOST}:{PORT}  (Ctrl+C 停止)")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
