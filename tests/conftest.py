import mlflow
import pytest


@pytest.fixture(autouse=True)
def isolated_mlflow_tracking(tmp_path_factory, monkeypatch):
    """
    Chuyen MLflow sang mot store tam thoi trong suot qua trinh chay test.

    Neu khong co fixture nay, moi lan chay pytest se ghi them cac run rac
    (mo hinh do choi, accuracy ~0.27) vao `mlflow.db`, lam nhieu MLflow UI
    dung de doi chieu ket qua thi nghiem cua Buoc 1.
    """
    store = tmp_path_factory.mktemp("mlflow") / "test.db"
    uri = f"sqlite:///{store}"

    monkeypatch.setenv("MLFLOW_TRACKING_URI", uri)
    mlflow.set_tracking_uri(uri)

    yield
