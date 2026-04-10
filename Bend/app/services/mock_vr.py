from app.schemas import BodyData


def build_mock_body_data(user_id: int, height_cm: float, chest_cm: float, waist_cm: float, hip_cm: float, inseam_cm: float) -> BodyData:
    shoulder_cm = round(chest_cm * 0.38, 2)
    arm_length_cm = round(height_cm * 0.36, 2)
    return BodyData(
        user_id=user_id,
        height_cm=height_cm,
        chest_cm=chest_cm,
        waist_cm=waist_cm,
        hip_cm=hip_cm,
        inseam_cm=inseam_cm,
        shoulder_cm=shoulder_cm,
        arm_length_cm=arm_length_cm,
    )

