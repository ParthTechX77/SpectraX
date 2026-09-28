from __future__ import annotations

import argparse
import json
import uuid
from pathlib import Path

import cv2

from app.services.visual.face.alignment import OpenCVFaceCropAligner
from app.services.visual.face.detector import OpenCVHaarFaceDetector
from ml.visual_training.ffpp_importer import discover_videos
from ml.visual_training.ffpp_splits import (
    build_source_membership,
    resolve_manipulated_split,
)
from ml.visual_training.manifest_schema import (
    VisualSample,
    validate_sample,
)


DEFAULT_DATASET_ROOT = Path(
    "datasets/visual/source/faceforensicspp"
)

DEFAULT_SPLIT_ROOT = Path(
    "external/FaceForensics/dataset/splits"
)

DEFAULT_OUTPUT_ROOT = Path(
    "datasets/visual/face_crops"
)

DEFAULT_MANIFEST = Path(
    "datasets/visual/manifests/visual_samples.jsonl"
)


def resolve_video_split(
    source_video_id: str,
    manipulation_type: str,
    membership,
) -> str:
    if manipulation_type == "original":
        item = membership.get(source_video_id)

        if item is None:
            raise ValueError(
                f"Original source video {source_video_id!r} "
                "is not present in official FF++ splits"
            )

        return item.split

    return resolve_manipulated_split(
        source_video_id,
        membership,
    )


def sample_video(
    *,
    video,
    split: str,
    output_root: Path,
    detector: OpenCVHaarFaceDetector,
    aligner: OpenCVFaceCropAligner,
    frames_per_video: int,
) -> list[VisualSample]:

    capture = cv2.VideoCapture(str(video.path))

    if not capture.isOpened():
        raise RuntimeError(
            f"Could not open video: {video.path}"
        )

    total_frames = int(
        capture.get(cv2.CAP_PROP_FRAME_COUNT)
    )

    fps = float(
        capture.get(cv2.CAP_PROP_FPS)
    )

    if total_frames <= 0:
        capture.release()
        raise RuntimeError(
            f"Invalid frame count for {video.path}"
        )

    if fps <= 0:
        fps = 1.0

    sample_count = min(
        frames_per_video,
        total_frames,
    )

    if sample_count == 1:
        frame_indices = [0]
    else:
        frame_indices = [
            round(
                index * (total_frames - 1)
                / (sample_count - 1)
            )
            for index in range(sample_count)
        ]

    samples: list[VisualSample] = []

    for frame_index in frame_indices:
        capture.set(
            cv2.CAP_PROP_POS_FRAMES,
            frame_index,
        )

        ok, frame = capture.read()

        if not ok:
            continue

        frame_number = frame_index + 1
        timestamp_seconds = frame_index / fps

        temporary_frame = (
            output_root
            / "_frames"
            / video.manipulation_type
            / video.source_video_id
            / f"frame_{frame_number:06d}.jpg"
        )

        temporary_frame.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        if not cv2.imwrite(
            str(temporary_frame),
            frame,
        ):
            raise RuntimeError(
                f"Could not write frame: {temporary_frame}"
            )

        detections = detector.detect(
            frame_id=uuid.uuid4(),
            frame_path=temporary_frame,
        )

        if not detections:
            continue

        # Use the largest detected face as the primary subject.
        face = max(
            detections,
            key=lambda item: (item.x2 - item.x1) * (item.y2 - item.y1),
        )
        face_index = 0

        for face_index, face in [(face_index, face)]:
            sample_id = (
                f"{video.manipulation_type}-"
                f"{video.source_video_id}-"
                f"{frame_number:06d}-"
                f"{face_index:02d}"
            )

            crop_path = (
                output_root
                / split
                / video.manipulation_type
                / video.source_video_id
                / f"face_{frame_number:06d}_{face_index:02d}.jpg"
            )

            aligner.align(
                frame_path=temporary_frame,
                face=face,
                output_path=crop_path,
            )

            sample = VisualSample(
                sample_id=sample_id,
                source_video_id=video.source_video_id,
                frame_number=frame_number,
                frame_path=str(crop_path),
                label=video.label,
                manipulation_type=video.manipulation_type,
                split=split,
                timestamp_seconds=timestamp_seconds,
                face_index=face_index,
                face_x1=face.x1,
                face_y1=face.y1,
                face_x2=face.x2,
                face_y2=face.y2,
            )

            validate_sample(sample)
            samples.append(sample)

    capture.release()

    return samples


