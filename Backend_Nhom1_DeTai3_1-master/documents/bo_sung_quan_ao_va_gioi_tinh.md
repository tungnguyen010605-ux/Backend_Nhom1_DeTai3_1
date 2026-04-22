# Bổ Sung Quản Lý Quần Áo Theo User Và Giới Tính

## 1) Mục tiêu cập nhật

- Lưu giới tính (`male`/`female`) cho user trong backend.
- Đồng bộ giới tính từ backend -> frontend -> Unity.
- Lọc danh sách quần áo theo đúng user đang chọn.
- Ngăn lỗi chạy chéo `user_id` và `clothing_item_id` của user khác.
- Hỗ trợ chọn avatar nam/nữ trong Unity (Remy/Megan) theo giới tính.

## 2) Thay đổi chính

## Backend

### 2.1 Dữ liệu user

- Thêm cột `gender` vào bảng `user_profiles`.
- Giá trị hợp lệ: `male`, `female`.
- Mặc định: `male`.

### 2.2 Schema API

- `UserCreate` có thêm field:
  - `gender: Literal["male", "female"] = "male"`
- `UserResponse` trả về kèm `gender`.

### 2.3 Migration dữ liệu cũ (SQLite)

- Tự thêm cột `gender` khi app khởi động nếu DB cũ chưa có cột.
- Backfill dữ liệu thiếu về `male` để tương thích ngược.

### 2.4 Ràng buộc an toàn khi chạy generate texture

- Endpoint `POST /tasks/generate-texture` đã bổ sung kiểm tra:
  - Nếu `clothing_item.user_id != payload.user_id` -> trả `400`.
- Mục đích: tránh chạy nhầm quần áo của user khác.

## Frontend (Web UI)

### 2.5 Form người dùng

- Thêm dropdown giới tính trong phần tạo user mới:
  - Nam (`male`)
  - Nữ (`female`)

### 2.6 Đồng bộ dữ liệu user

- Khi chọn user đã có:
  - Tự điền `name`, `gender`, số đo.
- Khi tạo user mới:
  - Payload gửi lên `/users` có `gender`.

### 2.7 Trạng thái input theo mode

- Mode `existing user`:
  - Khóa input thông tin user (`name`, `gender`, số đo) để tránh ghi đè nhầm.
- Mode `new user`:
  - Mở input để nhập mới.

### 2.8 Danh sách quần áo theo user

- FE gọi `/clothing-items?limit=500&user_id={selectedUserId}`.
- Dropdown quần áo chỉ hiển thị item của user đang chọn.
- Text UI đã đổi từ danh sách global sang danh sách theo user.

## Unity (VRBackendClient)

### 2.9 Đồng bộ giới tính -> avatar

- Panel có chọn giới tính Nam/Nữ.
- Tự bật avatar/viewer tương ứng:
  - Nam -> Remy
  - Nữ -> Megan
- Chỉ giữ active viewer phù hợp để tránh chồng logic.

### 2.10 Danh sách user trong panel

- Hiển thị user kèm giới tính.
- Lọc theo giới tính đang chọn.
- Sắp xếp theo bản ghi mới nhất (`id` giảm dần).

### 2.11 Danh sách quần áo trong panel

- Khi chọn user, fetch theo đúng `user_id`.
- Nếu user không có quần áo, hiển thị trạng thái rỗng rõ ràng.

## 3) Luồng hoạt động sau cập nhật

1. Chọn giới tính (hoặc để tự đồng bộ từ user).
2. Chọn user trong danh sách đã lọc theo giới tính.
3. Hệ thống load quần áo theo đúng user.
4. Chọn quần áo và chạy generate texture.
5. Backend kiểm tra ownership user-clothing trước khi tạo task.

## 4) Nguyên nhân lỗi cũ và cách đã xử lý

## Lỗi cũ

- Chọn `user_id = A` nhưng dùng `clothing_item_id` thuộc user `B` vẫn chạy được.
- Dẫn tới hiểu nhầm: tưởng user A có quần áo, nhưng thực tế item thuộc user khác.

## Cách xử lý

- FE đã lọc dropdown quần áo theo `user_id`.
- BE chặn cứng mismatch `user_id` và `clothing_item_id`.

## 5) Checklist test nhanh

- Tạo user mới `female`, xác nhận `/users` trả đúng `gender`.
- Chuyển qua mode existing, chọn user vừa tạo, xác nhận form fill đúng giới tính.
- Kiểm tra dropdown quần áo chỉ hiện item của user đang chọn.
- Gọi `POST /tasks/generate-texture` với user-clothing mismatch, kỳ vọng `400`.
- Trên Unity:
  - Chọn `Nữ` -> danh sách user chỉ còn nữ, avatar chuyển Megan.
  - Chọn `Nam` -> danh sách user chỉ còn nam, avatar chuyển Remy.

## 6) Ghi chú triển khai tiếp theo

- Có thể bổ sung map tự động `gender` -> preset body type khi bước body deformation hoàn thiện.
- Có thể thêm script seed dữ liệu demo để tạo nhanh user + clothing đúng ownership.
