from __future__ import annotations

import json
import os
from pathlib import Path

from PIL import Image
import torch  # type: ignore[import-not-found]
from torch.utils.data import Dataset  # type: ignore[import-not-found]
import torchvision.transforms as transforms  # type: ignore[import-not-found]


class VTONDataset(Dataset):
    """
    Dataset chuẩn hóa cho mô hình Try-On (VITON/CP-VTON/Stable Diffusion).
    Định dạng folder:
    - data_root/
        - images/ (ảnh người)
        - clothes/ (ảnh quần áo)
        - pose/ (file json toạ độ khung xương - Tuỳ chọn)
        - pairs.txt (Mapping: 'image_filename clothing_filename')
    """
    def __init__(self, data_root: str | os.PathLike[str], mode: str = 'train', image_size: tuple[int, int] = (256, 192)):
        self.data_root = Path(data_root)
        self.mode = mode
        self.image_height, self.image_width = image_size
        
        self.image_dir = self.data_root / 'images'
        self.cloth_dir = self.data_root / 'clothes'
        self.pose_dir = self.data_root / 'pose'
        
        pairs_file = self.data_root / 'pairs.txt'
        self.pairs = []
        
        if pairs_file.exists():
            with open(pairs_file, 'r', encoding='utf-8') as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        self.pairs.append((parts[0], parts[1]))
            print(f"✅ Đã tải Dataset ({mode}): {len(self.pairs)} cặp áo-người.")
        else:
            print(f"⚠️ CẢNH BÁO: Không tìm thấy tệp {pairs_file}. Dataloader sẽ rỗng!")
            
        # Tiêu chuẩn Transform dành cho kiến trúc GAN
        self.transform = transforms.Compose([
            transforms.Resize((self.image_height, self.image_width)),
            transforms.ToTensor(),
            transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))
        ])

    def __len__(self):
        return len(self.pairs)

    def __getitem__(self, idx):
        im_name, c_name = self.pairs[idx]
        
        # 1. Đọc Ảnh
        im_path = self.image_dir / im_name
        c_path = self.cloth_dir / c_name
        
        try:
            image = Image.open(im_path).convert('RGB')
            cloth = Image.open(c_path).convert('RGB')
        except FileNotFoundError as e:
            # Fallback tránh việc Crash vòng lặp Train khi 1 ảnh lỗi
            print(f"❌ Lỗi file: {e}")
            return {
                'image': torch.zeros((3, self.image_height, self.image_width)),
                'cloth': torch.zeros((3, self.image_height, self.image_width)),
                'pose_data': [],
                'im_name': im_name,
                'c_name': c_name
            }

        image_tensor = self.transform(image)
        cloth_tensor = self.transform(cloth)

        # 2. Đọc Pose JSON (Tuỳ chọn nạp vào model)
        pose_data = self._load_pose_data(im_name)
                
        return {
            'image': image_tensor,
            'cloth': cloth_tensor,
            'pose_data': pose_data,
            'im_name': im_name,
            'c_name': c_name
        }

    def _load_pose_data(self, image_name: str) -> list | dict:
        pose_path = self.pose_dir / f"{Path(image_name).stem}.json"
        if not pose_path.exists():
            return []

        try:
            with open(pose_path, 'r', encoding='utf-8') as file:
                pose_dict = json.load(file)
        except json.JSONDecodeError:
            return []

        if isinstance(pose_dict, dict) and 'people' in pose_dict:
            people = pose_dict.get('people') or []
            if people:
                return people[0].get('pose_keypoints_2d', [])
        return pose_dict
