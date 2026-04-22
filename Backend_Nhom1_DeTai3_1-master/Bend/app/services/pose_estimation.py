from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from enum import Enum
from io import BytesIO
from pathlib import Path
from time import perf_counter
from typing import Callable

import cv2
import mediapipe as mp
import numpy as np
from PIL import Image
from dotenv import load_dotenv

try:
    from mediapipe.tasks.python import vision as mp_tasks_vision
    from mediapipe.tasks.python.core.base_options import BaseOptions as MpBaseOptions
    from mediapipe.tasks.python.vision.core.image import Image as MpImage
    from mediapipe.tasks.python.vision.core.image import ImageFormat as MpImageFormat
    from mediapipe.tasks.python.vision.core.vision_task_running_mode import VisionTaskRunningMode
except Exception:
    mp_tasks_vision = None
    MpBaseOptions = None
    MpImage = None
    MpImageFormat = None
    VisionTaskRunningMode = None


class MediaPipeBackend(str, Enum):
    CLASSIC = "classic"
    TASKS = "tasks"


@dataclass(slots=True)
class PoseKeypoint:
    """Serializable representation of a single MediaPipe pose landmark."""

    index: int
    name: str
    x: float
    y: float
    z: float
    pixel_x: int
    pixel_y: int
    visibility: float | None = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class PoseFrameResult:
    """Pose output for one processed frame."""

    frame_index: int
    timestamp_ms: float
    image_width: int
    image_height: int
    keypoints: list[PoseKeypoint]

    def to_dict(self) -> dict:
        return {
            "frame_index": self.frame_index,
            "timestamp_ms": self.timestamp_ms,
            "image_width": self.image_width,
            "image_height": self.image_height,
            "keypoints": [asdict(point) for point in self.keypoints],
        }


@dataclass(slots=True)
class BodyMeasurementEstimate:
    height_cm: float
    chest_cm: float
    waist_cm: float
    hip_cm: float
    inseam_cm: float
    shoulder_cm: float
    arm_length_cm: float

    def to_dict(self) -> dict:
        return asdict(self)


PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PROJECT_ROOT / ".env")


def _resolve_model_path(model_path: str | Path | None) -> Path:
    configured_path = model_path or os.getenv("POSE_LANDMARKER_MODEL_PATH") or "pose_landmarker_full.task"
    path = Path(configured_path).expanduser()
    if not path.is_absolute():
        path = (PROJECT_ROOT / path).resolve()
    return path


