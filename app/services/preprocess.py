from __future__ import annotations

import random
from io import BytesIO
from pathlib import Path
from uuid import uuid4

from PIL import Image, ImageEnhance, ImageOps

MAX_EDGE = 1024


def preprocess_image_bytes(file_bytes: bytes, output_dir: Path, width: int = 512, height: int = 512, normalize: bool = True, augment: bool = False) -> tuple[Path, dict]:
    width = max(64, min(width, MAX_EDGE))
    height = max(64, min(height, MAX_EDGE))

    image = Image.open(BytesIO(file_bytes)).convert("RGB")
    image = image.resize((width, height), Image.Resampling.BILINEAR)

    if augment:
        if random.random() < 0.5:
            image = ImageOps.mirror(image)
        brightness = random.uniform(0.92, 1.08)
        image = ImageEnhance.Brightness(image).enhance(brightness)

    if normalize:
        # Keep this lightweight: normalize to 0-255 range after optional augment.
        image = ImageOps.autocontrast(image)

    output_dir.mkdir(parents=True, exist_ok=True)
    out_name = f"preprocessed_{uuid4().hex}.png"
    out_path = output_dir / out_name
    image.save(out_path, format="PNG", optimize=True)

    metadata = {
        "width": width,
        "height": height,
        "normalized": normalize,
        "augmented": augment,
    }
    return out_path, metadata

