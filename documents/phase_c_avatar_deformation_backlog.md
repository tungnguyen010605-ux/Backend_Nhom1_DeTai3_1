# Phase C Backlog: Avatar Deformation and Body-Meaningful Fitting

## Why this backlog exists

Hiện tại pipeline AI đã có thể sinh texture và chạy end-to-end trong VR. Tuy nhiên nếu chỉ dùng một avatar form cố định (ví dụ Remy), thì số đo cơ thể (height/chest/waist/hip/inseam) chưa phản ánh đúng khác biệt hình thể người dùng.

Tài liệu này gom phần việc "để xử lý sau" nhằm biến body measurements thành thay đổi trực quan thực sự trong VR.

## Current limitation

- Một avatar form cố định cho nhiều user khác nhau.
- Texture fitting chạy được nhưng shape fitting còn yếu.
- Kết quả "vừa hay không vừa" chưa đáng tin khi body frame không biến đổi.

## Target outcome (Phase C)

- User khác nhau cho ra silhouette khác nhau trong VR.
- Body measurements tác động trực tiếp vào shape avatar.
- Quần áo hiển thị nhất quán giữa texture và body form.

## Scope options

### Option A - Blendshape Mapping (recommended for project scale)

- Chuẩn bị avatar có các blendshape chính:
  - chest_up/down
  - waist_in/out
  - hip_in/out
  - arm_thick/thin
  - leg_thick/thin
  - shoulder_wide/narrow
  - height_short/tall (hoặc tách qua skeleton scale)
- Xây mapper từ measurements -> blendshape weights (0..100).
- Ưu điểm: triển khai nhanh, dễ debug trong Unity.
- Nhược điểm: phụ thuộc chất lượng rig/avatar.

### Option B - Multi-Base Body Archetypes

- Tạo nhiều base body (male/female + slim/normal/plus).
- Chọn base gần nhất theo số đo rồi tinh chỉnh nhẹ bằng blendshape.
- Ưu điểm: ổn định hơn khi khoảng chênh lệch body lớn.
- Nhược điểm: tốn asset và logic chọn base.

### Option C - Parametric Body Model (SMPL/SMPL-X)

- Dùng model tham số cơ thể để dựng mesh theo shape vector.
- Ưu điểm: chuẩn nghiên cứu.
- Nhược điểm: phức tạp, nặng triển khai cho timeline đồ án.

## Recommended path for this repo

1. Làm Option A trước (blendshape mapping).
2. Nếu còn thời gian, bổ sung Option B với 2-4 base body.
3. Không ưu tiên Option C trong scope hiện tại.

## Proposed technical tasks

1. Add measurements fields (if needed): shoulder, arm_length, thigh, calf, neck.
2. Define mapping ranges:
   - Ví dụ chest 80..120 cm -> chest_blendshape 0..100.
   - Ví dụ waist 65..110 cm -> waist_blendshape 0..100.
3. Implement normalization utility in backend or Unity-side mapper.
4. Add API response payload for mapped avatar parameters.
5. Implement Unity applier:
   - apply blendshape weights
   - apply skeleton scale for height
6. Validate visual consistency with at least 5 body profiles.

## Acceptance criteria

- Cùng một set quần áo, thay user measurements sẽ thấy form thay đổi rõ.
- Height difference hiển thị đúng theo tỷ lệ mong muốn.
- Không bị méo mesh nghiêm trọng ở các pose cơ bản.
- FPS trong VR vẫn đạt ngưỡng chấp nhận được cho demo.

## Risks and mitigations

- Risk: Blendshape không đủ để biểu diễn body extremes.
  - Mitigation: thêm base body archetypes.
- Risk: Garment clipping khi body thay đổi mạnh.
  - Mitigation: ưu tiên body-safe ranges + test matrix sớm.
- Risk: mapping quá tuyến tính dẫn đến visual sai.
  - Mitigation: dùng piecewise mapping theo từng vùng số đo.

## Deliverables checklist

- [ ] Mapping spec doc (measurements -> avatar params)
- [ ] Unity implementation notes
- [ ] Test matrix (user profiles x outfits)
- [ ] Demo capture before/after deformation
