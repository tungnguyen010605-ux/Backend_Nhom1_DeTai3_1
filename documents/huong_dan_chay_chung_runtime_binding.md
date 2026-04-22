# Hướng Dẫn Chạy Chung Sau Khi Đã Tạo Xong User Và Quần Áo

## 1. Trạng thái hiện tại của bạn
Bạn đã đi đúng luồng backend:
- Dùng user sẵn có: id=14
- Dùng clothing item sẵn có: id=20
- Task tạo texture đã chạy thành công 100%

Điều này xác nhận phần backend và pipeline tạo ảnh đầu ra đã ổn.
Bước tiếp theo là cấu hình Runtime Bindings trong Unity để kiểm tra luồng outfit 3D (prefab) hoạt động đúng.

## 2. Cần làm gì tiếp theo ngay bây giờ
1. Xác nhận item id=20 trong UI/backend đang ở render_mode nào.
2. Nếu render_mode là texture:
- Runtime binding sẽ không được bật.
- Bạn chỉ cần kiểm tra đổi texture đúng slot.
3. Nếu render_mode là prefab:
- Bắt buộc phải cấu hình đúng runtimeBindings trong Unity.
- Nếu thiếu hoặc sai map, hệ thống sẽ báo chưa map runtime binding.

## 3. Giải thích từng trường trong Runtime Bindings
Mỗi phần tử trong runtimeBindings gồm các trường sau:

### 3.1 modelPath
- Mục đích: khóa định danh để match với model_path từ backend.
- Quy tắc: phải trùng 100% với model_path của clothing item (nội dung, dấu gạch chéo, tên).
- Ví dụ: outfits/josh/jacket_black_v1
- Lưu ý: sai 1 ký tự là không match.

### 3.2 slot
- Mục đích: chỉ định binding này thuộc vùng nào trên cơ thể.
- Giá trị nên dùng: top, bottom, shoes.
- Khuyến nghị: điền đúng slot của item backend để tránh bật/tắt nhầm outfit.

### 3.3 rootObject
- Mục đích: GameObject outfit 3D sẽ bật khi item được apply.
- Cách điền: kéo thả object outfit trong Hierarchy vào trường này.
- Bắt buộc: Có. Nếu trống thì binding coi như không hợp lệ.

### 3.4 previewRenderer
- Mục đích: renderer nhận preview texture (nếu có) lên outfit vừa bật.
- Cách dùng: thường là renderer chính của rootObject hoặc mesh con đại diện bề mặt vải.
- Có thể để trống nếu outfit prefab đã có material hoàn chỉnh và không cần dán preview.

### 3.5 previewMaterialIndex
- Mục đích: chọn material slot để dán preview texture.
- Chỉ số bắt đầu từ 0.
- Ví dụ: material đầu tiên là 0, material thứ hai là 1.

### 3.6 hideBaseRenderer
- Mục đích: khi bật outfit 3D thì có ẩn renderer cơ thể gốc của slot đó hay không.
- Giá trị khuyến nghị:
  - true: với áo/quần/giày mặc chồng lên base để tránh lộ xuyên mesh.
  - false: khi outfit chỉ là phụ kiện hoặc cần giữ bề mặt gốc.

## 4. Công thức cấu hình nhanh cho 1 item prefab
Áp dụng cho mỗi item có render_mode = prefab:
1. Mở object có script RemyWardrobeViewer.
2. Bật preferRuntimeBindings.
3. Trong runtimeBindings, bấm Add.
4. Điền:
- modelPath = model_path từ backend
- slot = top hoặc bottom hoặc shoes
- rootObject = outfit prefab instance trong scene
- previewRenderer = renderer chính của outfit (nếu cần)
- previewMaterialIndex = 0 (test trước, chỉnh sau nếu sai)
- hideBaseRenderer = true
5. Đảm bảo rootObject ban đầu đang tắt (hoặc để script tự tắt khi Start).
6. Chạy Play và apply item tương ứng.

## 5. Checklist test thực tế trong Unity

### TC-A: Item texture
1. Chọn item texture.
2. Apply.
Kỳ vọng:
- Đổi texture thành công.
- Không bật rootObject của runtime binding.

### TC-B: Item prefab map đúng
1. Chọn item prefab đã map đúng modelPath.
2. Apply.
Kỳ vọng:
- rootObject tương ứng được bật.
- Base renderer của slot bị ẩn nếu hideBaseRenderer=true.

### TC-C: Item prefab map sai
1. Cố tình đổi modelPath trong runtime binding khác với backend.
2. Apply.
Kỳ vọng:
- Không crash.
- Không bật nhầm outfit.
- Có cảnh báo chưa map runtime binding.

### TC-D: Reset outfit
1. Sau khi mặc prefab, gọi ResetOutfit.
Kỳ vọng:
- Tắt tất cả runtime bindings.
- Trả renderer gốc về trạng thái hiển thị.
- Texture mặc định được phục hồi.

## 6. Cách quyết định "đã xong"
Có thể coi là xong phần tích hợp runtime khi thỏa cả 4 điều kiện:
1. Item texture chạy đúng, không bật outfit 3D.
2. Item prefab bật đúng rootObject theo modelPath.
3. Không còn hiện tượng trắng do map sai hoặc thiếu binding.
4. ResetOutfit trả trạng thái về bình thường.

## 7. Lỗi thường gặp và cách xử lý nhanh
- Không bật outfit prefab:
  - Kiểm tra render_mode có phải prefab không.
  - Kiểm tra model_path backend và modelPath binding có trùng tuyệt đối không.
  - Kiểm tra rootObject đã gán chưa.
- Bật sai outfit:
  - Có nhiều binding trùng modelPath hoặc slot không đúng.
  - Sửa lại slot và modelPath duy nhất.
- Outfit bị xuyên với cơ thể gốc:
  - Bật hideBaseRenderer=true cho slot tương ứng.
- Preview không dán lên outfit:
  - Gán previewRenderer đúng object.
  - Chỉnh previewMaterialIndex đúng material slot.
