from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class FFPPVideo:
    source_video_id: str
    path: Path
    label: int
    manipulation_type: str


MANIPULATIONS = {
    "Deepfakes": 1,
    "Face2Face": 1,
    "FaceSwap": 1,
    "NeuralTextures": 1,
}


VIDEO_EXTENSIONS = {
    ".mp4",
    ".avi",
    ".mov",
    ".mkv",
}


def _discover_category(
    category_root: Path,
    *,
    label: int,
    manipulation_type: str,
) -> list[FFPPVideo]:
    results: list[FFPPVideo] = []

    if not category_root.is_dir():
        return results

    for path in sorted(category_root.rglob("*")):
        if not path.is_file():
            continue

        if path.suffix.lower() not in VIDEO_EXTENSIONS:
            continue

        results.append(
            FFPPVideo(
                source_video_id=path.stem,
                path=path,
                label=label,
                manipulation_type=manipulation_type,
            )
        )

    return results


def discover_videos(dataset_root: Path) -> list[FFPPVideo]:
    results: list[FFPPVideo] = []

    original_root = (
        dataset_root
        / "original_sequences"
        / "youtube"
        / "c23"
        / "videos"
    )

    results.extend(
        _discover_category(
            original_root,
            label=0,
            manipulation_type="original",
        )
    )

    for manipulation_type, label in MANIPULATIONS.items():
        category_root = (
            dataset_root
            / "manipulated_sequences"
            / manipulation_type
            / "c23"
            / "videos"
        )

        results.extend(
            _discover_category(
                category_root,
                label=label,
                manipulation_type=manipulation_type,
            )
        )

    return results


if __name__ == "__main__":
    root = Path(
        "datasets/visual/source/faceforensicspp"
    )

    videos = discover_videos(root)

    print(f"Discovered videos: {len(videos)}")

    counts: dict[str, int] = {}

    for video in videos:
        counts[video.manipulation_type] = (
            counts.get(video.manipulation_type, 0) + 1
        )

    for category, count in sorted(counts.items()):
        print(f"{category}: {count}")

    for video in videos[:10]:
        print(
            video.source_video_id,
            video.label,
            video.manipulation_type,
            video.path,
        )