def write_manifest(
    samples: list[VisualSample],
    output: Path,
) -> None:
    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output.open(
        "w",
        encoding="utf-8",
    ) as handle:
        for sample in samples:
            handle.write(
                json.dumps(
                    {
                        "sample_id": sample.sample_id,
                        "source_video_id": sample.source_video_id,
                        "frame_number": sample.frame_number,
                        "frame_path": sample.frame_path,
                        "label": sample.label,
                        "manipulation_type": sample.manipulation_type,
                        "split": sample.split,
                        "timestamp_seconds": sample.timestamp_seconds,
                        "face_index": sample.face_index,
                        "face_x1": sample.face_x1,
                        "face_y1": sample.face_y1,
                        "face_x2": sample.face_x2,
                        "face_y2": sample.face_y2,
                    },
                    sort_keys=True,
                )
                + "\n"
            )


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--dataset-root",
        type=Path,
        default=DEFAULT_DATASET_ROOT,
    )

    parser.add_argument(
        "--split-root",
        type=Path,
        default=DEFAULT_SPLIT_ROOT,
    )

    parser.add_argument(
        "--output-root",
        type=Path,
        default=DEFAULT_OUTPUT_ROOT,
    )

    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST,
    )

    parser.add_argument(
        "--frames-per-video",
        type=int,
        default=4,
    )

    parser.add_argument(
        "--max-videos",
        type=int,
        default=None,
    )

    parser.add_argument(
        "--manipulation-types",
        nargs="+",
        default=None,
        help="Only process these FF++ manipulation types.",
    )

    parser.add_argument(
        "--splits",
        nargs="+",
        choices=["train", "val", "test"],
        default=None,
        help="Only process videos belonging to these official FF++ splits.",
    )

    parser.add_argument(
        "--max-per-type",
        type=int,
        default=None,
        help="Maximum number of videos to process per manipulation type.",
    )

    parser.add_argument(
        "--max-per-split-type",
        type=int,
        default=None,
        help="Maximum number of videos per official split and manipulation type.",
    )

    args = parser.parse_args()

    if args.frames_per_video <= 0:
        raise ValueError(
            "--frames-per-video must be positive"
        )

    membership = build_source_membership(
        args.split_root
    )

    videos = discover_videos(
        args.dataset_root
    )

    if args.manipulation_types:
        allowed = set(args.manipulation_types)
        videos = [
            video
            for video in videos
            if video.manipulation_type in allowed
        ]

    if args.splits:
        allowed_splits = set(args.splits)
        videos = [
            video
            for video in videos
            if resolve_video_split(
                video.source_video_id,
                video.manipulation_type,
                membership,
            ) in allowed_splits
        ]

    if args.max_per_type is not None:
        if args.max_per_type <= 0:
            raise ValueError("--max-per-type must be positive")

        selected = []
        counts = {}

        for video in videos:
            count = counts.get(video.manipulation_type, 0)

            if count >= args.max_per_type:
                continue

            selected.append(video)
            counts[video.manipulation_type] = count + 1

        videos = selected

    if args.max_per_split_type is not None:
        if args.max_per_split_type <= 0:
            raise ValueError("--max-per-split-type must be positive")

        selected = []
        counts = {}

        for video in videos:
            split = resolve_video_split(
                video.source_video_id,
                video.manipulation_type,
                membership,
            )

            key = (split, video.manipulation_type)
            count = counts.get(key, 0)

            if count >= args.max_per_split_type:
                continue

            selected.append(video)
            counts[key] = count + 1

        videos = selected

    if args.max_videos is not None:
        videos = videos[:args.max_videos]

    detector = OpenCVHaarFaceDetector()
    aligner = OpenCVFaceCropAligner()

    all_samples: list[VisualSample] = []

    for index, video in enumerate(videos, start=1):
        split = resolve_video_split(
            video.source_video_id,
            video.manipulation_type,
            membership,
        )

        print(
            f"[{index}/{len(videos)}] "
            f"{video.manipulation_type}/"
            f"{video.source_video_id} "
            f"-> {split}"
        )

        samples = sample_video(
            video=video,
            split=split,
            output_root=args.output_root,
            detector=detector,
            aligner=aligner,
            frames_per_video=args.frames_per_video,
        )

        print(
            f"  faces/samples: {len(samples)}"
        )

        all_samples.extend(samples)

    write_manifest(
        all_samples,
        args.manifest,
    )

    print()
    print("Manifest generation complete")
    print("Videos:", len(videos))
    print("Samples:", len(all_samples))
    print("Manifest:", args.manifest)


if __name__ == "__main__":
    main()
