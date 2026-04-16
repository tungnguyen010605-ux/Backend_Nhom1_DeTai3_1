# Dữ liệu từ `smoke_test.py`

## Tổng quan
File `smoke_test.py` thực hiện kiểm thử end-to-end cho các luồng:
- Upload ảnh tham chiếu người dùng
- Lấy danh sách user
- Xác thực clothing item mục tiêu đã tồn tại
- Lấy mock VR body data
- Preprocess ảnh
- Tạo task sinh texture + polling trạng thái
- Kiểm tra DB record `ClothingItem` tương ứng sau khi task hoàn tất

## Dữ liệu đầu vào

### ID cố định dùng trong smoke test
- `user_id = 22`
- `clothing_item_id = 31`

### Các bản ghi quần đã bổ sung cho `user_id=22`
- `clothing_id=32`, `category=pants:jeans`, `size_label=L`, `color=navy`
- `clothing_id=33`, `category=pants:trouser`, `size_label=L`, `color=black`

### 1) `user_payload`
> Mục này chỉ dùng khi bạn muốn tạo mới user thủ công trước test. `smoke_test.py` hiện tại không gọi `POST /users`.

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

### 2) Upload ảnh tham chiếu user
- Endpoint: `POST /users/{user_id}/reference-image`
- Content-Type: `multipart/form-data`
- Form-data:
  - `file`: ảnh người tham chiếu

- File dùng trong smoke test:
  - `Bend/static/person_images/serious-young-man-standing-against-white-background-photo.jpg`
  - MIME: `image/jpeg`

### 3) Clothing item mục tiêu (dùng record có sẵn)
- Không tạo mới trong smoke test.
- Dùng bản ghi cố định:

```json
{
  "user_id": 22,
  "clothing_item_id": 31
}
```

### 4) Payload tạo task texture
```json
{
  "user_id": 22,
  "clothing_item_id": 31
}
```

### 5) Dữ liệu preprocess ảnh
- Loại ảnh dùng trong `smoke_test.py`: ảnh người tham chiếu thật.
- File upload:
  - `serious-young-man-standing-against-white-background-photo.jpg`
  - MIME: `image/jpeg`
- Query params:
  - `width=256`
  - `height=256`
  - `normalize=true`
  - `augment=false`

### 6) Yêu cầu ảnh cho môi trường thực tế (tách riêng khỏi smoke test)
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
1. `POST /users/22/reference-image`
  - Body: multipart/form-data (`file`)
2. `GET /users`
  - Body: không có
3. `GET /clothing-items?user_id=22`
  - Body: không có
4. `GET /mock/vr/body/22`
  - Body: không có
5. `POST /preprocess?width=256&height=256&normalize=true&augment=false`
  - Body: multipart/form-data (`file` = ảnh người)
6. `POST /tasks/generate-texture`
  - Body: `{"user_id":22,"clothing_item_id":31}`
7. `GET /status/{task_id}`
  - Body: không có
  - Polling tối đa 15 lần, mỗi lần chờ `0.2s`

## Điều kiện kiểm tra (assert)
- `POST /users/22/reference-image` trả `200`
- `GET /users` trả `200` và có `user_id=22`
- `GET /clothing-items?user_id=22` trả `200` và có `clothing_id=31`
- `GET /mock/vr/body/22` trả `200`
- `POST /preprocess` trả `200`
- `POST /tasks/generate-texture` trả `200`
- Polling `/status/{task_id}` phải đạt `status == "completed"` trong giới hạn cho phép
- DB check:
  - Tìm thấy `ClothingItem` theo `clothing_id=31`
  - `status.output_url` tồn tại
  - Nếu `ClothingItem.image_path` đang là đường dẫn `/textures/...` thì phải khớp `output_url`

## Thư viện/đối tượng được dùng trong test
- `fastapi.testclient.TestClient`
- `pathlib.Path`
- `app.database.SessionLocal`
- `app.models.ClothingItem`
- `time.sleep`

## Đầu ra mong đợi
- Nếu tất cả đúng, in ra:
```text
Smoke test passed
```




