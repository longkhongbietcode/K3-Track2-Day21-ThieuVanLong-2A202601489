# Báo cáo MLOps Wine Quality trên AWS

Repository: https://github.com/longkhongbietcode/K3-Track2-Day21-ThieuVanLong-2A202601489

Bằng chứng chi tiết (link Actions, ảnh chụp màn hình, log kiểm chứng): [docs/EVIDENCE.md](docs/EVIDENCE.md)

## 1. Bộ siêu tham số đã chọn và lý do

Cấu hình cuối cùng trong `params.yaml`:

```yaml
model_type: random_forest
n_estimators: 500
max_depth: 15
min_samples_split: 2
max_features: null
criterion: gini
class_weight: balanced_subsample
```

Kết quả các thí nghiệm trên MLflow (tập đánh giá `eval.csv`, 500 mẫu held-out):

| Thuật toán | Siêu tham số chính | Số mẫu train | Accuracy | F1 (weighted) |
|---|---|---:|---:|---:|
| RandomForest | n=50, depth=3, split=2 | 2.998 | 0,5580 | 0,5185 |
| RandomForest | n=100, depth=5, split=2 | 2.998 | 0,5640 | 0,5534 |
| RandomForest | n=200, depth=10, split=5 | 2.998 | 0,6440 | 0,6417 |
| **RandomForest** | **n=500, depth=15, balanced_subsample** | 2.998 | **0,6880** | **0,6872** |
| LogisticRegression | max_iter=1000, C=1.0 | 5.996 | 0,5240 | 0,5078 |
| GradientBoosting | n=200, depth=3, lr=0.1 | 5.996 | 0,6420 | 0,6390 |
| **RandomForest** | **n=500, depth=15, balanced_subsample** | 5.996 | **0,7360** | **0,7355** |

Lý do chọn: accuracy tăng đơn điệu theo độ sâu và số cây (0,558 → 0,564 → 0,644 → 0,688),
cho thấy các cấu hình nông bị **underfit** — cây độ sâu 3-5 không tách được ranh giới
phi tuyến giữa ba mức chất lượng. `class_weight=balanced_subsample` được thêm vì lớp 2
(chất lượng cao) chỉ chiếm 19,6% tập huấn luyện; nếu không bù trọng số, mô hình bỏ qua
lớp thiểu số và F1 tụt xa dưới accuracy. Trên cùng tập dữ liệu 5.996 mẫu, RandomForest
vượt GradientBoosting 9,4 điểm và LogisticRegression 21,2 điểm — LogisticRegression kém
nhất vì ranh giới tuyến tính không phù hợp với đặc trưng hóa học chưa chuẩn hóa.

## 2. So sánh Bước 2 và Bước 3 (mục 3.6)

| Chỉ số | Bước 2 (2.998 mẫu) | Bước 3 (5.996 mẫu) | Thay đổi |
|---|---:|---:|---:|
| accuracy | 0,6880 | 0,7360 | **+0,0480** |
| f1_score | 0,6872 | 0,7355 | **+0,0483** |
| Eval gate (≥ 0,70) | ❌ Không đạt | ✅ Đạt | — |
| Deploy | Bị chặn (skipped) | Thành công | — |

Cùng một bộ siêu tham số, chỉ tăng gấp đôi dữ liệu huấn luyện đã đưa mô hình vượt ngưỡng
0,70. Đây là bằng chứng trực tiếp cho giá trị của vòng lặp huấn luyện liên tục: model
không đổi, code không đổi, chỉ dữ liệu mới làm nên khác biệt.

## 3. Kết quả pipeline

