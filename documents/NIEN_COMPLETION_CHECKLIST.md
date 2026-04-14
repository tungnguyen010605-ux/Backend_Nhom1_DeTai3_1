# Checklist Hoan Thanh Cong Viec Nguyen Duy Nien

Ngay cap nhat: 2026-04-14
Nguon doi chieu: toan bo thu muc `backend_nhom1_detai3_1/` va runtime check trong moi truong hien tai.

## Tong ket
- Trang thai chung: Da co backend, frontend web, project Unity VR va luong mock fitting end-to-end.
- Phan da co bang chung implementation:
  - MediaPipe pose estimation va endpoint `/pose/estimate`.
  - Frontend web cho camera, upload anh, tao user, tao clothing, goi fitting task.
  - Unity client goi backend, poll task status va ap texture len avatar.
  - Backend task sinh texture mock, luu ket qua vao SQLite.
- Phan chua co bang chung day du:
  - Chua thay artifact test thiet bi Oculus/Meta XR thuc te.
  - Chua thay GAN/Diffusion inference that; hien tai la mock texture CPU-safe.

## Danh sach doi chieu
1. Lay keypoints tu camera bang MediaPipe
- Trang thai: DONE
- Bang chung:
  - `Bend/app/services/pose_estimation.py`
  - `Bend/app/main_api.py` endpoint `POST /pose/estimate`
  - `Bend/run_pose_webcam.py`
  - `Fend/index.html`
  - `Fend/app.js`

2. Dong bo du lieu pose voi avatar trong Unity
- Trang thai: PARTIAL DONE
- Bang chung:
  - Co project Unity trong `VRClient/`
  - Co script `VRClient/Assets/Scripts/VRBackendClient.cs`
  - Script da:
    - kiem tra `GET /health`
    - lay user va clothing tu backend
    - goi `POST /tasks/generate-texture`
    - poll `GET /status/{task_id}`
    - tai texture tra ve va gan vao `avatarRenderer.material.mainTexture`
- Gioi han hien tai:
  - Chua thay code map MediaPipe keypoints vao human rig/IK avatar theo xuong khop.
  - Luong hien tai dang la fitting texture mock, chua phai body tracking real-time.

3. Test VR voi Oculus SDK
- Trang thai: PARTIAL / CHUA DU BANG CHUNG
- Bang chung tim thay:
  - Co Unity project, package XR va sample XR Interaction Toolkit trong `VRClient/Assets/Samples/XR Interaction Toolkit/`
  - Co cau hinh XR trong `VRClient/ProjectSettings/`
- Thieu:
  - Chua thay tai lieu test tren thiet bi Oculus/Meta.
  - Chua thay log test, build artifact, hay checklist UAT cho headset.

4. Chay inference GAN/Diffusion o muc nhe
- Trang thai: NOT DONE
- Bang chung:
  - `Bend/app/services/tasks.py` hien dang tao `mock texture` bang PIL.
  - Chua thay model GAN/Diffusion, code torch, weights hoac benchmark inference.

## Kiem tra runtime
1. Kha nang khoi dong backend
- Ket qua: PASS sau khi sua import lazy cho pose estimation.
- Ghi chu:
  - Backend hien co the khoi dong du cac route co ban ngay ca khi may chua cai `opencv-python` va `mediapipe`.
  - Neu thieu cac goi nay, endpoint `/pose/estimate` se tra `503` kem huong dan cai dependency.

2. Smoke test tu dong
- Trang thai hien tai: CHUA CHAY TRON trong moi truong nay.
- Ly do:
  - May dang thieu `httpx`, trong khi `Bend/smoke_test.py` dung `fastapi.testclient`.
  - Day la van de moi truong, khong phai loi logic trong repo, vi `httpx` da co trong `Bend/requirements.txt`.

3. Pose runtime
- Trang thai hien tai: CHUA VERIFY tren may nay.
- Ly do:
  - Moi truong hien tai chua cai `cv2` va `mediapipe`.

## Viec da chinh sua trong dot nay
1. Sua backend de de khoi dong hon
- File: `Bend/app/main_api.py`
- Noi dung:
  - Bo import cung `pose_estimation` o luc app khoi tao.
  - Doi sang kiem tra dependency khi goi `/pose/estimate`.
  - Giup app van boot duoc de chay UI, user, clothing, preprocess, task va Unity mock workflow.

2. Cap nhat lai checklist cho dung repo hien tai
- File: `documents/NIEN_COMPLETION_CHECKLIST.md`
- Noi dung:
  - Sua nhan dinh sai truoc do ve Unity project va XR assets.
  - Tach ro phan nao da xong, phan nao moi chi o muc mock, phan nao con thieu bang chung.

## Cach chay de dung voi repo hien tai
1. Local Python
- Cai dependency:
  - `python -m pip install -r Bend/requirements.txt`
- Chay backend:
  - `python main.py`
- Mo:
  - `http://127.0.0.1:8000/ui`
  - `http://127.0.0.1:8000/docs`

2. Docker
- Trong thu muc `backend_nhom1_detai3_1/`:
  - `docker compose up --build`

## Viec can lam neu muon "dong task" hoan toan
1. Them true avatar rig sync
- Nhan keypoints/body measurements tu backend va map vao avatar Unity bang IK/retargeting.

2. Them test Oculus/Meta co bang chung
- Ghi ro version SDK, scene test, ket qua test tren thiet bi that.

3. Thay mock texture bang model that
- Them it nhat mot pipeline GAN/Diffusion nhe, co endpoint, benchmark thoi gian va tai nguyen.

4. Chay lai smoke test sau khi cai du dependency
- Muc tieu:
  - `python -m pip install -r Bend/requirements.txt`
  - `python Bend/smoke_test.py`
