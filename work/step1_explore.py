# -*- coding: utf-8 -*-
"""NSL-KDD 数据探查：读取原始文件，统计样本量、列结构、重复与缺失、类别分布。"""
import json
import os

import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data", "b4986-main", "NSL-KDD", "NSL-KDD")
OUT_DIR = os.path.join(BASE_DIR, "work", "out")
os.makedirs(OUT_DIR, exist_ok=True)

COLUMNS = [
    "duration", "protocol_type", "service", "flag", "src_bytes", "dst_bytes",
    "land", "wrong_fragment", "urgent", "hot", "num_failed_logins", "logged_in",
    "num_compromised", "root_shell", "su_attempted", "num_root", "num_file_creations",
    "num_shells", "num_access_files", "num_outbound_cmds", "is_host_login",
    "is_guest_login", "count", "srv_count", "serror_rate", "srv_serror_rate",
    "rerror_rate", "srv_rerror_rate", "same_srv_rate", "diff_srv_rate",
    "srv_diff_host_rate", "dst_host_count", "dst_host_srv_count",
    "dst_host_same_srv_rate", "dst_host_diff_srv_rate", "dst_host_same_src_port_rate",
    "dst_host_srv_diff_host_rate", "dst_host_serror_rate", "dst_host_srv_serror_rate",
    "dst_host_rerror_rate", "dst_host_srv_rerror_rate", "label", "difficulty",
]

FILES = {
    "KDDTrain+": "KDDTrain+.txt",
    "KDDTrain+_20Percent": "KDDTrain+_20Percent.txt",
    "KDDTest+": "KDDTest+.txt",
    "KDDTest-21": "KDDTest-21.txt",
}

CATEGORICAL = ["protocol_type", "service", "flag"]

ATTACK_CATEGORY = {}
for name in ["back", "land", "neptune", "pod", "smurf", "teardrop", "mailbomb",
             "apache2", "processtable", "udpstorm", "worm"]:
    ATTACK_CATEGORY[name] = "DoS"
for name in ["satan", "ipsweep", "nmap", "portsweep", "mscan", "saint"]:
    ATTACK_CATEGORY[name] = "Probe"
for name in ["guess_passwd", "ftp_write", "imap", "phf", "multihop", "warezmaster",
             "warezclient", "spy", "xlock", "xsnoop", "snmpguess", "snmpgetattack",
             "httptunnel", "sendmail", "named"]:
    ATTACK_CATEGORY[name] = "R2L"
for name in ["buffer_overflow", "loadmodule", "rootkit", "perl", "sqlattack",
             "xterm", "ps"]:
    ATTACK_CATEGORY[name] = "U2R"


def to_category(label):
    if label == "normal":
        return "Normal"
    return ATTACK_CATEGORY.get(label, "Unknown")


def load(name):
    path = os.path.join(DATA_DIR, FILES[name])
    df = pd.read_csv(path, header=None, names=COLUMNS)
    return df


def build_report():
    report = {}
    frames = {}
    for name in FILES:
        df = load(name)
        frames[name] = df
        cat = df["label"].map(to_category)
        report[name] = {
        "rows": int(df.shape[0]),
        "cols": int(df.shape[1]),
        "dup_rows_excl_difficulty": int(df.drop(columns=["difficulty"]).duplicated().sum()),
        "missing_cells": int(df.isna().sum().sum()),
        "label_counts": {k: int(v) for k, v in df["label"].value_counts().items()},
        "category_counts": {k: int(v) for k, v in cat.value_counts().items()},
        "unknown_labels": sorted(set(df["label"]) - set(ATTACK_CATEGORY) - {"normal"}),
        "protocol_type_values": {k: int(v) for k, v in df["protocol_type"].value_counts().items()},
        "service_unique": int(df["service"].nunique()),
        "flag_values": {k: int(v) for k, v in df["flag"].value_counts().items()},
        "difficulty_min": int(df["difficulty"].min()),
        "difficulty_max": int(df["difficulty"].max()),
        }

    train = frames["KDDTrain+"]
    test = frames["KDDTest+"]
    report["_splits"] = {
    "train_rows": int(train.shape[0]),
    "test_rows": int(test.shape[0]),
    "train_services_not_in_test": sorted(set(train["service"]) - set(test["service"])),
    "test_services_not_in_train": sorted(set(test["service"]) - set(train["service"])),
    "train_labels_not_in_test": sorted(set(train["label"]) - set(test["label"])),
    "test_labels_not_in_train": sorted(set(test["label"]) - set(train["label"])),
    "overlap_rows_full_record": int(
        pd.merge(train, test, on=COLUMNS, how="inner").shape[0]
    ),
    }
    return report


if __name__ == "__main__":
    report = build_report()

    with open(os.path.join(OUT_DIR, "explore_report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(json.dumps(report, ensure_ascii=False, indent=2))
