# -*- coding: utf-8 -*-
"""PyTorch 模型定义：方案主模型 1D-CNN（另附同结构 MLP 便于对照）。
输入为 step2 预处理后的 122 维特征向量，reshape 为 (batch, 1, 122) 送入 Conv1d。
"""
import torch
import torch.nn as nn


class CNN1D(nn.Module):
    """一维卷积分类器：Conv(1->32) -> Pool -> Conv(32->64) -> Pool -> FC -> FC。"""

    def __init__(self, input_dim=122, num_classes=2, dropout=0.5):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv1d(1, 32, kernel_size=3, padding=1), nn.ReLU(),
            nn.MaxPool1d(2),                              # 122 -> 61
            nn.Conv1d(32, 64, kernel_size=3, padding=1), nn.ReLU(),
            nn.MaxPool1d(2),                              # 61 -> 30
        )
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(64 * (input_dim // 4), 128), nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(128, num_classes),
        )

    def forward(self, x):
        # x: (batch, input_dim) -> (batch, 1, input_dim)
        return self.classifier(self.features(x.unsqueeze(1)))


class TorchMLP(nn.Module):
    """PyTorch 版 MLP 基线（128-64），用于和 sklearn MLP / CNN 对照。"""

    def __init__(self, input_dim=122, num_classes=2, dropout=0.3):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 128), nn.ReLU(), nn.Dropout(dropout),
            nn.Linear(128, 64), nn.ReLU(), nn.Dropout(dropout),
            nn.Linear(64, num_classes),
        )

    def forward(self, x):
        return self.net(x)


if __name__ == "__main__":
    m = CNN1D(input_dim=122, num_classes=5)
    out = m(torch.randn(4, 122))
    print("CNN1D output shape:", out.shape)          # 期望 (4, 5)
    print("参数量:", sum(p.numel() for p in m.parameters()))
