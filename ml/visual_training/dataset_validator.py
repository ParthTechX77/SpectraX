from __future__ import annotations

import json
from pathlib import Path


CONFIG_PATH = Path("datasets/visual/dataset_config.json")


EXPECTED_MANIPULATIONS = {
    "original",
    "Deepfakes",
    "Face2Face",
    "FaceSwap",
    "NeuralTextures",
}


def load_config() -> dict:
    with CONFIG_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_config(config: dict) -> None:
    if config["dataset_name"] != "FaceForensics++":
        raise ValueError("Unexpected dataset")

    if config["compression"] != "c23":
        raise ValueError("Expected c23 compression")

    if config["resolution"] != 256:
        raise ValueError("Expected 256px resolution")

    if config["label_map"].get("original") != 0:
        raise ValueError("original must map to label 0")

    for name in EXPECTED_MANIPULATIONS - {"original"}:
        if config["label_map"].get(name) != 1:
            raise ValueError(f"{name} must map to label 1")

    splits = config["splits"]

    if abs(sum(splits.values()) - 1.0) > 1e-9:
        raise ValueError("Split ratios must sum to 1.0")

    if config["frames_per_video"] <= 0:
        raise ValueError("frames_per_video must be positive")

    print("Dataset configuration: PASS")


def inspect_dataset_root(root: Path) -> None:
    if not root.exists():
        print(f"Dataset root not present yet: {root}")
        print("Configuration is valid; dataset files are not installed.")
        return

    if not root.is_dir():
        raise ValueError(f"Dataset root is not a directory: {root}")

    print(f"Dataset root: {root}")
    print("Dataset root exists.")


if __name__ == "__main__":
    config = load_config()
    validate_config(config)

    inspect_dataset_root(
        Path("datasets/visual/faceforensicspp")
    )