class PoseEstimator:
    """Reusable pose estimation service optimized for real-time webcam usage."""

    def __init__(
        self,
        static_image_mode: bool = False,
        model_complexity: int = 0,
        smooth_landmarks: bool = True,
        enable_segmentation: bool = False,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
        draw_landmarks: bool = True,
        model_path: str | Path | None = None,
    ) -> None:
        self._draw_landmarks = draw_landmarks
        self._start_time = perf_counter()
        self._model_path = _resolve_model_path(model_path)

        if hasattr(mp, "solutions"):
            self._backend = MediaPipeBackend.CLASSIC
            self._mp_pose = mp.solutions.pose
            self._mp_drawing = mp.solutions.drawing_utils
            self._mp_drawing_styles = mp.solutions.drawing_styles

            # model_complexity=0 is the lightest mode and usually the best
            # choice for weak GPUs or CPU-only execution.
            self._pose = self._mp_pose.Pose(
                static_image_mode=static_image_mode,
                model_complexity=model_complexity,
                smooth_landmarks=smooth_landmarks,
                enable_segmentation=enable_segmentation,
                min_detection_confidence=min_detection_confidence,
                min_tracking_confidence=min_tracking_confidence,
            )
            self._landmarker = None
            self._pose_connections = self._mp_pose.POSE_CONNECTIONS
            self._pose_landmark_enum = self._mp_pose.PoseLandmark
            return

        if mp_tasks_vision is None or MpBaseOptions is None or MpImage is None or MpImageFormat is None:
            raise RuntimeError(
                "Installed MediaPipe package does not expose either the classic "
                "`solutions` API or the Tasks API needed by this module."
            )

        if not self._model_path.exists():
            raise FileNotFoundError(f"Pose landmarker model not found: {self._model_path}")

        self._backend = MediaPipeBackend.TASKS
        self._mp_pose = None
        self._mp_drawing = None
        self._mp_drawing_styles = None
        self._pose = None
        self._pose_connections = mp_tasks_vision.PoseLandmarksConnections.POSE_LANDMARKS
        self._pose_landmark_enum = mp_tasks_vision.PoseLandmark

        options = mp_tasks_vision.PoseLandmarkerOptions(
            base_options=MpBaseOptions(model_asset_path=str(self._model_path)),
            running_mode=VisionTaskRunningMode.VIDEO,
            num_poses=1,
            min_pose_detection_confidence=min_detection_confidence,
            min_pose_presence_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
            output_segmentation_masks=False,
        )
        self._landmarker = mp_tasks_vision.PoseLandmarker.create_from_options(options)

    @property
    def backend_name(self) -> str:
        return self._backend.value

    def close(self) -> None:
        if self._pose is not None:
            self._pose.close()
        if self._landmarker is not None:
            self._landmarker.close()

    def __enter__(self) -> "PoseEstimator":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def process_frame(self, frame_bgr, frame_index: int) -> tuple[object, PoseFrameResult]:
        """Process one BGR frame and return an annotated frame plus keypoints."""

        image_height, image_width = frame_bgr.shape[:2]
        annotated_frame = frame_bgr.copy()
        timestamp_ms = int((perf_counter() - self._start_time) * 1000.0)

        if self._backend == MediaPipeBackend.CLASSIC:
            rgb_frame = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            rgb_frame.flags.writeable = False
            results = self._pose.process(rgb_frame)
            rgb_frame.flags.writeable = True

            keypoints = self._extract_classic_keypoints(results, image_width, image_height)
            if self._draw_landmarks and results.pose_landmarks:
                self._mp_drawing.draw_landmarks(
                    annotated_frame,
                    results.pose_landmarks,
                    self._pose_connections,
                    landmark_drawing_spec=self._mp_drawing_styles.get_default_pose_landmarks_style(),
                )
        else:
            rgb_frame = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            mp_image = MpImage(image_format=MpImageFormat.SRGB, data=rgb_frame)
            results = self._landmarker.detect_for_video(mp_image, timestamp_ms)

            keypoints = self._extract_tasks_keypoints(results, image_width, image_height)
            if self._draw_landmarks and results.pose_landmarks:
                self._draw_tasks_landmarks(annotated_frame, results.pose_landmarks[0])

        frame_result = PoseFrameResult(
            frame_index=frame_index,
            timestamp_ms=float(timestamp_ms),
            image_width=image_width,
            image_height=image_height,
            keypoints=keypoints,
        )
        return annotated_frame, frame_result

    def process_image(self, frame_bgr) -> PoseFrameResult:
        _, frame_result = self.process_frame(frame_bgr, frame_index=0)
        return frame_result

    def _extract_classic_keypoints(self, results, image_width: int, image_height: int) -> list[PoseKeypoint]:
        if not results.pose_landmarks:
            return []

        keypoints: list[PoseKeypoint] = []
        for index, landmark in enumerate(results.pose_landmarks.landmark):
            landmark_name = self._pose_landmark_enum(index).name.lower()
            keypoints.append(
                PoseKeypoint(
                    index=index,
                    name=landmark_name,
                    x=float(landmark.x),
                    y=float(landmark.y),
                    z=float(landmark.z),
                    pixel_x=int(landmark.x * image_width),
                    pixel_y=int(landmark.y * image_height),
                    visibility=float(landmark.visibility) if hasattr(landmark, "visibility") else None,
                )
            )
        return keypoints

    def _extract_tasks_keypoints(self, results, image_width: int, image_height: int) -> list[PoseKeypoint]:
        if not results.pose_landmarks:
            return []

        keypoints: list[PoseKeypoint] = []
        for index, landmark in enumerate(results.pose_landmarks[0]):
            landmark_name = self._pose_landmark_enum(index).name.lower()
            keypoints.append(
                PoseKeypoint(
                    index=index,
                    name=landmark_name,
                    x=float(landmark.x),
                    y=float(landmark.y),
                    z=float(landmark.z),
                    pixel_x=int(landmark.x * image_width),
                    pixel_y=int(landmark.y * image_height),
                    visibility=float(landmark.visibility) if hasattr(landmark, "visibility") else None,
                )
            )
        return keypoints

    def _draw_tasks_landmarks(self, frame_bgr, landmarks) -> None:
        image_height, image_width = frame_bgr.shape[:2]

        for connection in self._pose_connections:
            start_landmark = landmarks[connection.start]
            end_landmark = landmarks[connection.end]
            start_point = (int(start_landmark.x * image_width), int(start_landmark.y * image_height))
            end_point = (int(end_landmark.x * image_width), int(end_landmark.y * image_height))
            cv2.line(frame_bgr, start_point, end_point, (124, 198, 255), 2, cv2.LINE_AA)

        for landmark in landmarks:
            center = (int(landmark.x * image_width), int(landmark.y * image_height))
            cv2.circle(frame_bgr, center, 4, (0, 255, 140), -1, cv2.LINE_AA)


