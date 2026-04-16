# Danh Sách Công Việc Cho Nhân

Ngày lập: 2026-04-13
Tham chiếu: Bend/documents/Jobs.txt và Bend/documents/Tech.txt.

## Mục tiêu vai trò
- [ ] Lead VR Client, 3D Integration, Rendering.
- [ ] Chịu trách nhiệm huấn luyện/inference nhóm AI fitting (theo phân công tài liệu).

## Checklist công việc theo Phase

### Phase A - VR Client nền tảng (ưu tiên cao)
- [~] Cải thiện độ chính xác mapping cho pose khó (ngồi/chân gập/sai khác lớn so với đứng). (Tạm thời bỏ qua theo yêu cầu)

Tiêu chí hoàn thành (Definition of Done - Phase A)
- [~] Avatar nhận data pose mock và thay đổi tư thế ổn định.

### Phase B - AI Fitting backend (theo phân công Nhân)
- [ ] Chuẩn bị pipeline train GAN/Diffusion trên dữ liệu đã preprocess.
- [ ] Tạo API inference backend (input: ảnh người + quần áo, output: ảnh fitting/texture).
- [ ] Thêm queue/async workflow để tránh timeout.
- [ ] Đo benchmark latency mỗi request.
- [ ] Đo benchmark VRAM sử dụng.
- [ ] Đo benchmark tỷ lệ lỗi.

Tiêu chí hoàn thành (Definition of Done - Phase B)
- [ ] Có endpoint inference chạy được trên máy RTX 3060.
- [ ] Có tài liệu model version, checkpoint và tham số chạy.
- [ ] Có script benchmark và kết quả baseline.

## Việc cần phối hợp với Tùng và Niên
- [ ] Chốt schema JSON keypoints và body measurements dùng chung.
- [ ] Chốt API contract cho inference và status task.
- [ ] Chốt quy trình release model + backend + Unity theo cùng version.

## Backlog kỹ thuật nên tạo issue ngay
- [x] Unity bridge: parser keypoints + mapping bone. (Baseline voi `VRPoseSyncClient.cs`)
- [ ] Async client service trong Unity (status polling/websocket).
- [ ] Texture streaming cache cho avatar. (Đã bỏ cache để giảm RAM)
- [x] Tool đo FPS/frametime trong scene VR. (Da them `VRPerformanceMonitor.cs`)
- [ ] Kịch bản test Oculus Quest trên thư viện bài test có sẵn.

## Thứ tự làm để tránh blocker
- [ ] Làm xong khung Phase A trong Unity.
- [ ] Song song khởi động train/inference prototype cho Phase B.
- [ ] Khi endpoint ổn định, đồng bộ Phase C và chạy demo end-to-end.
