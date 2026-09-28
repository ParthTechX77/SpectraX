from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class FFPPSourceSplit:
    source_video_id: str
    split: str


SPLITS = ("train", "val", "test")


def load_split_file(path: Path) -> list[tuple[str, str]]:
    data = json.loads(path.read_text(encoding="utf-8"))

    pairs: list[tuple[str, str]] = []

    for entry in data:
        if not isinstance(entry, list) or len(entry) != 2:
            raise ValueError(
                f"Invalid FF++ split entry: {entry!r}"
            )

        pairs.append((str(entry[0]), str(entry[1])))

    return pairs


def load_all_splits(
    split_root: Path,
) -> dict[str, list[tuple[str, str]]]:
    result = {}

    for split in SPLITS:
        result[split] = load_split_file(
            split_root / f"{split}.json"
        )

    return result


def build_source_membership(
    split_root: Path,
) -> dict[str, FFPPSourceSplit]:
    splits = load_all_splits(split_root)

    membership: dict[str, FFPPSourceSplit] = {}

    for split, pairs in splits.items():
        for first, second in pairs:
            for source_id in (first, second):
                previous = membership.get(source_id)

                if previous is not None and previous.split != split:
                    raise ValueError(
                        f"Source ID {source_id} appears in "
                        f"{previous.split} and {split}"
                    )

                membership[source_id] = FFPPSourceSplit(
                    source_video_id=source_id,
                    split=split,
                )

    return membership


if __name__ == "__main__":
    root = Path("external/FaceForensics/dataset/splits")

    membership = build_source_membership(root)

    counts = {
        split: sum(
            item.split == split
            for item in membership.values()
        )
        for split in SPLITS
    }

    print("Source membership:")
    for split in SPLITS:
        print(f"{split}: {counts[split]}")

    print("Total unique source IDs:", len(membership))
    print("Cross-split leakage check: PASS")


def resolve_manipulated_split(
    source_video_id: str,
    membership: dict[str, FFPPSourceSplit],
) -> str:
    parts = source_video_id.split("_")

    if len(parts) != 2:
        raise ValueError(
            f"Expected manipulated FF++ video ID "
            f"'source_target', got: {source_video_id!r}"
        )

    first, second = parts

    first_split = membership.get(first)
    second_split = membership.get(second)

    if first_split is None or second_split is None:
        raise ValueError(
            f"Missing official split membership for "
            f"{source_video_id!r}: "
            f"{first!r}={first_split}, "
            f"{second!r}={second_split}"
        )

    if first_split.split != second_split.split:
        raise ValueError(
            f"Cross-split manipulated pair detected: "
            f"{source_video_id!r} -> "
            f"{first_split.split}, {second_split.split}"
        )

    return first_split.split
