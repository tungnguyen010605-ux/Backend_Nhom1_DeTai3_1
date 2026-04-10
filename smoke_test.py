from io import BytesIO
from time import sleep

from fastapi.testclient import TestClient
from PIL import Image

from app.main_api import app


def _make_image_bytes() -> bytes:
    image = Image.new("RGB", (128, 128), color=(90, 140, 200))
    buf = BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


def run() -> None:
    with TestClient(app) as client:
        user_payload = {
            "name": "Test User",
            "height_cm": 172,
            "chest_cm": 94,
            "waist_cm": 78,
            "hip_cm": 96,
            "inseam_cm": 79,
        }
        user = client.post("/users", json=user_payload)
        assert user.status_code == 200, user.text
        user_id = user.json()["id"]

        users = client.get("/users")
        assert users.status_code == 200, users.text
        users_data = users.json()
        assert any(u["id"] == user_id for u in users_data), "Created user not found in /users"

        cloth_payload = {
            "user_id": user_id,
            "category": "shirt",
            "size_label": "M",
            "color": "blue",
        }
        cloth = client.post("/clothing-items", json=cloth_payload)
        assert cloth.status_code == 200, cloth.text
        cloth_id = cloth.json()["id"]

        vr = client.get(f"/mock/vr/body/{user_id}")
        assert vr.status_code == 200, vr.text

        image_bytes = _make_image_bytes()
        preprocess = client.post(
            "/preprocess?width=256&height=256&normalize=true&augment=false",
            files={"file": ("in.png", image_bytes, "image/png")},
        )
        assert preprocess.status_code == 200, preprocess.text

        task = client.post(
            "/tasks/generate-texture",
            json={"user_id": user_id, "clothing_item_id": cloth_id},
        )
        assert task.status_code == 200, task.text
        task_id = task.json()["task_id"]

        completed = False
        for _ in range(15):
            status = client.get(f"/status/{task_id}")
            assert status.status_code == 200, status.text
            data = status.json()
            if data["status"] == "completed":
                completed = True
                break
            sleep(0.2)

        assert completed, "Task did not complete in expected time"
        print("Smoke test passed")


if __name__ == "__main__":
    run()

