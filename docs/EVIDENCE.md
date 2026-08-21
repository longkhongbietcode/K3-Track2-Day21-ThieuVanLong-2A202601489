# Bằng chứng kiểm chứng

Mọi số liệu dưới đây đều lấy từ log thật, có thể tự kiểm tra lại bằng lệnh kèm theo.

Repo: `longkhongbietcode/K3-Track2-Day21-ThieuVanLong-2A202601489`

---

## 1. Bước 1 — MLflow tracking

```bash
mlflow ui --backend-store-uri sqlite:///mlflow.db     # http://localhost:5000
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

Đủ điều kiện: **7 run thí nghiệm, 6 bộ siêu tham số, 3 thuật toán**, mọi run đều có cả
`accuracy` lẫn `f1_score`.

> `tests/conftest.py` chuyển MLflow sang store tạm khi chạy pytest, nên `mlflow.db` chỉ
> chứa thí nghiệm thật, không lẫn run rác từ unit test.

**📸 Cần chụp:** MLflow UI sắp xếp theo `accuracy` giảm dần, hiển thị đủ 7 run.
→ `docs/img/01-mlflow-runs.png`

---

## 2. Bước 2 — DVC trên S3

```bash
dvc remote list
# myremote  s3://mlops-wine-long-2026-320628059591/dvc

aws s3 ls s3://mlops-wine-long-2026-320628059591/dvc/ --recursive
```

Kết quả thật — 4 phiên bản object:

```
368068  dvc/files/md5/58/53e7711c78f02286e65fca6cb6e124   train_phase1 (5.996 mẫu)
 30769  dvc/files/md5/b1/1de6b7adaa93a44278fd7e168b2288   eval (500 mẫu)
184090  dvc/files/md5/c4/3afab731fd6431a94f888fdc687876   train_phase1 (2.998 mẫu)
184134  dvc/files/md5/fd/073d6651b2ff224c0da1eb1c049a32   train_phase2 (2.998 mẫu)
```

Hai phiên bản của `train_phase1.csv` cùng tồn tại — đây chính là giá trị của việc phiên bản
hóa dữ liệu: có thể quay lại tập cũ bất cứ lúc nào, và vòng Bước 3 ở mục 4 đã làm đúng vậy.

File CSV bị `.gitignore` chặn, chỉ con trỏ `.dvc` được commit. Bằng chứng gián tiếp mạnh
nhất: step **"Pull data with DVC"** chạy thành công trên runner sạch của GitHub ở mọi lần
chạy — dữ liệu thực sự nằm trên S3.

**📸 Cần chụp:** AWS S3 Console, prefix `dvc/files/md5/` và `models/latest/`.
→ `docs/img/04-s3-bucket.png`

---

## 3. Toàn bộ lịch sử GitHub Actions

Kiểm chứng không cần đăng nhập (repo public):

```bash
curl -s "https://api.github.com/repos/longkhongbietcode/K3-Track2-Day21-ThieuVanLong-2A202601489/actions/runs/32500181695/jobs" \
  | python -c "import json,sys; [print(j['name'],'->',j['conclusion']) for j in json.load(sys.stdin)['jobs']]"
