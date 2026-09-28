from pathlib import Path
from time import perf_counter
from uuid import UUID, uuid4

from PIL import Image
from torchvision import transforms

from app.services.visual.detector import VisualDetector
from app.services.visual.face.alignment import OpenCVFaceCropAligner
from app.services.visual.face.detector import OpenCVHaarFaceDetector
from app.services.visual.schemas import VisualDetectionResult
from app.services.visual.model.xception.detector import XceptionDeepfakeClassifier


class XceptionVisualDetector(VisualDetector):
    """
    Frame-level visual deepfake detector.

    Pipeline:
        frame -> face detection -> largest face crop -> Xception classifier
    """

    def __init__(
        self,
        *,
        checkpoint_path: str | Path,
        device: str = "cpu",
        temporary_root: str | Path = "storage/temporary",
    ) -> None:
        self._face_detector = OpenCVHaarFaceDetector()
        self._face_aligner = OpenCVFaceCropAligner()
        self._classifier = XceptionDeepfakeClassifier(
            checkpoint_path=checkpoint_path,
            device=device,
        )

        self._temporary_root = Path(temporary_root)
        self._temporary_root.mkdir(parents=True, exist_ok=True)

        self._preprocess = transforms.Compose(
            [
                transforms.Resize((256, 256)),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.5, 0.5, 0.5],
                    std=[0.5, 0.5, 0.5],
                ),
            ]
        )

    @property
    def model_name(self) -> str:
        return self._classifier.model_name

    @property
    def model_version(self) -> str:
        return self._classifier.model_version

    def detect(
        self,
        *,
        frame_id: UUID,
        frame_path: str | Path,
        timestamp_seconds: float,
    ) -> VisualDetectionResult:
        started = perf_counter()

        detections = self._face_detector.detect(
            frame_id=frame_id,
            frame_path=frame_path,
        )

        if not detections:
            elapsed_ms = (perf_counter() - started) * 1000.0

            return VisualDetectionResult(
                frame_id=frame_id,
                timestamp_seconds=timestamp_seconds,
                score=0.0,
                model_name=self.model_name,
                model_version=self.model_version,
                face_detected=False,
                processing_time_ms=elapsed_ms,
            )

        face = max(
            detections,
            key=lambda item: (item.x2 - item.x1) * (item.y2 - item.y1),
        )

        crop_path = (
            self._temporary_root
            / f"spectrax_face_{uuid4().hex}.jpg"
        )

        try:
            self._face_aligner.align(
                frame_path=frame_path,
                face=face,
                output_path=crop_path,
            )

            image = Image.open(crop_path).convert("RGB")
            tensor = self._preprocess(image).unsqueeze(0)

            result = self._classifier.predict(tensor)

            elapsed_ms = (perf_counter() - started) * 1000.0

            return VisualDetectionResult(
                frame_id=frame_id,
                timestamp_seconds=timestamp_seconds,
                score=result["fake_probability"],
                model_name=self.model_name,
                model_version=self.model_version,
                face_detected=True,
                processing_time_ms=elapsed_ms,
            )
        finally:
            crop_path.unlink(missing_ok=True)
