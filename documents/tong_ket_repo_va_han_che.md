# Tổng Kết Repo Backend_Nhom1_DeTai3_1

## 1. Thông tin chung

- Tên repo: Backend_Nhom1_DeTai3_1
- Mục tiêu chính: Xây dựng hệ thống backend phục vụ quy trình thử đồ ảo, bao gồm quản lý người dùng, số đo cơ thể, dữ liệu quần áo, tiền xử lý ảnh và sinh texture phục vụ VR.
- Trạng thái hiện tại: Đã hoàn thiện luồng chạy end-to-end ở mức demo học thuật, có benchmark cơ bản, có smoke test, có tài liệu định hướng Phase C.

## 2. Những gì repo đã làm được

### 2.1. Nền tảng backend và dữ liệu

- Xây dựng API bằng FastAPI với cấu trúc module rõ ràng.
- Thiết kế schema dữ liệu với SQLAlchemy và SQLite cho:
  - Hồ sơ người dùng.
  - Số đo cơ thể theo thời điểm.
  - Danh sách trang phục theo người dùng.
- Cung cấp các API CRUD nền tảng để:
  - Tạo và truy vấn user.
  - Tạo và truy vấn body measurements.
  - Tạo và truy vấn clothing items.

### 2.2. Luồng xử lý AI thử đồ

- Đã có cơ chế runtime model dạng singleton để giảm chi phí khởi tạo lặp lại.
- Đã tích hợp preload model ở lifecycle khởi động ứng dụng.
- Đã thay thế luồng mock cơ bản bằng luồng inference backend theo task.
- Đã hỗ trợ kết nối checkpoint CP-VTON TOM ở mức tương thích:
  - Có đọc nhiều định dạng state_dict thường gặp.
  - Có xử lý prefix module. trong key.
- Đã có cơ chế fallback khi thiếu checkpoint hoặc lỗi inference để hệ thống không dừng đột ngột.

### 2.3. Quản lý tác vụ bất đồng bộ

- Đã có TaskManager để tạo task sinh texture và theo dõi trạng thái.
- Đã có polling status cho client VR/frontend.
- Đã giới hạn số tác vụ đồng thời để tránh quá tải tài nguyên.

### 2.4. Quản lý ảnh và static assets

- Đã có endpoint upload ảnh tham chiếu người dùng.
- Đã có endpoint upload/quản lý ảnh quần áo.
- Đã mount static files cho:
  - Texture output.
  - Ảnh quần áo.
  - Ảnh người dùng.
- Đã có logic resolve input inference từ dữ liệu DB và đường dẫn asset.

### 2.5. Tiền xử lý và kiểm thử

- Đã có endpoint preprocess ảnh với các tham số kích thước/chuẩn hóa.
- Đã có smoke test cho luồng chính từ upload ảnh đến generate texture.
- Đã có tài liệu mô tả dữ liệu smoke test và thứ tự gọi API.

### 2.6. Đo hiệu năng cơ bản

- Đã có script benchmark latency cho luồng generate texture.
- Đã có script benchmark VRAM (qua pynvml) để theo dõi mức dùng GPU.
- Đã có script chạy benchmark local theo kiểu orchestration một lệnh.

### 2.7. Vệ sinh dữ liệu và tài liệu hóa

- Đã có script dọn dữ liệu test/rác trong SQLite kèm backup.
- Đã có chế độ strict cleanup để xử lý mạnh hơn.
- Đã có tài liệu backlog cho Phase C (avatar deformation).
- Đã có tài liệu handover trạng thái Phase B.

## 3. Giá trị kỹ thuật đã đạt được

- Hệ thống đã chứng minh được tính khả thi end-to-end của bài toán trong phạm vi đồ án.
- Kiến trúc tách lớp tương đối rõ giữa API, service, model runtime và script vận hành.
- Có khả năng trình diễn thực tế với client VR thông qua cơ chế task + polling.
- Có nền tảng để tiếp tục nâng cấp chất lượng model mà không phải viết lại toàn bộ backend.

## 4. Hạn chế hiện tại của repo

