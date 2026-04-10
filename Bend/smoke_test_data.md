# Dữ liệu từ `smoke_test.py`

## Tổng quan
File `smoke_test.py` thực hiện kiểm thử end-to-end cho các luồng:
- Tạo user
- Lấy danh sách user
- Tạo clothing item
- Lấy mock VR body data
- Preprocess ảnh
- Tạo task sinh texture + polling trạng thái
- Kiểm tra DB đã persist `ClothingItem.image_path`

## Dữ liệu đầu vào

### 1) `user_payload`
```json
{
  "name": "Test User",
  "height_cm": 172,
  "chest_cm": 94,
  "waist_cm": 78,
  "hip_cm": 96,
  "inseam_cm": 79
}
```

### 2) `cloth_payload`
```json
{
  "user_id": "<user_id từ /users>",
  "category": "shirt",
  "size_label": "M",
  "color": "blue"
}
```

### 3) Payload tạo task texture
```json
{
  "user_id": "<user_id>",
  "clothing_item_id": "<cloth_id>"
}
```

### 4) Dữ liệu preprocess ảnh
- Loại ảnh yêu cầu trong `smoke_test.py`: **ảnh PNG bất kỳ** (ảnh test giả lập), không bắt buộc là ảnh quần áo hoặc ảnh dáng người mặc quần áo.
- File upload: `in.png` (PNG, tạo trong bộ nhớ)
- Kích thước ảnh gốc: `128x128`, màu `(90, 140, 200)`
- Không yêu cầu trong smoke test này:
  - Ảnh quần áo riêng (flat lay/product photo)
  - Ảnh dáng người đang mặc quần áo
  - Ảnh pose/keypoint hoặc ảnh segmentation
- Query params:
  - `width=256`
  - `height=256`
  - `normalize=true`
  - `augment=false`

### 5) Yêu cầu ảnh cho môi trường thực tế (tách riêng khỏi smoke test)
- Mục tiêu: dùng ảnh thật để pipeline preprocess phục vụ thử đồ/texture có chất lượng ổn định.
- Loại ảnh nên dùng (production):
  - Ảnh quần áo riêng (flat lay hoặc ảnh sản phẩm rõ chi tiết vải) cho bài toán texture.
  - Ảnh người mặc quần áo (toàn thân hoặc nửa thân) cho bài toán fit/visual thử đồ.
- Không khuyến nghị: ảnh quá mờ, thiếu sáng, vật thể bị che khuất nhiều, hoặc ảnh nén mạnh gây mất chi tiết.
- Yêu cầu kỹ thuật khuyến nghị:
  - Định dạng: `PNG` hoặc `JPEG`.
  - Kích thước ảnh đầu vào: tối thiểu khoảng `512x512`, khuyến nghị `1024x1024` để giữ chi tiết.
  - Ánh sáng: đủ sáng, đều, hạn chế đổ bóng mạnh.
  - Nền ảnh: càng đơn giản càng tốt để giảm nhiễu.
  - Góc chụp: rõ đối tượng chính (quần áo/người), không bị cắt mất vùng quan trọng.
- Lưu ý: các yêu cầu trên áp dụng cho triển khai thực tế; **không bắt buộc** trong `smoke_test.py`.

## Thứ tự API được gọi
1. `POST /users`
2. `GET /users`
3. `POST /clothing-items`
4. `GET /mock/vr/body/{user_id}`
5. `POST /preprocess?width=256&height=256&normalize=true&augment=false`
6. `POST /tasks/generate-texture`
7. `GET /status/{task_id}` (lặp tối đa 15 lần, mỗi lần chờ `0.2s`)

## Điều kiện kiểm tra (assert)
- `POST /users` trả `200`
- `GET /users` trả `200` và có `user_id` vừa tạo
- `POST /clothing-items` trả `200`
- `GET /mock/vr/body/{user_id}` trả `200`
- `POST /preprocess` trả `200`
- `POST /tasks/generate-texture` trả `200`
- Polling `/status/{task_id}` phải đạt `status == "completed"` trong giới hạn cho phép
- DB check:
  - Tìm thấy `ClothingItem` theo `cloth_id`
  - `ClothingItem.image_path == output_url` từ task status

## Thư viện/đối tượng được dùng trong test
- `fastapi.testclient.TestClient`
- `PIL.Image`
- `app.database.SessionLocal`
- `app.models.ClothingItem`
- `time.sleep`

## Đầu ra mong đợi
- Nếu tất cả đúng, in ra:
```text
Smoke test passed
```




