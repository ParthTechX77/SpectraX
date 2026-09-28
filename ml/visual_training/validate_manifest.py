from __future__ import annotations

import json
from pathlib import Path


MANIFEST = Path(
    "datasets/visual/manifests/visual_samples.jsonl"
)

VALID_LABELS = {0, 1}
VALID_SPLITS = {"train", "val", "test"}


def validate_manifest(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(path)

    seen_samples: set[str] = set()
    source_splits: dict[str, str] = {}
    counts = {
        "train": {0: 0, 1: 0},
        "val": {0: 0, 1: 0},
        "test": {0: 0, 1: 0},
    }

    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue

            try:
                sample = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSON at line {line_number}"
                ) from exc

            required = {
                "sample_id",
                "source_video_id",
                "frame_path",
                "label",
                "manipulation_type",
                "split",
            }

            missing = required - sample.keys()
            if missing:
                raise ValueError(
                    f"Line {line_number}: missing fields "
                    f"{sorted(missing)}"
                )

            sample_id = sample["sample_id"]
            source_video_id = sample["source_video_id"]
            label = sample["label"]
            split = sample["split"]

            if sample_id in seen_samples:
                raise ValueError(
                    f"Duplicate sample_id: {sample_id}"
                )

            if label not in VALID_LABELS:
                raise ValueError(
                    f"Invalid label at line {line_number}: {label}"
                )

            if split not in VALID_SPLITS:
                raise ValueError(
                    f"Invalid split at line {line_number}: {split}"
                )

            previous_split = source_splits.get(source_video_id)

            if (
                previous_split is not None
                and previous_split != split
            ):
                raise ValueError(
                    "Source-video leakage detected: "
                    f"{source_video_id} appears in "
                    f"{previous_split} and {split}"
                )

            seen_samples.add(sample_id)
            source_splits[source_video_id] = split
            counts[split][label] += 1

    print(f"Samples: {len(seen_samples)}")
    print(f"Train: {counts['train']}")
    print(f"Val:   {counts['val']}")
    print(f"Test:  {counts['test']}")
    print("Manifest validation: PASS")


if __name__ == "__main__":
    validate_manifest(MANIFEST)