| Giai đoạn | Trigger | Unit Test | Train | Eval | Deploy |
|---|---|---|---|---|---|
| [Phase 1 (2.998 mẫu)](https://github.com/longkhongbietcode/K3-Track2-Day21-ThieuVanLong-2A202601489/actions/runs/32499561084) | push commit dữ liệu | ✅ | ✅ | ❌ chặn tại gate 0,70 | ⏭️ skipped |
| [Phase 2 (5.996 mẫu)](https://github.com/longkhongbietcode/K3-Track2-Day21-ThieuVanLong-2A202601489/actions/runs/32500181695) | push commit dữ liệu | ✅ | ✅ | ✅ | ✅ |

Cả hai lần chạy đều được kích hoạt tự động bởi một lệnh `git push` con trỏ DVC, không có
thao tác thủ công nào. Khi pipeline bị chặn ở phase 1, `models/latest/` trên S3 giữ nguyên
model tốt trước đó — kiểm chứng bằng timestamp trong [docs/EVIDENCE.md](docs/EVIDENCE.md).

API đang phục vụ: `http://13.212.232.83:8000` (EC2 `i-0903a309e10cfef6c`).
`GET /health` → `{"status":"ok"}`; `POST /predict` → `{"prediction":0,"label":"thap"}`;
input sai số lượng feature → HTTP 400.

## 4. Các thách thức nâng cao đã thực hiện

| Bonus | Nội dung | Vị trí |
|---|---|---|
| 1 | MLflow tracking từ xa: workflow đọc `MLFLOW_TRACKING_URI` từ GitHub Secrets, tự quay về SQLite nếu chưa cấu hình | `.github/workflows/mlops.yml` (step *Train model*) |
| 2 | Ba thuật toán chọn qua `model_type`: random_forest / gradient_boosting / logistic_regression | `src/train.py` (`MODEL_REGISTRY`, `build_model`) |
| 3 | Báo cáo tự động: confusion matrix + precision/recall/f1 từng lớp ghi ra `outputs/report.txt`, upload cùng `metrics.json` | `src/train.py` (`write_report`) + step *Save metrics and report as artifact* |
| 4 | Chặn hồi quy: tải `metrics.json` của model đang chạy từ S3, chỉ deploy khi accuracy mới ≥ accuracy cũ | step *Download previous metrics* + *Check regression against deployed model* |
| 5 | Cảnh báo lệch lạc dữ liệu: tính tỷ lệ từng lớp, cảnh báo nếu lớp nào < 10%, ghi vào `metrics.json` | `src/train.py` (`check_label_distribution`) |

Cơ chế **candidate → latest** đi kèm Bonus 4: model mới chỉ được upload vào
`models/candidate/` ở job Train, và chỉ được thăng hạng lên `models/latest/` ở job Deploy
sau khi qua cả hai gate. Nhờ vậy khi pipeline bị chặn, S3 vẫn giữ nguyên model tốt cuối
cùng — VM có khởi động lại ngoài ý muốn cũng không nạp phải model đã bị từ chối.

## 5. Khó khăn và cách khắc phục

**Phase 1 không đạt ngưỡng 0,70.** Đã grid-search RandomForest nhưng trần là 0,688. Thay
vì hạ ngưỡng cho pipeline xanh, tôi giữ nguyên gate để chứng minh cơ chế chặn deploy hoạt
động thật, rồi giải quyết bằng đúng cách mà lab hướng tới: bổ sung dữ liệu ở Bước 3 → 0,736.

**DVC lỗi refresh credentials của `aws login`.** Temporary credentials được export trực
tiếp vào biến môi trường của tiến trình, không ghi ra file, tránh rò rỉ khoá vào repo.

**Actions không kích hoạt.** Repository là một fork nên GitHub tự tắt Actions; phải bật lại
ở cấp repository. Sau đó path filter `data/*.dvc` mới bắt được commit con trỏ DVC và pipeline
chạy đủ bốn jobs tự động.

**Test làm bẩn MLflow.** Mỗi lần chạy `pytest`, ba test huấn luyện mô hình đồ chơi và ghi
run rác (accuracy ~0,27) vào `mlflow.db`, làm nhiễu MLflow UI dùng để so sánh thí nghiệm.
Đã thêm `tests/conftest.py` chuyển MLflow sang store tạm thời trong lúc test.

**IAM quá chặt và security group khoá SSH.** Khi chạy lại pipeline, hai lỗi cấu hình có sẵn
mới lộ ra: policy của user `mlops-github-actions` không cho ghi ngoài `models/latest/*` và
không cho đọc lại metrics của model đang chạy; đồng thời port 22 chỉ mở cho IP máy cá nhân
nên runner GitHub không SSH vào được — service trên EC2 chưa hề restart dù pipeline báo
xanh ở các bước trước. Đã sửa bằng cách chuyển model qua artifact của workflow, bổ sung
đúng một statement `s3:GetObject` cho `models/latest/*`, và cho job Deploy mở tạm port 22
đúng IP runner rồi gỡ ra ở step `always()` thay vì phơi SSH ra toàn Internet. Chi tiết ở
mục 6 của [docs/EVIDENCE.md](docs/EVIDENCE.md).
