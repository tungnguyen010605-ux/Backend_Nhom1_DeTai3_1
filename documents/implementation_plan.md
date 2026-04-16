# Phase B: AI Fitting Backend Pipeline

Phase B tập trung vào việc hiện thực hóa phần "lõi" của dự án (AI Model) và tích hợp nó vào Backend FastAPI một cách mượt mà để Unity có thể gọi đến mà không bị đứng server.

### In Progress
- [ ] Tối ưu chất lượng preprocessing đúng chuẩn CP-VTON (agnostic person, cloth mask, pose map) thay vì mức compatibility hiện tại.
- [ ] Căn chỉnh lại persistence strategy để vừa giữ được ảnh quần áo gốc, vừa lưu được lịch sử output texture theo task.

### To Do
- [ ] Gắn checkpoint CP-VTON thật đã train ổn định (kèm versioning và rollback strategy).
- [ ] Tạo quy trình đánh giá định lượng (FID/LPIPS hoặc proxy metric phù hợp đồ án) cho output fitting.
- [ ] Hoàn thiện tài liệu runbook deploy + monitor VRAM cho môi trường demo.
- [ ] Thiết kế Phase C cho avatar deformation (blendshape/bone scaling) để body measurements có ý nghĩa trực quan trong VR.

## Đánh giá Kiến trúc Hiện tại
- Hiện tại, Backend đã có một thread độc lập (`TaskManager` trong `tasks.py`) để giả lập việc sinh ảnh (quá trình mất 2 giây).
- Unity Client đã ghép nối thành công API poll `/status/{task_id}` và tự động tải ảnh về. Luồng kết nối đồng bộ cơ bản đã hoàn tất.

## Proposed Changes

### 1. ML Training Pipeline (Pipeline Huấn Luyện ML)
Tạo cấu trúc thư mục mới `Bend/ml_pipeline/` hoạt động độc lập với FastAPI app để chuyên lo việc training và thử nghiệm model.

#### [NEW] ml_pipeline/dataset.py:
  - Script chuẩn bị lớp `PyTorch Dataset/DataLoader` để đọc "dữ liệu đã preprocess" (ảnh gốc, ảnh pose keypoints, ảnh quần áo mask, v.v.).
#### [NEW] ml_pipeline/train.py:
  - Vòng lặp huấn luyện chính (Training loop), checkpoint saving, và ghi log loss metrics.
#### [NEW] ml_pipeline/models/:
  - Chứa cấu trúc mạng nơ-ron (ví dụ: các file định nghĩa kiến trúc GAN hoặc tham chiếu đến Diffusers thư viện).

---

### 2. Inference API & Model Loading
Tích hợp model đã được huấn luyện vào hệ thống Backend để phục vụ các yêu cầu (requests) thực tế từ Unity.

#### [MODIFY] Bend/app/services/tasks.py
  - Thay thế hàm `_create_mock_texture` bằng hàm gọi Model Inference thực thụ.
  - Quản lý VRAM: thiết kế cơ chế (Singleton) nạp model weights vào GPU đúng 1 lần khi server start để tránh Overhead nạp model mỗi luồng.
  
#### [MODIFY] Bend/app/main_api.py
  - Khai báo lifecycle event (ví dụ `lifespan`) để load sẵn model PyTorch/ONNX vào bộ nhớ, tránh tình trạng "khởi động lạnh" mất 5-10 giây cho mỗi request từ VR.

---

### 3. Queue / Async Workflow
Mặc dù Tùng đã xử lý cơ chế Polling và Background Thread (`TaskManager`) khá ổn định, nhưng đối với model nặng (như Diffusion chạy mất 20s-30s), Thread thông thường trong Python có thể gặp tắc nghẽn GIL (Global Interpreter Lock).

#### [MODIFY] Bend/app/services/tasks.py
  - Nâng cấp `TaskManager` hiện hữu nếu cần thiết, hoặc áp dụng hàng đợi đa tiến trình (`concurrent.futures.ProcessPoolExecutor`) để việc load CUDA/Tensor không chặn luồng chạy của ứng dụng FastAPI. Lựa chọn này gọn nhẹ hơn Celery (tránh phải cài thêm Redis/RabbitMQ quá rườm rà cho dự án đồ án nhỏ).

---

### 4. Benchmarking
Viết các script độ lường độc lập để lập báo cáo đánh giá hệ thống.

#### [NEW] Bend/scripts/benchmark_latency.py
  - Script tự động gửi hàng loạt request đến `/tasks/generate-texture` và thống kê thời gian phản hồi (TTFB) và tổng thời gian hoàn thành.
#### [NEW] Bend/scripts/benchmark_vram.py
  - Tích hợp `pynvml` (hoặc nvidia-smi interface) để đo đếm peak memory usage trên Card RTX 3060 trong quá trình Inference.

## User Review Required

> [!WARNING]
> Mảng Generative AI rủi ro tràn VRAM rất lớn trên Card 4GB/6GB/12GB! Cách thiết kế cấu trúc Dataset và Queue phục thuộc rất lớn vào kích thước file model (size parameters) và cách xử lý input.

## Verification Plan
1. **Automated Tests**: Dùng Postman hoặc script Python gửi luồng request, đảm bảo hệ thống xếp hàng ảnh đợi xử lý mà không bị nghẽn (crash web server).
2. **Manual Verification**: Theo dõi `nvidia-smi` để đảm bảo GPU Usage không bị rỉ bộ nhớ (memory leak) sau 10 lần gọi fitting liên tiếp.
