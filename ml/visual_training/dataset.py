from __future__ import annotations

import json
from pathlib import Path

import torch
from PIL import Image
from torch import Tensor
from torch.utils.data import Dataset
from torchvision import transforms


class FFPPFaceDataset(Dataset[tuple[Tensor, int]]):
    def __init__(
        self,
        manifest_path: str | Path,
        split: str,
        resolution: int = 256,
    ) -> None:
        self.manifest_path = Path(manifest_path)
        self.split = split

        if split not in {"train", "val", "test"}:
            raise ValueError(f"Invalid split: {split}")

        records = []

        for line in self.manifest_path.read_text(
            encoding="utf-8"
        ).splitlines():
            if not line.strip():
                continue

            record = json.loads(line)

            if record["split"] == split:
                records.append(record)

        if not records:
            raise ValueError(
                f"No samples found for split={split!r}"
            )

        self.records = records

        self.transform = transforms.Compose(
            [
                transforms.Resize(
                    (resolution, resolution)
                ),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.5, 0.5, 0.5],
                    std=[0.5, 0.5, 0.5],
                ),
            ]
        )

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(
        self,
        index: int,
    ) -> tuple[Tensor, int]:
        record = self.records[index]

        image_path = Path(record["frame_path"])

        if not image_path.exists():
            raise FileNotFoundError(
                f"Missing face crop: {image_path}"
            )

        image = Image.open(image_path).convert("RGB")
        tensor = self.transform(image)

        label = int(record["label"])

        return tensor, label
