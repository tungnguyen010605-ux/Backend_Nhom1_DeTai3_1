# Jobs Phần Cơ Thể Avatar (Nam, Nữ, Các Kiểu Cơ Thể)

## 1) Mục tiêu

- Xây dựng hệ avatar nam/nữ có nhiều kiểu cơ thể để phản ánh dữ liệu người dùng thực tế.

## 2) Danh sách job chi tiết

## Job B1: Chốt bộ avatar gốc

- Mô tả: Chọn 2 avatar nam + 1 avatar nữ cùng chuẩn rig.
- Đầu ra: Bộ avatar base đã kiểm tra tương thích animation.
- Trạng thái: Not Started

## Job B2: Định nghĩa body types chuẩn

- Mô tả: Xác định các body type dùng cho demo.
- Gợi ý: slim, normal, heavy + biến thể cao/thấp.
- Đầu ra: Bộ quy tắc body type chính thức.
- Trạng thái: Not Started

## Job B3: Tạo body presets

- Mô tả: Tạo preset hình thể cho nam và nữ.
- Đầu ra: Preset cho từng body type áp dụng được runtime.
- Trạng thái: Not Started

## Job B4: Mapping số đo -> body type

- Mô tả: Thiết kế hàm quy đổi từ số đo (height/chest/waist/hip/inseam) sang preset.
- Đầu ra: Rule map rõ ràng, có bảng ngưỡng.
- Trạng thái: Not Started

## Job B5: Runtime applier

- Mô tả: Viết logic áp body preset vào avatar khi load user.
- Đầu ra: Script Unity áp dụng body preset tự động.
- Trạng thái: Not Started

## Job B6: Đồng bộ giới tính với hệ thống chọn avatar

- Mô tả: Bổ sung cờ giới tính/profile trong dữ liệu và flow chọn avatar.
- Đầu ra: User nam/nữ chọn đúng nhóm avatar.
- Trạng thái: Not Started

## Job B7: Test tương thích body x outfit

- Mô tả: Kiểm tra ma trận body type với 4 outfit.
- Đầu ra: Báo cáo lỗi clipping/méo mesh và cách xử lý.
- Trạng thái: Not Started

## Job B8: Tối ưu hiệu năng và khóa preset demo

- Mô tả: Chọn số preset tối ưu giữa chất lượng và FPS.
- Đầu ra: Danh sách preset cuối cùng dùng khi demo.
- Trạng thái: Not Started

## 3) Ưu tiên triển khai

- Ưu tiên 1: B1 -> B2 -> B3
- Ưu tiên 2: B4 -> B5 -> B6
- Ưu tiên 3: B7 -> B8

## 4) Định nghĩa hoàn thành phần cơ thể

- Có tối thiểu 2 nhóm giới tính hoạt động: nam và nữ.
- Có tối thiểu 3 body types chạy ổn định.
- Dữ liệu số đo tác động rõ tới ngoại hình avatar.
- Tỷ lệ lỗi hiển thị trong ma trận test ở mức chấp nhận được.