def load_image_bytes_to_bgr(file_bytes: bytes):
    image = Image.open(BytesIO(file_bytes)).convert("RGB")
    rgb_array = np.array(image)
    return cv2.cvtColor(rgb_array, cv2.COLOR_RGB2BGR)


def _keypoint_map(keypoints: list[PoseKeypoint]) -> dict[str, PoseKeypoint]:
    return {point.name: point for point in keypoints}


def _distance(point_a: PoseKeypoint, point_b: PoseKeypoint, image_width: int, image_height: int) -> float:
    dx = (point_a.x - point_b.x) * image_width
    dy = (point_a.y - point_b.y) * image_height
    return float((dx * dx + dy * dy) ** 0.5)


def estimate_body_measurements_from_keypoints(
    keypoints: list[PoseKeypoint],
    image_width: int,
    image_height: int,
    reference_height_cm: float,
) -> BodyMeasurementEstimate:
    if not keypoints:
        raise ValueError("No pose landmarks detected")

    named = _keypoint_map(keypoints)
    required = [
        "left_shoulder",
        "right_shoulder",
        "left_hip",
        "right_hip",
        "left_ankle",
        "right_ankle",
    ]
    missing = [name for name in required if name not in named]
    if missing:
        raise ValueError(f"Missing required landmarks: {', '.join(missing)}")

    visible_points = [point for point in keypoints if point.visibility is None or point.visibility >= 0.35]
    if not visible_points:
        visible_points = keypoints

    min_y = min(point.y for point in visible_points)
    max_y = max(point.y for point in visible_points)
    body_height_px = max((max_y - min_y) * image_height, image_height * 0.35)
    cm_per_px = reference_height_cm / body_height_px

    shoulder_width_cm = _distance(named["left_shoulder"], named["right_shoulder"], image_width, image_height) * cm_per_px
    hip_width_cm = _distance(named["left_hip"], named["right_hip"], image_width, image_height) * cm_per_px

    left_torso = _distance(named["left_shoulder"], named["left_hip"], image_width, image_height) * cm_per_px
    right_torso = _distance(named["right_shoulder"], named["right_hip"], image_width, image_height) * cm_per_px
    torso_height_cm = (left_torso + right_torso) / 2.0

    left_inseam = _distance(named["left_hip"], named["left_ankle"], image_width, image_height) * cm_per_px
    right_inseam = _distance(named["right_hip"], named["right_ankle"], image_width, image_height) * cm_per_px
    inseam_cm = (left_inseam + right_inseam) / 2.0

    arm_length_cm = 0.0
    if {"left_shoulder", "left_elbow", "left_wrist"}.issubset(named):
        arm_length_cm = (
            _distance(named["left_shoulder"], named["left_elbow"], image_width, image_height)
            + _distance(named["left_elbow"], named["left_wrist"], image_width, image_height)
        ) * cm_per_px
    elif {"right_shoulder", "right_elbow", "right_wrist"}.issubset(named):
        arm_length_cm = (
            _distance(named["right_shoulder"], named["right_elbow"], image_width, image_height)
            + _distance(named["right_elbow"], named["right_wrist"], image_width, image_height)
        ) * cm_per_px
    else:
        arm_length_cm = reference_height_cm * 0.36

    chest_cm = max(65.0, min(150.0, shoulder_width_cm * 2.18))
    waist_width_cm = shoulder_width_cm * 0.72 + torso_height_cm * 0.12
    waist_cm = max(55.0, min(150.0, waist_width_cm * 1.95))
    hip_cm = max(70.0, min(170.0, hip_width_cm * 2.12))
    inseam_cm = max(40.0, min(reference_height_cm * 0.55, inseam_cm))
    shoulder_cm = max(28.0, min(65.0, shoulder_width_cm))
    arm_length_cm = max(35.0, min(90.0, arm_length_cm))

    return BodyMeasurementEstimate(
        height_cm=round(reference_height_cm, 2),
        chest_cm=round(chest_cm, 2),
        waist_cm=round(waist_cm, 2),
        hip_cm=round(hip_cm, 2),
        inseam_cm=round(inseam_cm, 2),
        shoulder_cm=round(shoulder_cm, 2),
        arm_length_cm=round(arm_length_cm, 2),
    )