```

| Run | Trigger | Test | Train | Eval | Deploy | Ghi chú |
|---|---|---|---|---|---|---|
| [32489775163](https://github.com/longkhongbietcode/K3-Track2-Day21-ThieuVanLong-2A202601489/actions/runs/32489775163) | dispatch | ✅ | ✅ | ❌ | ⏭️ | eval gate chặn (0,688) |
| [32490631626](https://github.com/longkhongbietcode/K3-Track2-Day21-ThieuVanLong-2A202601489/actions/runs/32490631626) | dispatch | ✅ | ✅ | ✅ | ✅ | |
| [32492303559](https://github.com/longkhongbietcode/K3-Track2-Day21-ThieuVanLong-2A202601489/actions/runs/32492303559) | push | ✅ | ✅ | ✅ | ✅ | |
| [32496099572](https://github.com/longkhongbietcode/K3-Track2-Day21-ThieuVanLong-2A202601489/actions/runs/32496099572) | push | ✅ | ❌ | ⏭️ | ⏭️ | IAM thiếu quyền ghi `models/candidate/` |
| [32497126558](https://github.com/longkhongbietcode/K3-Track2-Day21-ThieuVanLong-2A202601489/actions/runs/32497126558) | push | ✅ | ✅ | ✅ | ❌ | SG chặn SSH từ runner |
| [32498717136](https://github.com/longkhongbietcode/K3-Track2-Day21-ThieuVanLong-2A202601489/actions/runs/32498717136) | push | ✅ | ✅ | ✅ | ✅ | 5 bonus chạy thật trên CI |
| **[32499561084](https://github.com/longkhongbietcode/K3-Track2-Day21-ThieuVanLong-2A202601489/actions/runs/32499561084)** | **push** | ✅ | ✅ | ❌ | ⏭️ | **Bước 3 vòng 1 — gate chặn** |
| **[32500181695](https://github.com/longkhongbietcode/K3-Track2-Day21-ThieuVanLong-2A202601489/actions/runs/32500181695)** | **push** | ✅ | ✅ | ✅ | ✅ | **Bước 3 vòng 2 — deploy tự động** |

**📸 Cần chụp:** tab Actions, sơ đồ 4 job của run `32499561084` (Eval đỏ, Deploy xám) và
run `32500181695` (cả bốn xanh). → `docs/img/02-actions-eval-gate-blocked.png`,
`docs/img/03-actions-all-green.png`

---

## 4. Bước 3 — Huấn luyện liên tục (đã diễn đầy đủ)

Vòng lặp được chạy lại từ đầu để chuỗi bằng chứng khớp chính xác với mục 3.4 của đề bài.

**Vòng 1 — commit `96bf2ba` đưa dữ liệu về phase 1 (2.998 mẫu):**

```
event   : push
commit  : data: dua tap huan luyen ve phase 1 (2998 mau)
pointer : md5 c43afab7... (184.090 B)
kết quả : accuracy 0,688 -> Eval FAIL tại step "Check eval gate" -> Deploy skipped
```

Kiểm chứng S3 **không hề bị ghi đè** khi pipeline bị chặn:

```console
$ aws s3 ls s3://mlops-wine-long-2026-320628059591/models/latest/
2026-08-21 22:43:18        236 metrics.json      <- vẫn là model 0,736 của lần trước
2026-08-21 22:43:13   76085217 model.pkl
```

**Vòng 2 — commit `8b80c45` bổ sung dữ liệu mới (5.996 mẫu):**

```bash
python add_new_data.py            # Cap nhat du lieu: 2998 -> 5996 mau
dvc add data/train_phase1.csv     # pointer -> md5 5853e771... (368.068 B)
git commit -m "data: bo sung 2998 mau du lieu moi (train_phase2)"
dvc push                          # Everything is up to date
git push origin main
```

```
event   : push
commit  : data: bo sung 2998 mau du lieu moi (train_phase2)
kết quả : accuracy 0,736 -> cả bốn job xanh -> model mới được thăng hạng và deploy
```

Chỉ một lần `git push` con trỏ DVC, không thao tác thủ công nào khác. Xác nhận model mới
thực sự lên EC2:

```console
$ aws s3 ls s3://mlops-wine-long-2026-320628059591/models/latest/
2026-08-21 23:00:03        236 metrics.json      <- đã cập nhật
2026-08-21 22:59:57   76085217 model.pkl

$ ssh ubuntu@13.212.232.83 "systemctl show mlops-serve -p ActiveEnterTimestamp"
ActiveEnterTimestamp=Fri 2026-08-21 16:00:08 UTC   <- service restart ngay sau khi promote
```

---

## 5. Bước 2 — Serving trên EC2

EC2 `i-0903a309e10cfef6c` (ap-southeast-1), endpoint `http://13.212.232.83:8000`:

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

Rượu đỏ axit bay hơi cao (0,70) → `thap`; rượu trắng cồn 12% → `cao`. Model phân biệt
được nhiều lớp, không trả hằng số. Input sai schema bị chặn bằng HTTP 400.

**📸 Cần chụp:** terminal chạy 4 lệnh curl trên. → `docs/img/05-curl-predict.png`

---

## 6. Hai lỗi hạ tầng phát hiện được nhờ chạy thật

Cả hai đều là lỗi cấu hình có sẵn, chỉ lộ ra khi pipeline chạy lại — nếu không sửa, giám
khảo chấm lại sẽ thấy pipeline đỏ.

**6.1 — IAM thiếu quyền (run `32496099572`).** Policy `MLOpsPipelineS3Access` chỉ cho
`PutObject` trên `models/latest/*`, nên không ghi được `models/candidate/`. Sửa bằng cách
chuyển model qua artifact của workflow thay vì vòng qua S3, và bổ sung statement
`ReadDeployedModelMetrics` để job Train đọc được accuracy của model đang chạy — điều kiện
cần của gate chặn hồi quy. Xem [aws/github-s3-policy.json](../aws/github-s3-policy.json).

**6.2 — Security group chặn SSH (run `32497126558`).** Port 22 chỉ mở cho
`113.185.52.236/32` (IP máy cá nhân), runner GitHub có IP động nên không kết nối được;
`ActiveEnterTimestamp` của service chứng minh nó chưa hề restart. Sửa bằng cách cho job
Deploy mở tạm port 22 đúng IP runner rồi gỡ ra ở step `always()`:

```console
$ aws ec2 describe-security-groups --group-ids sg-02d44d2d511d4cea5 \
    --query 'SecurityGroups[].IpPermissions[].{Port:FromPort,Cidrs:IpRanges[].CidrIp}'
[{"Port": 8000, "Cidrs": ["0.0.0.0/0"]},
 {"Port": 22,   "Cidrs": ["113.185.52.236/32"]}]     <- sau 2 lần deploy, rule tạm đã được gỡ sạch
```

Quyền được giới hạn đúng một security group duy nhất, xem
[aws/github-ec2-sg-policy.json](../aws/github-ec2-sg-policy.json).

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
