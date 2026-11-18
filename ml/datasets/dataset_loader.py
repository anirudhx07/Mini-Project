"""Dataset loader for COD10K, CAMO, and custom drone terrain images."""

import os
import glob
from typing import Tuple, List, Optional
import cv2
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader


class CamouflageDataset(Dataset):
    """Loads paired aerial/camouflage images and binary ground-truth segmentation masks."""

    def __init__(self, image_dir: str, mask_dir: Optional[str] = None, target_size: Tuple[int, int] = (224, 224), transform=None):
        self.image_dir = image_dir
        self.mask_dir = mask_dir
        self.target_size = target_size
        self.transform = transform

        self.image_paths = sorted(glob.glob(os.path.join(image_dir, "*.*")))
        # Supported image extensions
        self.image_paths = [p for p in self.image_paths if p.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))]

    def __len__(self) -> int:
        return len(self.image_paths)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        img_path = self.image_paths[idx]
        image = cv2.imread(img_path)
        if image is None:
            # Fallback zero image if read fails
            image = np.zeros((self.target_size[1], self.target_size[0], 3), dtype=np.uint8)
        else:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            image = cv2.resize(image, self.target_size)

        # Normalize to [0.0, 1.0] and shape (C, H, W)
        image_tensor = torch.from_numpy(image).permute(2, 0, 1).float() / 255.0

        if self.mask_dir and os.path.exists(self.mask_dir):
            base_name = os.path.splitext(os.path.basename(img_path))[0]
            # Try matching mask with same base name
            mask_candidates = glob.glob(os.path.join(self.mask_dir, f"{base_name}.*"))
            if mask_candidates:
                mask = cv2.imread(mask_candidates[0], cv2.IMREAD_GRAYSCALE)
                mask = cv2.resize(mask, self.target_size)
                mask = (mask > 127).astype(np.float32)
            else:
                mask = np.zeros(self.target_size, dtype=np.float32)
        else:
            mask = np.zeros(self.target_size, dtype=np.float32)

        mask_tensor = torch.from_numpy(mask).unsqueeze(0).float()
        return image_tensor, mask_tensor


def create_dataloaders(dataset_dir: str, batch_size: int = 8, split_ratio: Tuple[float, float, float] = (0.70, 0.15, 0.15)):
    """Utility to partition dataset into train/validation/test sets."""
    images_dir = os.path.join(dataset_dir, "images")
    masks_dir = os.path.join(dataset_dir, "masks")
    
    full_dataset = CamouflageDataset(images_dir, masks_dir)
    total_samples = len(full_dataset)
    if total_samples == 0:
        return None, None, None

    train_n = int(total_samples * split_ratio[0])
    val_n = int(total_samples * split_ratio[1])
    test_n = total_samples - train_n - val_n

    train_set, val_set, test_set = torch.utils.data.random_split(
        full_dataset, [train_n, val_n, test_n], generator=torch.Generator().manual_seed(42)
    )

    train_loader = DataLoader(train_set, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_set, batch_size=batch_size, shuffle=False)
    test_loader = DataLoader(test_set, batch_size=batch_size, shuffle=False)

    return train_loader, val_loader, test_loader
