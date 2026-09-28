from pathlib import Path

import torch
from PIL import Image
from torchvision.models import ResNet18_Weights, resnet18


class ResNet18FeatureExtractor:
    """
    ImageNet-pretrained ResNet18 used as a visual feature extractor.

    The ImageNet classification head is removed. The extractor returns
    a 512-dimensional representation for an input face image.
    """

    def __init__(self) -> None:
        weights = ResNet18_Weights.DEFAULT

        model = resnet18(weights=weights)

        self._model = torch.nn.Sequential(*list(model.children())[:-1])
        self._model.eval()

        self._preprocess = weights.transforms()

    @property
    def model_name(self) -> str:
        return "resnet18"

    @property
    def model_version(self) -> str:
        return "IMAGENET1K_V1"

    @torch.inference_mode()
    def extract(self, image_path: str | Path) -> torch.Tensor:
        image = Image.open(image_path).convert("RGB")

        tensor = self._preprocess(image).unsqueeze(0)

        features = self._model(tensor)

        return features.flatten(1).squeeze(0)
