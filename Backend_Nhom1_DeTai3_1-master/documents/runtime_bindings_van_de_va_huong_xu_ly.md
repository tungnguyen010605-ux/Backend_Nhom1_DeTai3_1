# Ghi Chú Vấn Đề Runtime Bindings (Prefab)

## 1. Bối cảnh
Trong backend đã có bản ghi clothing item với dữ liệu dạng:
- render_mode = prefab
- model_path = prefab/white-t-shirt
- image_path, preview_image_path có giá trị hợp lệ

Ví dụ thực tế đã tạo:
- user_id: 14
- id: 27
- display_name: Shirt trắng
- slot: top
- render_mode: prefab
- model_path: prefab/white-t-shirt

## 2. Vấn đề đang gặp
Dù đã có bản ghi prefab trong database, dự án vẫn không có prefab asset mới được tạo tự động trong Unity.

## 3. Kết luận kỹ thuật
Hệ thống hiện tại KHÔNG có cơ chế tự sinh prefab từ dữ liệu DB.

Ý nghĩa các trường hiện tại:
- render_mode = prefab: chỉ là cờ logic để chạy nhánh prefab trong runtime.
- model_path: chỉ là khóa định danh để so khớp với Runtime Binding trong Unity.

Điều này có nghĩa:
- DB không tạo file .prefab.
- Unity chỉ bật object đã được gán sẵn trong Inspector khi model_path khớp.

## 4. Hành vi thực tế của Runtime Bindings
Script RemyWardrobeViewer hiện làm các bước:
1. Lấy item từ catalog.
2. Nếu render_mode != prefab thì bỏ qua runtime binding.
3. Nếu render_mode = prefab thì tìm binding theo model_path + slot.
4. Nếu tìm thấy binding hợp lệ thì bật rootObject đã gán sẵn.

Không có bước nào:
- tạo prefab mới,
- load prefab tự động từ backend URL,
- instantiate prefab theo model_path nếu chưa tồn tại.

## 5. Tác động
- Nếu chỉ tạo bản ghi DB mà không cấu hình Runtime Bindings trong Unity, item prefab sẽ không mặc được.
- Cần map thủ công model_path -> rootObject (hoặc prefab instance trong scene).

## 6. Cách xử lý hiện tại (workaround)
1. Chuẩn bị outfit object/prefab trong Unity trước.
2. Mở object chứa RemyWardrobeViewer.
3. Thêm 1 Runtime Binding với:
- Model Path: trùng 100% model_path trong DB (ví dụ prefab/white-t-shirt)
- Slot: top/bottom/shoes đúng với item
- Root Object: object outfit cần bật
- Hide Base Renderer: bật nếu muốn ẩn áo/quần base
4. Chạy Play và apply item prefab để kiểm thử.

## 7. Đề xuất cải tiến sau này
Có thể triển khai 1 trong 2 hướng:

### Hướng A: Auto-bind theo bảng map local
- Tạo file cấu hình local (model_path -> prefab reference).
- Khi load catalog, script tự map binding thay vì kéo tay Inspector.

### Hướng B: Runtime loader theo Addressables/Resources
- Quy ước model_path thành key asset.
- Load và instantiate prefab theo key lúc runtime.
- Giảm phụ thuộc vào cấu hình thủ công trong scene.

## 8. Tiêu chí xác nhận đã xử lý đúng
- Item prefab chỉ cần chọn trong catalog là bật đúng outfit.
- Không còn lỗi không map do thiếu binding thủ công.
- Quy trình thêm item prefab mới không cần kéo thả nhiều bước trong Inspector.
