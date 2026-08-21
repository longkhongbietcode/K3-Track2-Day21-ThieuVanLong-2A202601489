# Bằng chứng kiểm chứng

Mọi số liệu dưới đây đều lấy từ log thật, có thể tự kiểm tra lại bằng lệnh kèm theo.

---

## 1. Bước 1 — MLflow tracking

Xuất bảng thí nghiệm trực tiếp từ `mlflow.db`:

```bash
mlflow ui --backend-store-uri sqlite:///mlflow.db     # xem trên http://localhost:5000
```

| # | model_type | Siêu tham số | n_train | accuracy | f1_score |
|---|---|---|---:|---:|---:|
| 1 | random_forest | n=50, depth=3, split=2 | 2.998 | 0,5580 | 0,5185 |
| 2 | random_forest | n=100, depth=5, split=2 | 2.998 | 0,5640 | 0,5534 |
| 3 | random_forest | n=200, depth=10, split=5 | 2.998 | 0,6440 | 0,6417 |
| 4 | random_forest | n=500, depth=15, balanced_subsample | 2.998 | 0,6880 | 0,6872 |
| 5 | logistic_regression | max_iter=1000, C=1.0 | 5.996 | 0,5240 | 0,5078 |
| 6 | gradient_boosting | n=200, depth=3, lr=0.1 | 5.996 | 0,6420 | 0,6390 |
| 7 | random_forest | n=500, depth=15, balanced_subsample | 5.996 | 0,7360 | 0,7355 |

Đủ điều kiện: **7 run thí nghiệm, 6 bộ siêu tham số khác nhau, 3 thuật toán**, mọi run
đều có cả `accuracy` lẫn `f1_score`.

> `tests/conftest.py` chuyển MLflow sang store tạm khi chạy pytest, nên `mlflow.db`
> chỉ chứa thí nghiệm thật, không lẫn run rác từ unit test.

**📸 Cần chụp:** MLflow UI ở `http://localhost:5000`, sắp xếp theo `accuracy` giảm dần,
hiển thị đủ 7 run. → lưu vào `docs/img/01-mlflow-runs.png`

---

## 2. Bước 2 — DVC trên S3

```bash
dvc remote list
# myremote  s3://mlops-wine-long-2026-320628059591/dvc

aws s3 ls s3://mlops-wine-long-2026-320628059591/dvc/ --recursive
aws s3 ls s3://mlops-wine-long-2026-320628059591/models/ --recursive
```

Con trỏ DVC được commit vào git (file CSV bị `.gitignore` chặn):

| File | md5 | size |
|---|---|---:|
| `data/train_phase1.csv.dvc` | `5853e7711c78f02286e65fca6cb6e124` | 368.068 B (5.996 mẫu) |
| `data/eval.csv.dvc` | `b11de6b7adaa93a44278fd7e168b2288` | 30.769 B (500 mẫu) |
| `data/train_phase2.csv.dvc` | `fd073d6651b2ff224c0da1eb1c049a32` | 184.134 B (2.998 mẫu) |

Bằng chứng gián tiếp mạnh nhất: step **"Pull data with DVC"** chạy thành công trên GitHub
runner (môi trường sạch, không có dữ liệu cục bộ) trong cả 3 lần chạy — nghĩa là dữ liệu
thực sự tồn tại trên S3.

**📸 Cần chụp:** AWS S3 Console hiển thị hai prefix `dvc/` và `models/latest/`.
→ `docs/img/04-s3-bucket.png`

---

## 3. Bước 2 — CI/CD và Eval gate

Kiểm chứng bằng GitHub API (không cần đăng nhập, repo public):

```bash
curl -s "https://api.github.com/repos/longkhongbietcode/K3-Track2-Day21-ThieuVanLong-2A202601489/actions/runs/32489775163/jobs" \
  | python -c "import json,sys; [print(j['name'],'->',j['conclusion']) for j in json.load(sys.stdin)['jobs']]"
```

