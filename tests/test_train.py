import os
import json
import numpy as np
import pandas as pd
import pytest
from src.train import train, build_model, check_label_distribution


FEATURE_NAMES = [
    "fixed_acidity", "volatile_acidity", "citric_acid", "residual_sugar",
    "chlorides", "free_sulfur_dioxide", "total_sulfur_dioxide", "density",
    "pH", "sulphates", "alcohol", "wine_type",
]


def _make_temp_data(tmp_path):
    """
    Tao dataset nho voi cung schema Wine Quality de su dung trong test.

    pytest cung cap `tmp_path` la mot thu muc tam thoi, tu dong xoa sau khi test ket thuc.
    Ham nay dung du lieu ngau nhien nen khong can ket noi S3 hay tai file CSV thuc.
    """
    rng = np.random.default_rng(0)
    n = 200

    X = rng.random((n, len(FEATURE_NAMES)))
    y = rng.integers(0, 3, size=n)

    df = pd.DataFrame(X, columns=FEATURE_NAMES)
    df["target"] = y

    train_path = str(tmp_path / "train.csv")
    eval_path = str(tmp_path / "eval.csv")
    df.iloc[:160].to_csv(train_path, index=False)
    df.iloc[160:].to_csv(eval_path, index=False)

    return train_path, eval_path


def test_train_returns_float(tmp_path):
    """Kiem tra ham train() tra ve mot so thuc nam trong [0.0, 1.0]."""
    train_path, eval_path = _make_temp_data(tmp_path)

    acc = train(
        {"n_estimators": 10, "max_depth": 3},
        data_path=train_path,
        eval_path=eval_path,
    )

    assert isinstance(acc, float)
    assert 0.0 <= acc <= 1.0


def test_metrics_file_created(tmp_path):
    """Kiem tra file outputs/metrics.json duoc tao sau khi huan luyen."""
    train_path, eval_path = _make_temp_data(tmp_path)
    train(
        {"n_estimators": 10, "max_depth": 3},
        data_path=train_path,
        eval_path=eval_path,
    )

    assert os.path.exists("outputs/metrics.json")

    with open("outputs/metrics.json") as f:
        metrics = json.load(f)

    assert "accuracy" in metrics
    assert "f1_score" in metrics


def test_model_file_created(tmp_path):
    """Kiem tra file models/model.pkl duoc tao sau khi huan luyen."""
    train_path, eval_path = _make_temp_data(tmp_path)
    train(
        {"n_estimators": 10, "max_depth": 3},
        data_path=train_path,
        eval_path=eval_path,
    )

    assert os.path.exists("models/model.pkl")


# --- Bonus 2: nhieu thuat toan --------------------------------------------


@pytest.mark.parametrize(
    "params, expected_type",
    [
        ({"n_estimators": 10, "max_depth": 3}, "random_forest"),
        (
            {"model_type": "random_forest", "n_estimators": 10, "max_depth": 3},
            "random_forest",
        ),
        (
            {"model_type": "gradient_boosting", "n_estimators": 5, "max_depth": 2},
            "gradient_boosting",
        ),
        ({"model_type": "logistic_regression", "max_iter": 200}, "logistic_regression"),
    ],
)
def test_supported_model_types(tmp_path, params, expected_type):
    """Moi thuat toan duoc ho tro deu huan luyen duoc va ghi dung model_type."""
    train_path, eval_path = _make_temp_data(tmp_path)

    acc = train(params, data_path=train_path, eval_path=eval_path)
    assert 0.0 <= acc <= 1.0

    with open("outputs/metrics.json") as f:
        metrics = json.load(f)

    assert metrics["model_type"] == expected_type


def test_unknown_model_type_raises():
    """model_type khong hop le phai bao loi ro rang thay vi that bai am tham."""
    with pytest.raises(ValueError, match="khong duoc ho tro"):
        build_model({"model_type": "khong_ton_tai"})


# --- Bonus 3: bao cao hieu suat -------------------------------------------


def test_report_file_created(tmp_path):
    """Kiem tra outputs/report.txt chua confusion matrix va precision/recall."""
    train_path, eval_path = _make_temp_data(tmp_path)
    train(
        {"n_estimators": 10, "max_depth": 3},
        data_path=train_path,
        eval_path=eval_path,
    )

    assert os.path.exists("outputs/report.txt")

    with open("outputs/report.txt", encoding="utf-8") as f:
        report = f.read()

    assert "CONFUSION MATRIX" in report
    assert "precision" in report
    assert "recall" in report


# --- Bonus 5: canh bao lech lac du lieu -----------------------------------


def test_label_distribution_in_metrics(tmp_path):
    """Ty le phan phoi nhan phai duoc ghi vao metrics.json ben canh accuracy."""
    train_path, eval_path = _make_temp_data(tmp_path)
    train(
        {"n_estimators": 10, "max_depth": 3},
        data_path=train_path,
        eval_path=eval_path,
    )

    with open("outputs/metrics.json") as f:
        metrics = json.load(f)

    distribution = metrics["label_distribution"]
    assert set(distribution) == {"0", "1", "2"}
    assert abs(sum(distribution.values()) - 1.0) < 1e-6


def test_drift_warning_on_imbalanced_data(capsys):
    """Lop chiem duoi 10% tong so mau phai sinh canh bao ro rang trong log."""
    y = pd.Series([0] * 60 + [1] * 35 + [2] * 5)

    distribution = check_label_distribution(y)
    captured = capsys.readouterr().out

    assert distribution["2"] == 0.05
    assert "CANH BAO LECH LAC DU LIEU" in captured
    assert "lop 2" in captured


def test_no_drift_warning_on_balanced_data(capsys):
    """Du lieu can bang thi khong duoc sinh canh bao gia."""
    y = pd.Series([0] * 34 + [1] * 33 + [2] * 33)

    check_label_distribution(y)
    captured = capsys.readouterr().out

    assert "CANH BAO LECH LAC DU LIEU" not in captured
