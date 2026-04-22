# UI Test Checklist - Quần Áo 3D (Unity + Backend)

## 1. Mục tiêu
Tài liệu này dùng để test end-to-end luồng thử đồ với 2 chế độ:
- texture: phủ texture lên renderer hiện có
- prefab: bật outfit 3D theo model_path

## 2. Điều kiện trước khi test
- Backend đang chạy và truy cập được:
  - /health trả về status ok
  - /ui mở được giao diện test
- Unity scene đã mở và có object gắn script RemyWardrobeViewer
- Trong Unity Inspector:
  - preferRuntimeBindings đã bật
  - đã tạo ít nhất 1 runtime binding cho item prefab

## 3. Dữ liệu test tối thiểu
Tạo 2 clothing item trong UI:

### 3.1 Item A (texture)
- Tên hiển thị: Tshirt blue test
- Nhóm category: Áo
- Loại quần áo: Tshirt
- Runtime slot: top
- Size: M
- Màu sắc: blue
- Render mode: texture
- Model path: để trống
- Body compatibility (CSV): regular
- Ghi chú runtime: để trống hoặc ghi ngắn
- Ảnh quần áo: upload PNG/JPG

### 3.2 Item B (prefab)
- Tên hiển thị: Jacket black prefab
- Nhóm category: Áo
- Loại quần áo: Jacket
- Runtime slot: top
- Size: M
- Màu sắc: black
- Render mode: prefab
- Model path: outfits/josh/jacket_black_v1
- Body compatibility (CSV): slim, regular
- Ghi chú runtime: hide base top
- Ảnh quần áo: upload 1 ảnh preview (khuyến nghị)

Lưu ý:
- model_path của item prefab phải trùng 100% với modelPath trong runtimeBindings của Unity.
- Nếu Render mode là texture, Model path nên để trống.

## 4. Test case chính

### TC01 - Tạo item texture thành công
Bước test:
1. Chuyển sang Tạo clothing item mới.
2. Nhập thông tin theo Item A.
3. Bấm Chạy luồng thử đồ.

Kỳ vọng:
- Không lỗi 422.
- Item được tạo trong danh sách clothing.
- Khi apply, avatar đổi texture đúng slot, không bật outfit 3D.

### TC02 - Tạo item prefab thành công
Bước test:
1. Tạo item theo Item B.
2. Bấm Chạy luồng thử đồ.

Kỳ vọng:
- Không lỗi 422.
- Item được tạo và lưu render_mode = prefab.
- Unity bật rootObject của runtime binding tương ứng.
- Base renderer slot đó bị ẩn nếu hideBaseRenderer = true.

### TC03 - Validation render_mode
Bước test:
1. Gửi request tạo clothing item với render_mode sai giá trị (ví dụ: abc) qua Swagger hoặc API client.

Kỳ vọng:
- API trả 422 (không chấp nhận giá trị ngoài texture/prefab).

### TC04 - Prefab mode nhưng thiếu model_path
Bước test:
1. Tạo item render_mode = prefab và để model_path trống.
2. Thử apply trên Unity.

Kỳ vọng:
- Không crash.
- Không bật nhầm runtime binding.
- Viewer hiện cảnh báo thiếu model_path.

### TC05 - model_path không map được runtime binding
Bước test:
1. Tạo item prefab với model_path không tồn tại trong runtimeBindings.
2. Thử apply.

Kỳ vọng:
- Không crash.
- Không bật sai outfit.
- Viewer hiện cảnh báo chưa map runtime binding.

### TC06 - Reset outfit
Bước test:
1. Apply 1 item prefab.
2. Bấm ResetOutfit trên viewer.

Kỳ vọng:
- Tắt tất cả runtime bindings.
- Hiện lại base renderer.
- Texture trở về mặc định.

## 5. Bảng ghi nhanh kết quả
| Test case | Kết quả (Pass/Fail) | Ghi chú |
|---|---|---|
| TC01 |  |  |
| TC02 |  |  |
| TC03 |  |  |
| TC04 |  |  |
| TC05 |  |  |
| TC06 |  |  |

## 6. Tiêu chí coi như xong phần chuẩn bị quần áo
- TC01 pass
- TC02 pass
- TC03 pass
- TC04 pass
- TC05 pass
- TC06 pass
- Không còn hiện tượng item texture bị bật runtime binding.
- Không còn lỗi trang phục trắng do map sai mode/slot.
