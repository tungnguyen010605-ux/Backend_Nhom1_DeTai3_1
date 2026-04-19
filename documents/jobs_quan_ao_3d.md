# Jobs Phần Quần Áo 3D

## 1) Mục tiêu

- Hoàn thiện pipeline quần áo 3D để thay đổi trang phục thật, không chỉ đổi texture.

## 2) Danh sách job chi tiết

## Job C1: Chốt danh mục 4 trang phục

- Mô tả: Chọn 4 món ưu tiên và xác định style rõ ràng.
- Đầu ra: Danh sách 4 món + ảnh tham chiếu + yêu cầu kỹ thuật.
- Trạng thái: Not Started

## Job C2: Thu thập/mua asset 3D

- Mô tả: Tìm nguồn asset hợp pháp, phù hợp license đồ án.
- Đầu ra: 4 file model thô + thông tin license.
- Trạng thái: Not Started

## Job C3: Chuẩn hóa rig và scale

- Mô tả: Đồng bộ rig theo skeleton chuẩn của avatar mục tiêu.
- Đầu ra: 4 bộ quần áo rigged tương thích.
- Trạng thái: Not Started

## Job C4: Chuẩn hóa vật liệu và texture

- Mô tả: Cân bằng material để hiển thị đồng nhất trong VR.
- Đầu ra: Bộ material/texture tối ưu cho từng trang phục.
- Trạng thái: Not Started

## Job C5: Thiết lập prefab runtime trong Unity

- Mô tả: Tạo prefab + script để thay trang phục theo lựa chọn.
- Đầu ra: Hệ thống switch outfit runtime ổn định.
- Trạng thái: Not Started

## Job C6: Chống clipping mức cơ bản

- Mô tả: Fix clipping ở các pose chính (đứng, đi, ngồi nhẹ).
- Đầu ra: Bộ outfit pass test pose cơ bản.
- Trạng thái: Not Started

## Job C7: Kết nối metadata với backend

- Mô tả: Mở rộng dữ liệu clothing item để tham chiếu model 3D.
- Đầu ra: Trường metadata cho model path, category, body compatibility.
- Trạng thái: Not Started

## Job C8: Viết checklist QA cho quần áo

- Mô tả: Chuẩn hóa các bước kiểm tra chất lượng mỗi outfit.
- Đầu ra: Checklist QA dùng chung cho team.
- Trạng thái: Not Started

## 3) Ưu tiên triển khai

- Ưu tiên 1: C1 -> C3 -> C5
- Ưu tiên 2: C4 -> C6
- Ưu tiên 3: C7 -> C8

## 4) Định nghĩa hoàn thành phần quần áo

- 4/4 outfit thay được trong runtime.
- Không lỗi rig nghiêm trọng.
- Clipping giảm đáng kể ở pose cơ bản.
- Có metadata kết nối được với luồng backend/user.
