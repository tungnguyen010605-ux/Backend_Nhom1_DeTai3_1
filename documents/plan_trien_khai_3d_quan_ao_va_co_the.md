# Plan Triển Khai 3D Quần Áo và Cơ Thể Avatar

## 1) Mục tiêu

- Chuyển từ mức thay đổi texture sang mức thay đổi trang phục 3D thực tế.
- Bổ sung hệ avatar nam/nữ với nhiều kiểu cơ thể để phản ánh khác biệt hình thể.
- Đảm bảo pipeline đủ ổn định để demo VR mượt và có tính thuyết phục.

## 2) Phạm vi triển khai

- 4 bộ quần áo 3D (ưu tiên các món bạn đã chọn).
- 2 avatar nam + 1 avatar nữ (giai đoạn đầu).
- Mỗi avatar có 2-3 body type cốt lõi: gầy, chuẩn, đầy đặn.
- Tích hợp chọn quần áo + body type từ dữ liệu backend.

## 3) Lộ trình theo giai đoạn

## Giai đoạn A: Chuẩn hóa asset (Tuần 1)

- Chốt danh sách 4 quần áo và yêu cầu kỹ thuật file.
- Chuẩn hóa rig, skeleton, scale, trục tọa độ cho toàn bộ asset.
- Tạo bảng quy chuẩn naming cho model/material/animation.

## Giai đoạn B: Avatar và body types (Tuần 1-2)

- Tạo bộ avatar nam/nữ dùng chung chuẩn rig.
- Tạo body preset (slim/normal/heavy, tall/short).
- Định nghĩa rule map số đo cơ thể sang body preset.

## Giai đoạn C: Gắn quần áo vào avatar (Tuần 2)

- Gắn 4 quần áo vào từng avatar/preset.
- Thiết lập hệ thay trang phục runtime trong Unity.
- Sửa lỗi clipping cơ bản ở các pose chính.

## Giai đoạn D: Kết nối backend + VR flow (Tuần 2-3)

- Bổ sung dữ liệu clothing 3D và body profile vào API.
- Đồng bộ logic chọn model theo giới tính + body type.
- Hoàn thiện flow thử đồ: chọn user -> chọn body -> chọn outfit -> render.

## Giai đoạn E: Test và khóa bàn giao (Tuần 3)

- Chạy test ma trận: giới tính x body type x outfit.
- Đánh giá FPS VR và chất lượng hiển thị.
- Chốt danh sách lỗi còn lại và khóa bản demo.

## 4) Tiêu chí hoàn thành

- Thay đồ phải thay đúng mesh/trang phục, không chỉ đổi màu.
- Có ít nhất 2 nhóm giới tính hoạt động ổn định: nam, nữ.
- Có khác biệt rõ về hình thể giữa các body presets.
- Tỷ lệ clipping ở các pose cơ bản trong ngưỡng chấp nhận được.
- FPS trong VR đạt mức demo mượt (do team tự chốt ngưỡng mục tiêu).

## 5) Rủi ro và phương án giảm rủi ro

- Rủi ro mismatch rig giữa asset: dùng một chuẩn skeleton duy nhất ngay từ đầu.
- Rủi ro nặng FPS: thêm LOD, giảm poly, tối ưu material.
- Rủi ro nổ khối lượng test: cố định ma trận test tối thiểu trước khi mở rộng.
- Rủi ro trễ tiến độ: ưu tiên bản tối thiểu khả dụng trước (4 outfit + 3 body presets).

## 6) Tài liệu liên quan

- documents/tong_ket_repo_va_han_che.md
- documents/phase_c_avatar_deformation_backlog.md
- documents/implementation_plan.md