### 4.1. Hạn chế về chất lượng mô hình thử đồ

- Pipeline preprocess chưa đạt mức đầy đủ theo chuẩn CP-VTON thực chiến:
  - Chưa hoàn thiện bộ artifact chuẩn như agnostic person, cloth mask, pose map ở mức production.
- Chất lượng ảnh output chưa có bộ tiêu chí định lượng chính thức để so sánh giữa các phiên bản.

### 4.2. Hạn chế về độ tin cậy vận hành

- Cơ chế fallback giúp hệ thống không crash, nhưng có thể che khuất lỗi inference/model nếu không có logging đủ rõ.
- Chưa có chiến lược versioning checkpoint và rollback chặt chẽ cho môi trường demo nhiều lần cập nhật.

### 4.3. Hạn chế về lưu vết kết quả

- Chiến lược lưu output texture hiện chưa tối ưu cho truy vết lịch sử nhiều lần generate.
- Chưa có mô hình dữ liệu riêng cho lịch sử task output để phục vụ audit, so sánh chất lượng hoặc khôi phục.

### 4.4. Hạn chế về khả năng mở rộng

- Luồng song song hiện dựa trên ThreadPoolExecutor, phù hợp mức demo nhưng cần đánh giá thêm khi tải nặng.
- Khi tăng số người dùng đồng thời hoặc model nặng hơn, cần kiến trúc worker/queue rõ ràng hơn.

### 4.5. Hạn chế về mức độ “ý nghĩa hình thể” trong VR

- Ở hiện trạng, thử đồ chủ yếu thay đổi texture.
- Số đo cơ thể chưa được ánh xạ đầy đủ thành biến đổi hình học avatar.
- Do đó, mức phản ánh “vừa form cơ thể” chưa thật sự trực quan ở VR.

## 5. Các rủi ro chính

- Rủi ro suy giảm chất lượng khi thay checkpoint mà không có bộ metric chuẩn.
- Rủi ro khó debug khi lỗi bị fallback âm thầm.
- Rủi ro phụ thuộc dữ liệu test cứng (ID cố định) làm smoke test thiếu ổn định khi DB thay đổi.
- Rủi ro hiệu năng khi mở rộng quy mô mà chưa tái thiết kế queue/worker.

## 6. Định hướng cải tiến tiếp theo

### 6.1. Ngắn hạn

- Chuẩn hóa preprocess đúng profile CP-VTON dùng trong huấn luyện và suy luận.
- Bổ sung logging, error code và cảnh báo rõ khi runtime đi vào nhánh fallback.
- Sửa smoke test theo hướng tự seed dữ liệu thay vì phụ thuộc ID cố định.
- Chuẩn hóa tài liệu vận hành và đường dẫn phụ thuộc để tránh lệch giữa code và README.

### 6.2. Trung hạn

- Bổ sung bảng lịch sử output theo task.
- Thiết lập bộ metric chất lượng ảnh (FID/LPIPS hoặc proxy phù hợp phạm vi đồ án).
- Thiết kế quy trình versioning checkpoint và rollback.

### 6.3. Dài hạn (Phase C)

- Triển khai avatar deformation (blendshape hoặc bone scaling) để số đo cơ thể tác động trực quan lên hình thể.
- Đồng bộ texture fitting và shape fitting để cải thiện cảm nhận “độ vừa” trong VR.

## 7. Kết luận

Repo hiện tại đã đạt mốc quan trọng: chạy được pipeline thử đồ ảo từ API đến texture output trong môi trường demo, có kiểm thử cơ bản, có đo hiệu năng nền và có tài liệu định hướng tiếp theo.

Điểm còn thiếu không nằm ở việc “có chạy được hay không”, mà nằm ở mức độ hoàn thiện sản phẩm: chất lượng mô hình, khả năng quan sát lỗi, lưu vết kết quả, mở rộng tải và biến đổi hình thể avatar. Nếu hoàn thiện các điểm này, repo có thể nâng từ mức demo kỹ thuật lên mức prototype ổn định hơn cho trình diễn và đánh giá học thuật.