def estimate_pose_from_image_bytes(
    file_bytes: bytes,
    reference_height_cm: float,
    model_path: str | Path | None = None,
) -> tuple[PoseFrameResult, BodyMeasurementEstimate]:
    frame_bgr = load_image_bytes_to_bgr(file_bytes)
    with PoseEstimator(model_complexity=0, enable_segmentation=False, draw_landmarks=False, model_path=model_path) as estimator:
        frame_result = estimator.process_image(frame_bgr)

    measurements = estimate_body_measurements_from_keypoints(
        frame_result.keypoints,
        frame_result.image_width,
        frame_result.image_height,
        reference_height_cm=reference_height_cm,
    )
    return frame_result, measurements


def run_webcam_pose_loop(
    camera_index: int = 0,
    frame_width: int = 640,
    frame_height: int = 480,
    window_name: str = "MediaPipe Pose Estimation",
    mirror_view: bool = True,
    show_fps: bool = True,
    on_frame: Callable[[PoseFrameResult], None] | None = None,
    model_path: str | Path | None = None,
) -> list[dict]:
    """
    Run realtime webcam pose estimation and return all collected frame keypoints.

    The optional callback makes this function easy to connect to a socket sender,
    Unity bridge, or a FastAPI websocket broadcaster later.
    """

    capture = cv2.VideoCapture(camera_index)
    capture.set(cv2.CAP_PROP_FRAME_WIDTH, frame_width)
    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_height)
    capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    if not capture.isOpened():
        raise RuntimeError(f"Could not open webcam with index {camera_index}")

    history: list[dict] = []
    frame_index = 0
    previous_tick = perf_counter()

    with PoseEstimator(model_complexity=0, enable_segmentation=False, model_path=model_path) as estimator:
        print(f"Using MediaPipe backend: {estimator.backend_name}")
        if estimator.backend_name == MediaPipeBackend.TASKS.value:
            print(f"Using landmarker model: {Path(model_path).expanduser()}")

        try:
            while True:
                ok, frame = capture.read()
                if not ok:
                    raise RuntimeError("Failed to read frame from webcam")

                if mirror_view:
                    frame = cv2.flip(frame, 1)

                annotated_frame, frame_result = estimator.process_frame(frame, frame_index=frame_index)
                frame_dict = frame_result.to_dict()
                history.append(frame_dict)

                if on_frame is not None:
                    on_frame(frame_result)

                if show_fps:
                    now = perf_counter()
                    fps = 1.0 / max(now - previous_tick, 1e-6)
                    previous_tick = now
                    cv2.putText(
                        annotated_frame,
                        f"FPS: {fps:.1f}",
                        (16, 28),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 255, 0),
                        2,
                        cv2.LINE_AA,
                    )
                    cv2.putText(
                        annotated_frame,
                        f"Keypoints: {len(frame_result.keypoints)}",
                        (16, 56),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 255, 255),
                        2,
                        cv2.LINE_AA,
                    )

                cv2.imshow(window_name, annotated_frame)

                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

                frame_index += 1
        finally:
            capture.release()
            cv2.destroyAllWindows()

    return history
