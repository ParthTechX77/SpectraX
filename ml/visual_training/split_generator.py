from __future__ import annotations

import random
from collections import defaultdict
from dataclasses import dataclass


@dataclass(frozen=True)
class VideoGroup:
    source_video_id: str
    label: int


def split_video_groups(
    groups: list[VideoGroup],
    *,
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
    seed: int = 42,
) -> dict[str, list[str]]:
    total = train_ratio + val_ratio + test_ratio

    if abs(total - 1.0) > 1e-9:
        raise ValueError("Split ratios must sum to 1.0")

    if not groups:
        raise ValueError("No video groups supplied")

    grouped: dict[int, list[str]] = defaultdict(list)

    for group in groups:
        grouped[group.label].append(group.source_video_id)

    rng = random.Random(seed)

    result = {
        "train": [],
        "val": [],
        "test": [],
    }

    for label, video_ids in grouped.items():
        video_ids = list(dict.fromkeys(video_ids))
        rng.shuffle(video_ids)

        n = len(video_ids)

        if n < 3:
            raise ValueError(
                f"Label {label} needs at least 3 source videos"
            )

        train_end = max(1, int(n * train_ratio))
        val_end = train_end + max(1, int(n * val_ratio))

        if val_end >= n:
            val_end = n - 1

        result["train"].extend(video_ids[:train_end])
        result["val"].extend(video_ids[train_end:val_end])
        result["test"].extend(video_ids[val_end:])

    return result
