from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.services.pose_estimation import run_webcam_pose_loop

DEFAULT_MODEL_PATH = Path("/home/nien/model/pose_landmarker_full.task")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Realtime pose estimation from webcam using OpenCV + MediaPipe."
    )
    parser.add_argument("--camera-index", type=int, default=0, help="Webcam index, usually 0.")
    parser.add_argument("--width", type=int, default=640, help="Requested capture width.")
    parser.add_argument("--height", type=int, default=480, help="Requested capture height.")
    parser.add_argument(
        "--model-path",
        type=Path,
        default=DEFAULT_MODEL_PATH,
        help="Path to pose_landmarker.task when using newer MediaPipe Tasks builds.",
    )
    parser.add_argument(
        "--save-json",
        type=Path,
        default=None,
        help="Optional path to save collected keypoints as JSON after exit.",
    )
    parser.add_argument(
        "--no-fps",
        action="store_true",
        help="Disable FPS overlay if you want the cleanest possible frame.",
    )
    parser.add_argument(
        "--no-mirror",
        action="store_true",
        help="Disable selfie-style mirrored preview.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    frame_history = run_webcam_pose_loop(
        camera_index=args.camera_index,
        frame_width=args.width,
        frame_height=args.height,
        mirror_view=not args.no_mirror,
        show_fps=not args.no_fps,
        model_path=args.model_path,
    )

    print(f"Collected {len(frame_history)} frames of pose keypoints.")
    if frame_history:
        latest = frame_history[-1]
        print(f"Last frame keypoints: {len(latest['keypoints'])}")

    if args.save_json:
        args.save_json.parent.mkdir(parents=True, exist_ok=True)
        args.save_json.write_text(json.dumps(frame_history, indent=2), encoding="utf-8")
        print(f"Saved keypoints to: {args.save_json}")


if __name__ == "__main__":
    main()
