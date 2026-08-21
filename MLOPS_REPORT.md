# Báo cáo MLOps Wine Quality trên AWS

Repository: https://github.com/longkhongbietcode/K3-Track2-Day21-ThieuVanLong-2A202601489

## Kết quả

| Giai đoạn | Số mẫu train | Accuracy | Weighted F1 | Kết quả pipeline |
|---|---:|---:|---:|---|
| Phase 1 | 2.998 | 0,6880 | 0,6872 | Unit Test/Train đạt; Eval gate 0,70 chặn Deploy |
| Phase 2 | 5.996 | 0,7360 | 0,7355 | Unit Test/Train/Eval/Deploy đều đạt |

Bộ siêu tham số được chọn: `n_estimators=500`, `max_depth=15`,
`min_samples_split=2`, `max_features=None`, `criterion=gini`,
`class_weight=balanced_subsample`. Đây là cấu hình có accuracy phase 1 cao
nhất trong các cấu hình Random Forest đã thử và đạt gate sau khi bổ sung dữ
liệu phase 2.

## Bằng chứng

- MLflow local có các runs với cả `accuracy` và `f1_score`; ba cấu hình bắt
  buộc đạt lần lượt 0,5640; 0,5580; 0,6440, và run tối ưu đạt 0,6880.
- Phase 1 eval-gate:
  https://github.com/longkhongbietcode/K3-Track2-Day21-ThieuVanLong-2A202601489/actions/runs/32489775163
- Phase 2 bốn jobs xanh:
  https://github.com/longkhongbietcode/K3-Track2-Day21-ThieuVanLong-2A202601489/actions/runs/32490631626
- DVC lưu bốn phiên bản object trong
  `s3://mlops-wine-long-2026-320628059591/dvc/`.
- Model mới nhất:
  `s3://mlops-wine-long-2026-320628059591/models/latest/model.pkl`.
- EC2 `i-0903a309e10cfef6c`, API: `http://13.212.232.83:8000`.
  `GET /health` trả `{"status":"ok"}`; `POST /predict` trả
  `{"prediction":0,"label":"thap"}`; input sai số feature trả HTTP 400.

## Khó khăn và cách khắc phục

Phase 1 không thể đạt ngưỡng 0,70 dù đã grid-search Random Forest; gate được
giữ nguyên để chứng minh cơ chế chặn deploy, còn phase 2 đạt 0,736 sau khi
thêm dữ liệu. DVC gặp lỗi refresh credentials của `aws login`; temporary
credentials được export chỉ trong bộ nhớ tiến trình. Push event của repository
không tạo Actions run dù workflow active và paths đã khớp, nên hai lần kiểm
chứng được chạy bằng `workflow_dispatch`; trigger `data/*.dvc` đã được sửa cho
các cập nhật dữ liệu trực tiếp trong thư mục `data`.
