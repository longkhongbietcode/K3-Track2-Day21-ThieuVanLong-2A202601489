import mlflow
import mlflow.sklearn
import pandas as pd
import yaml
import json
import joblib
import os
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    classification_report,
    confusion_matrix,
)

EVAL_THRESHOLD = 0.70

# Nguong canh bao lech lac du lieu: mot lop chiem duoi 10% tong so mau.
MIN_CLASS_RATIO = 0.10

CLASS_LABELS = {0: "thap", 1: "trung_binh", 2: "cao"}

# Bonus 2: cac thuat toan duoc ho tro, chon bang khoa `model_type` trong params.yaml.
MODEL_REGISTRY = {
    "random_forest": RandomForestClassifier,
    "gradient_boosting": GradientBoostingClassifier,
    "logistic_regression": LogisticRegression,
}


def build_model(params: dict):
    """
    Khoi tao mo hinh dua tren khoa `model_type` trong params.

    Cac khoa con lai duoc truyen thang vao constructor cua thuat toan,
    nen params.yaml phai chua dung sieu tham so cua thuat toan da chon.
    """
    model_params = dict(params)
    model_type = model_params.pop("model_type", "random_forest")

    if model_type not in MODEL_REGISTRY:
        raise ValueError(
            f"model_type '{model_type}' khong duoc ho tro. "
            f"Chon mot trong: {sorted(MODEL_REGISTRY)}"
        )

    return MODEL_REGISTRY[model_type](**model_params, random_state=42), model_type


def check_label_distribution(y_train) -> dict:
    """
    Bonus 5: kiem tra phan phoi nhan truoc khi huan luyen.

    Tra ve dict {nhan: ty_le} va in canh bao neu bat ky lop nao
    chiem duoi MIN_CLASS_RATIO tong so mau.
    """
    ratios = y_train.value_counts(normalize=True).sort_index()
    distribution = {str(int(label)): float(r) for label, r in ratios.items()}

    print("Phan phoi nhan tap huan luyen:")
    for label, ratio in distribution.items():
        name = CLASS_LABELS.get(int(label), label)
        print(f"  lop {label} ({name}): {ratio:.2%}")

    for label, ratio in distribution.items():
        if ratio < MIN_CLASS_RATIO:
            print(
                f"CANH BAO LECH LAC DU LIEU: lop {label} chi chiem "
                f"{ratio:.2%} (< {MIN_CLASS_RATIO:.0%}). "
                "Mo hinh co the du doan kem tren lop nay."
            )

    return distribution


def write_report(y_eval, preds, model_type: str, params: dict) -> str:
    """
    Bonus 3: sinh bao cao hieu suat dang van ban vao outputs/report.txt.

    Bao gom confusion matrix, precision/recall/f1 cho tung lop (0, 1, 2).
    """
    labels = sorted(CLASS_LABELS)
    target_names = [f"{i}_{CLASS_LABELS[i]}" for i in labels]

    cm = confusion_matrix(y_eval, preds, labels=labels)
    report_text = classification_report(
        y_eval,
        preds,
        labels=labels,
        target_names=target_names,
        digits=4,
        zero_division=0,
    )

    lines = [
        "BAO CAO HIEU SUAT MO HINH",
        "=" * 60,
        f"model_type : {model_type}",
        f"params     : {params}",
        "",
        "CONFUSION MATRIX (hang = nhan that, cot = nhan du doan)",
        "-" * 60,
        "            " + "".join(f"pred_{i:<8}" for i in labels),
    ]

    for i, row in zip(labels, cm):
        lines.append(f"true_{i:<8}" + "".join(f"{v:<13}" for v in row))

    lines += [
        "",
        "PRECISION / RECALL / F1 THEO TUNG LOP",
        "-" * 60,
        report_text,
    ]

    os.makedirs("outputs", exist_ok=True)
    report_path = "outputs/report.txt"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print("\n".join(lines))
    return report_path


def train(
    params: dict,
    data_path: str = "data/train_phase1.csv",
    eval_path: str = "data/eval.csv",
) -> float:
    """
    Huan luyen mo hinh va ghi nhan ket qua vao MLflow.

    Tham so:
        params     : dict chua `model_type` (tuy chon) va cac sieu tham so.
        data_path  : duong dan den file du lieu huan luyen.
        eval_path  : duong dan den file du lieu danh gia.

    Tra ve:
        accuracy (float): do chinh xac tren tap danh gia.
    """

    df_train = pd.read_csv(data_path)
    df_eval = pd.read_csv(eval_path)

    X_train = df_train.drop(columns=["target"])
    y_train = df_train["target"]
    X_eval = df_eval.drop(columns=["target"])
    y_eval = df_eval["target"]

    label_distribution = check_label_distribution(y_train)

    with mlflow.start_run():

        mlflow.log_params(params)
        mlflow.log_param("n_train_samples", len(df_train))

        for label, ratio in label_distribution.items():
            mlflow.log_metric(f"label_ratio_{label}", ratio)

        model, model_type = build_model(params)
        model.fit(X_train, y_train)

        preds = model.predict(X_eval)
        acc = float(accuracy_score(y_eval, preds))
        f1 = float(f1_score(y_eval, preds, average="weighted"))

        mlflow.log_metric("accuracy", acc)
        mlflow.log_metric("f1_score", f1)
        mlflow.sklearn.log_model(model, "model")

        print(f"Accuracy: {acc:.4f} | F1: {f1:.4f}")

        report_path = write_report(y_eval, preds, model_type, params)
        mlflow.log_artifact(report_path)

        os.makedirs("outputs", exist_ok=True)
        with open("outputs/metrics.json", "w") as f:
            json.dump(
                {
                    "accuracy": acc,
                    "f1_score": f1,
                    "model_type": model_type,
                    "n_train_samples": len(df_train),
                    "label_distribution": label_distribution,
                },
                f,
                indent=2,
            )

        os.makedirs("models", exist_ok=True)
        joblib.dump(model, "models/model.pkl")

    return acc


if __name__ == "__main__":
    with open("params.yaml") as f:
        params = yaml.safe_load(f)
    train(params)
