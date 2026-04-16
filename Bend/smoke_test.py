from pathlib import Path
from time import sleep

from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main_api import app
from app.models import ClothingItem


BASE_DIR = Path(__file__).resolve().parent
TEST_PERSON_IMAGE = BASE_DIR / "static" / "person_images" / "serious-young-man-standing-against-white-background-photo.jpg"
TARGET_USER_ID = 22
TARGET_CLOTHING_ID = 31


def _read_image_bytes(image_path: Path) -> bytes:
    if not image_path.exists():
        raise FileNotFoundError(f"Missing test image: {image_path}")
    return image_path.read_bytes()


def run() -> None:
    with TestClient(app) as client:
        user_id = TARGET_USER_ID
        cloth_id = TARGET_CLOTHING_ID

        person_image_bytes = _read_image_bytes(TEST_PERSON_IMAGE)
        person_upload = client.post(
            f"/users/{user_id}/reference-image",
            files={
                "file": (
                    TEST_PERSON_IMAGE.name,
                    person_image_bytes,
                    "image/jpeg",
                )
            },
        )
        assert person_upload.status_code == 200, person_upload.text

        users = client.get("/users")
        assert users.status_code == 200, users.text
        users_data = users.json()
        assert any(u["id"] == user_id for u in users_data), f"Required user_id={user_id} not found in /users"

        clothing_items = client.get(f"/clothing-items?user_id={user_id}")
        assert clothing_items.status_code == 200, clothing_items.text
        clothes_data = clothing_items.json()
        assert any(c["id"] == cloth_id for c in clothes_data), f"Required clothing_id={cloth_id} not found for user_id={user_id}"

        vr = client.get(f"/mock/vr/body/{user_id}")
        assert vr.status_code == 200, vr.text

        preprocess = client.post(
            "/preprocess?width=256&height=256&normalize=true&augment=false",
            files={"file": (TEST_PERSON_IMAGE.name, person_image_bytes, "image/jpeg")},
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

        db = SessionLocal()
        try:
            updated_item = db.query(ClothingItem).filter(ClothingItem.id == cloth_id).first()
            assert updated_item is not None, "Clothing item missing in DB"
            assert data.get("output_url"), "Task output_url is missing"
            # Current backend keeps original clothing image_path if it is a clothing asset path.
            # Therefore smoke test only verifies generation completed and output URL exists.
            if updated_item.image_path and updated_item.image_path.startswith("/textures/"):
                assert updated_item.image_path == data.get("output_url"), "Texture path mismatch"
        finally:
            db.close()

        print("Smoke test passed")


if __name__ == "__main__":
    run()

