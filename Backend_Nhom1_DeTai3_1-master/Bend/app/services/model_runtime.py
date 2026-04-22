from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import TYPE_CHECKING, Callable

from PIL import Image

try:
    import torch
except Exception:  # pragma: no cover - optional runtime dependency
    torch = None

try:
    import torchvision.transforms as transforms
except Exception:  # pragma: no cover - optional runtime dependency
    transforms = None

try:
    from Bend.ml_pipeline.models.gan_architecture import DummyVTONGenerator
except Exception:  # pragma: no cover - optional import path during packaging
    DummyVTONGenerator = None

try:
    from Bend.ml_pipeline.models.cpvton_tom import CPVTONTOMGenerator
except Exception:  # pragma: no cover - optional import path during packaging
    CPVTONTOMGenerator = None

if TYPE_CHECKING:
    from torch import Tensor
else:
    Tensor = object


@dataclass(slots=True)
class VTONRuntimeConfig:
    input_height: int = 256
    input_width: int = 192
    checkpoint_path: Path | None = None
    device: str | None = None
    use_half_precision: bool = False
    model_type: str = "cpvton_tom"
    input_channels: int = 25
    output_channels: int = 4


InputResolver = Callable[[int, int], tuple[Path | None, Path | None]]


class VTONModelRuntime:
    def __init__(self, config: VTONRuntimeConfig | None = None) -> None:
        self.config = config or VTONRuntimeConfig()
        self._model = None
        self._loaded = False
        self._device = self._resolve_device()
        self._input_resolver: InputResolver | None = None
        self._preprocess = self._build_preprocess()

    def _resolve_device(self) -> str:
        if self.config.device:
            return self.config.device
        if torch is not None and torch.cuda.is_available():
            return "cuda"
        return "cpu"

    @property
    def is_ready(self) -> bool:
        return self._loaded

    def set_input_resolver(self, resolver: InputResolver) -> None:
        self._input_resolver = resolver

    def _build_preprocess(self):
        if transforms is None:
            return None
        return transforms.Compose(
            [
                transforms.Resize((self.config.input_height, self.config.input_width)),
                transforms.ToTensor(),
                transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)),
            ]
        )

    def load(self) -> "VTONModelRuntime":
        if self._loaded:
            return self

        if torch is None:
            self._loaded = True
            return self

        model = self._build_model()
        if model is None:
            self._loaded = True
            return self

        model.eval()

        if self.config.checkpoint_path and self.config.checkpoint_path.exists():
            state_dict = self._load_checkpoint_state_dict(self.config.checkpoint_path)
            model.load_state_dict(state_dict, strict=False)

        if self._device == "cuda":
            model = model.to(self._device)
            if self.config.use_half_precision:
                model = model.half()
        else:
            model = model.to("cpu")

        self._model = model
        self._loaded = True
        return self

    def _build_model(self):
        if self.config.model_type == "cpvton_tom":
            if CPVTONTOMGenerator is None:
                return None
            return CPVTONTOMGenerator(
                input_nc=self.config.input_channels,
                output_nc=self.config.output_channels,
            )

        if DummyVTONGenerator is None:
            return None
        return DummyVTONGenerator(input_nc=6, output_nc=3)

    @staticmethod
    def _load_checkpoint_state_dict(checkpoint_path: Path) -> dict:
        assert torch is not None
        checkpoint = torch.load(checkpoint_path, map_location="cpu")
        if isinstance(checkpoint, dict):
            if "state_dict" in checkpoint and isinstance(checkpoint["state_dict"], dict):
                checkpoint = checkpoint["state_dict"]
            elif "model" in checkpoint and isinstance(checkpoint["model"], dict):
                checkpoint = checkpoint["model"]
            elif "generator" in checkpoint and isinstance(checkpoint["generator"], dict):
                checkpoint = checkpoint["generator"]

        if not isinstance(checkpoint, dict):
            raise ValueError("Checkpoint format is not a valid state_dict")

        normalized: dict[str, Tensor] = {}
        for key, value in checkpoint.items():
            clean_key = key[7:] if key.startswith("module.") else key
            normalized[clean_key] = value
        return normalized

    def infer_texture(self, user_id: int, clothing_item_id: int, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if not self._loaded:
            self.load()

        if torch is None or self._model is None:
            self._write_fallback_texture(output_path, user_id, clothing_item_id)
            return output_path

        person_image_path = None
        cloth_image_path = None
        if self._input_resolver is not None:
            person_image_path, cloth_image_path = self._input_resolver(user_id, clothing_item_id)

        if person_image_path is None or cloth_image_path is None:
            self._write_fallback_texture(output_path, user_id, clothing_item_id)
            return output_path

        try:
            texture = self._run_torch_inference_from_images(person_image_path, cloth_image_path)
        except Exception:
            self._write_fallback_texture(output_path, user_id, clothing_item_id)
            return output_path

        self._save_tensor_as_image(texture, output_path)
        return output_path

    def _run_torch_inference_from_images(self, person_image_path: Path, cloth_image_path: Path) -> "Tensor":
        assert torch is not None
        assert self._model is not None
        if self._preprocess is None:
            raise RuntimeError("torchvision is required for model preprocessing")

        person_image = Image.open(person_image_path).convert("RGB")
        cloth_image = Image.open(cloth_image_path).convert("RGB")

        person_tensor = self._preprocess(person_image).unsqueeze(0).to(self._device)
        cloth_tensor = self._preprocess(cloth_image).unsqueeze(0).to(self._device)

        if self._device == "cuda":
            dtype_tensor = person_tensor.half() if self.config.use_half_precision else person_tensor.float()
            person_tensor = dtype_tensor
            cloth_tensor = cloth_tensor.half() if self.config.use_half_precision else cloth_tensor.float()

        if self.config.model_type == "cpvton_tom":
            input_tensor = self._build_cpvton_input(person_tensor, cloth_tensor)
            with torch.no_grad():
                output = self._model(input_tensor).float()

            if output.shape[1] >= 4:
                rendered_person = output[:, :3, :, :].clamp(-1.0, 1.0)
                composite_mask = torch.sigmoid(output[:, 3:4, :, :])
                result = cloth_tensor.float() * composite_mask + rendered_person * (1.0 - composite_mask)
                return result.squeeze(0).clamp(-1.0, 1.0)

            return output[:, :3, :, :].squeeze(0).clamp(-1.0, 1.0)

        input_tensor = torch.cat((person_tensor, cloth_tensor), dim=1)
        with torch.no_grad():
            output = self._model(input_tensor)
            output = output.float().clamp(-1.0, 1.0)
        return output.squeeze(0)

    def _build_cpvton_input(self, person_tensor: "Tensor", cloth_tensor: "Tensor") -> "Tensor":
        assert torch is not None
        merged = torch.cat((person_tensor, cloth_tensor), dim=1)
        extra_channels = self.config.input_channels - merged.shape[1]
        if extra_channels <= 0:
            return merged[:, : self.config.input_channels, :, :]

        extra = torch.zeros(
            (merged.shape[0], extra_channels, merged.shape[2], merged.shape[3]),
            device=merged.device,
            dtype=merged.dtype,
        )
        return torch.cat((merged, extra), dim=1)

    def _save_tensor_as_image(self, tensor: "Tensor", output_path: Path) -> None:
        assert torch is not None
        array = (
            tensor.detach()
            .cpu()
            .mul(127.5)
            .add(127.5)
            .clamp(0, 255)
            .byte()
            .permute(1, 2, 0)
            .numpy()
        )
        Image.fromarray(array).save(output_path, format="PNG", optimize=True)

    def _write_fallback_texture(self, output_path: Path, user_id: int, clothing_item_id: int) -> None:
        color_seed = self._seed_from_ids(user_id, clothing_item_id)
        top = ((color_seed >> 0) & 0xFF, (color_seed >> 8) & 0xFF, (color_seed >> 16) & 0xFF)
        bottom = ((color_seed >> 24) & 0xFF, (color_seed >> 32) & 0xFF, (color_seed >> 40) & 0xFF)
        image = Image.new("RGB", (self.config.input_width, self.config.input_height), top)
        for y in range(self.config.input_height // 2, self.config.input_height):
            for x in range(self.config.input_width):
                image.putpixel((x, y), bottom)
        image.save(output_path, format="PNG", optimize=True)

    @staticmethod
    def _seed_from_ids(user_id: int, clothing_item_id: int) -> int:
        digest = sha256(f"{user_id}:{clothing_item_id}".encode("utf-8")).digest()
        return int.from_bytes(digest[:8], byteorder="big", signed=False)


_runtime: VTONModelRuntime | None = None


def get_vton_runtime(config: VTONRuntimeConfig | None = None) -> VTONModelRuntime:
    global _runtime
    if _runtime is None:
        _runtime = VTONModelRuntime(config=config)
    elif config is not None:
        _runtime.config = config
        _runtime._device = _runtime._resolve_device()
    return _runtime