| Run | Trigger | Unit Test | Train | Eval | Deploy |
|---|---|---|---|---|---|
| [32489775163](https://github.com/longkhongbietcode/K3-Track2-Day21-ThieuVanLong-2A202601489/actions/runs/32489775163) | workflow_dispatch | ✅ success | ✅ success | ❌ **failure** | ⏭️ skipped |
| [32490631626](https://github.com/longkhongbietcode/K3-Track2-Day21-ThieuVanLong-2A202601489/actions/runs/32490631626) | workflow_dispatch | ✅ success | ✅ success | ✅ success | ✅ success |
| [32492303559](https://github.com/longkhongbietcode/K3-Track2-Day21-ThieuVanLong-2A202601489/actions/runs/32492303559) | **push** | ✅ success | ✅ success | ✅ success | ✅ success |

Run `32489775163` fail đúng tại step **"Check eval gate"** với accuracy 0,688 < 0,70, và
job Deploy bị **skipped** — eval gate hoạt động thật, không phải mô phỏng.

**📸 Cần chụp:** tab Actions với sơ đồ 4 job (một ảnh cho run bị chặn, một ảnh cho run xanh).
→ `docs/img/02-actions-eval-gate-blocked.png`, `docs/img/03-actions-all-green.png`

---

## 4. Bước 3 — Huấn luyện liên tục

Run [32492303559](https://github.com/longkhongbietcode/K3-Track2-Day21-ThieuVanLong-2A202601489/actions/runs/32492303559)
có `"event": "push"`, kích hoạt bởi commit con trỏ DVC `e6566bb`, chạy đủ 4 job xanh và
train trên 5.996 mẫu → accuracy 0,736.

```bash
curl -s ".../actions/runs/32492303559" | python -c "import json,sys; d=json.load(sys.stdin); print(d['event'], d['head_commit']['message'])"
# push data: confirm phase-2 continuous training
```

⚠️ **Lưu ý trung thực:** commit dữ liệu gốc `2ab9bbf` (đổi md5 con trỏ từ 184.090 B →
368.068 B) không kích hoạt được run nào vì Actions đang bị tắt trên fork. Sau khi bật
Actions và sửa path filter, commit `e6566bb` mới kích hoạt thành công — commit này chỉ sửa
dòng comment trong file `.dvc`. Cơ chế trigger và dữ liệu train (5.996 mẫu) đều đúng, nhưng
để chuỗi bằng chứng khớp hoàn toàn với mục 3.4 của đề, xem hướng dẫn chạy lại ở mục 6.

---

## 5. Bước 2 — Serving trên EC2

EC2 `i-0903a309e10cfef6c`, endpoint `http://13.212.232.83:8000`. Kết quả thật:

```console
$ curl http://13.212.232.83:8000/health
{"status":"ok"}

$ curl -X POST http://13.212.232.83:8000/predict -H "Content-Type: application/json" \
    -d '{"features":[7.4,0.70,0.00,1.9,0.076,11.0,34.0,0.9978,3.51,0.56,9.4,0]}'
{"prediction":0,"label":"thap"}

$ curl -X POST http://13.212.232.83:8000/predict -H "Content-Type: application/json" \
    -d '{"features":[6.6,0.24,0.35,7.7,0.031,36.0,135.0,0.9938,3.19,0.37,12.0,1]}'
{"prediction":2,"label":"cao"}

$ curl -X POST http://13.212.232.83:8000/predict -H "Content-Type: application/json" \
    -d '{"features":[1,2,3]}'
HTTP 400
```

Mẫu rượu đỏ axit bay hơi cao (0,70) → `thap`; mẫu rượu trắng cồn 12% → `cao`. Model phân
biệt được nhiều lớp khác nhau, không trả hằng số. Input sai schema bị chặn bằng HTTP 400.

**📸 Cần chụp:** terminal chạy 4 lệnh curl trên. → `docs/img/05-curl-predict.png`

---

## 6. Cách chạy lại vòng lặp Bước 3 để có bằng chứng hoàn chỉnh

Nếu muốn chuỗi bằng chứng khớp tuyệt đối với mục 3.4 (commit message trong Actions chính là
commit bổ sung dữ liệu), chạy lại một vòng với dữ liệu thay đổi thật:

```bash
# 1. Đưa con trỏ về trạng thái phase 1 (object cũ vẫn còn trên S3)
git show 48f7540:data/train_phase1.csv.dvc > data/train_phase1.csv.dvc
dvc checkout data/train_phase1.csv.dvc
git commit -am "data: revert ve tap phase 1 de dien lai vong huan luyen lien tuc"

# 2. Bổ sung dữ liệu mới -> md5 thay đổi thật
python add_new_data.py            # 2998 -> 5996 mẫu
dvc add data/train_phase1.csv
git add data/train_phase1.csv.dvc
git commit -m "data: bo sung 2998 mau du lieu moi (train_phase2)"

# 3. Đẩy dữ liệu lên S3 TRƯỚC, rồi mới push git
dvc push
git push origin main
```

Bước 1 sẽ tạo một run bị chặn tại eval gate (accuracy 0,688) — đúng hành vi mong muốn.
Bước 2 tạo run xanh đủ 4 job với commit message là commit dữ liệu.

---

## 7. Bonus 1 — kích hoạt MLflow từ xa

Code đã sẵn sàng; chỉ cần thêm 3 secrets vào **Settings → Secrets and variables → Actions**:

| Secret | Giá trị |
|---|---|
| `MLFLOW_TRACKING_URI` | `https://dagshub.com/<user>/<repo>.mlflow` |
| `MLFLOW_TRACKING_USERNAME` | tên đăng nhập DagsHub |
| `MLFLOW_TRACKING_PASSWORD` | access token DagsHub |

Nếu chưa có secret, workflow tự quay về `sqlite:///mlflow.db` nên pipeline không bao giờ
gãy vì thiếu cấu hình.

---

## 8. Kiểm chứng cục bộ

```bash
python -m pytest tests/ -v        # 12 passed
python src/train.py               # in phân phối nhãn + confusion matrix, ghi outputs/
```

Danh sách test:

| Test | Kiểm tra |
|---|---|
| `test_train_returns_float` | `train()` trả float trong [0, 1] |
| `test_metrics_file_created` | `outputs/metrics.json` có `accuracy` và `f1_score` |
| `test_model_file_created` | `models/model.pkl` được tạo |
| `test_supported_model_types` (×4) | cả 3 thuật toán train được, ghi đúng `model_type` |
| `test_unknown_model_type_raises` | `model_type` sai báo `ValueError` rõ ràng |
| `test_report_file_created` | `outputs/report.txt` có confusion matrix + precision/recall |
| `test_label_distribution_in_metrics` | tỷ lệ nhãn ghi vào `metrics.json`, tổng = 1,0 |
| `test_drift_warning_on_imbalanced_data` | lớp < 10% sinh cảnh báo |
| `test_no_drift_warning_on_balanced_data` | dữ liệu cân bằng không sinh cảnh báo giả |
