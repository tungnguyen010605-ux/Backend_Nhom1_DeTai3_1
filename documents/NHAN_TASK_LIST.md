# Danh Sách Công Việc Cho Nhân

Ngày lập: 2026-04-13
Tham chiếu: Bend/documents/Jobs.txt và Bend/documents/Tech.txt.

## Mục tiêu vai trò
- [ ] Lead VR Client, 3D Integration, Rendering.
- [ ] Chịu trách nhiệm huấn luyện/inference nhóm AI fitting (theo phân công tài liệu).

## Checklist công việc theo Phase

### Phase A - VR Client nền tảng (ưu tiên cao)
- [ ] Tích hợp Oculus/Meta XR SDK vào Unity project.
- [x] Dựng avatar rig và hệ IK có thể nhận dữ liệu pose. (Hoàn thành tích hợp FBX Humanoid)
- [ ] Viết bộ map keypoints JSON -> bones transform.
- [ ] Tối ưu hiệu năng VR: dùng capsule/sphere collider cho khớp.
- [ ] Thiết lập fallback giảm cloth particles khi FPS < 72.

Tiêu chí hoàn thành (Definition of Done - Phase A)
- [ ] Chạy scene VR ổn định ở mức 72 FPS trở lên trong bài test có avatar.
- [ ] Avatar nhận data pose mock và thay đổi tư thế ổn định.
- [x] Có tài liệu setup Unity + XR package version. (Đã cấu hình .gitignore và .gitattributes)

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

### Phase C - Unity x Backend integration
- [x] Gọi API backend từ Unity.
- [x] Nhận task_id và theo dõi trạng thái (polling hoặc websocket).
- [x] Download texture và apply vào material avatar.
- [x] Xử lý retry, timeout, fallback UI.

Tiêu chí hoàn thành (Definition of Done - Phase C)
- [x] End-to-end demo: chọn user -> pose -> gọi fitting -> avatar mặc được texture mới. (Mock API)
- [x] Có log và màn hình status rõ ràng trong Unity.
- [x] Có checklist UAT cho nhóm.

## Việc cần phối hợp với Tùng và Niên
- [ ] Chốt schema JSON keypoints và body measurements dùng chung.
- [ ] Chốt API contract cho inference và status task.
- [ ] Chốt quy trình release model + backend + Unity theo cùng version.

## Backlog kỹ thuật nên tạo issue ngay
- [ ] Unity bridge: parser keypoints + mapping bone.
- [ ] Async client service trong Unity (status polling/websocket).
- [ ] Texture streaming cache cho avatar.
- [ ] Tool đo FPS/frametime trong scene VR.
- [ ] Kịch bản test Oculus Quest trên thư viện bài test có sẵn.

## Thứ tự làm để tránh blocker
- [ ] Làm xong khung Phase A trong Unity.
- [ ] Song song khởi động train/inference prototype cho Phase B.
- [ ] Khi endpoint ổn định, đồng bộ Phase C và chạy demo end-to-end.
