from pathlib import Path

import torch
import torch.nn as nn
import torch.nn.functional as F


class SeparableConv2d(nn.Module):
    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        kernel_size: int = 1,
        stride: int = 1,
        padding: int = 0,
        dilation: int = 1,
        bias: bool = False,
    ):
        super().__init__()

        self.conv1 = nn.Conv2d(
            in_channels,
            in_channels,
            kernel_size,
            stride,
            padding,
            dilation,
            groups=in_channels,
            bias=bias,
        )
        self.pointwise = nn.Conv2d(
            in_channels,
            out_channels,
            1,
            1,
            0,
            1,
            1,
            bias=bias,
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.conv1(x)
        return self.pointwise(x)


class Block(nn.Module):
    def __init__(
        self,
        in_filters: int,
        out_filters: int,
        reps: int,
        strides: int = 1,
        start_with_relu: bool = True,
        grow_first: bool = True,
    ):
        super().__init__()

        if out_filters != in_filters or strides != 1:
            self.skip = nn.Conv2d(
                in_filters,
                out_filters,
                1,
                stride=strides,
                bias=False,
            )
            self.skipbn = nn.BatchNorm2d(out_filters)
        else:
            self.skip = None

        self.relu = nn.ReLU(inplace=True)

        rep = []
        filters = in_filters

        if grow_first:
            rep.extend(
                [
                    self.relu,
                    SeparableConv2d(
                        in_filters,
                        out_filters,
                        3,
                        stride=1,
                        padding=1,
                        bias=False,
                    ),
                    nn.BatchNorm2d(out_filters),
                ]
            )
            filters = out_filters

        for _ in range(reps - 1):
            rep.extend(
                [
                    self.relu,
                    SeparableConv2d(
                        filters,
                        filters,
                        3,
                        stride=1,
                        padding=1,
                        bias=False,
                    ),
                    nn.BatchNorm2d(filters),
                ]
            )

        if not grow_first:
            rep.extend(
                [
                    self.relu,
                    SeparableConv2d(
                        in_filters,
                        out_filters,
                        3,
                        stride=1,
                        padding=1,
                        bias=False,
                    ),
                    nn.BatchNorm2d(out_filters),
                ]
            )

        if not start_with_relu:
            rep = rep[1:]
        else:
            rep[0] = nn.ReLU(inplace=False)

        if strides != 1:
            rep.append(nn.MaxPool2d(3, strides, 1))

        self.rep = nn.Sequential(*rep)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        residual = self.rep(x)

        if self.skip is not None:
            skip = self.skip(x)
            skip = self.skipbn(skip)
        else:
            skip = x

        return residual + skip


class SpectraXXception(nn.Module):
    """
    SpectraX-native Xception classifier.

    Architecture adapted from the Xception implementation used by
    DeepfakeBench. The model produces two logits:
      class 0 -> real
      class 1 -> manipulated/deepfake

    The weights are intentionally not bundled here.
    """

    def __init__(self, num_classes: int = 2, in_channels: int = 3):
        super().__init__()

        self.num_classes = num_classes

        self.conv1 = nn.Conv2d(
            in_channels, 32, 3, 2, 0, bias=False
        )
        self.bn1 = nn.BatchNorm2d(32)
        self.relu = nn.ReLU(inplace=True)

        self.conv2 = nn.Conv2d(32, 64, 3, bias=False)
        self.bn2 = nn.BatchNorm2d(64)

        self.block1 = Block(
            64, 128, 2, 2,
            start_with_relu=False,
            grow_first=True,
        )
        self.block2 = Block(
            128, 256, 2, 2,
            start_with_relu=True,
            grow_first=True,
        )
        self.block3 = Block(
            256, 728, 2, 2,
            start_with_relu=True,
            grow_first=True,
        )

        self.block4 = Block(728, 728, 3)
        self.block5 = Block(728, 728, 3)
        self.block6 = Block(728, 728, 3)
        self.block7 = Block(728, 728, 3)
        self.block8 = Block(728, 728, 3)
        self.block9 = Block(728, 728, 3)
        self.block10 = Block(728, 728, 3)
        self.block11 = Block(728, 728, 3)

        self.block12 = Block(
            728,
            1024,
            2,
            2,
            start_with_relu=True,
            grow_first=False,
        )

        self.conv3 = SeparableConv2d(1024, 1536, 3, 1, 1)
        self.bn3 = nn.BatchNorm2d(1536)

        self.conv4 = SeparableConv2d(1536, 2048, 3, 1, 1)
        self.bn4 = nn.BatchNorm2d(2048)

        self.last_linear = nn.Linear(2048, num_classes)

    def features(self, x: torch.Tensor) -> torch.Tensor:
        x = self.conv1(x)
        x = self.bn1(x)
        x = self.relu(x)

        x = self.conv2(x)
        x = self.bn2(x)
        x = self.relu(x)

        x = self.block1(x)
        x = self.block2(x)
        x = self.block3(x)

        x = self.block4(x)
        x = self.block5(x)
        x = self.block6(x)
        x = self.block7(x)
        x = self.block8(x)
        x = self.block9(x)
        x = self.block10(x)
        x = self.block11(x)
        x = self.block12(x)

        x = self.conv3(x)
        x = self.bn3(x)
        x = self.relu(x)

        x = self.conv4(x)
        x = self.bn4(x)

        return x

    def classifier(self, features: torch.Tensor) -> torch.Tensor:
        x = self.relu(features)

        if x.ndim == 4:
            x = F.adaptive_avg_pool2d(x, (1, 1))
            x = x.flatten(1)

        return self.last_linear(x)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.classifier(self.features(x))


class XceptionDeepfakeClassifier:
    """
    SpectraX inference wrapper.

    No checkpoint is loaded unless explicitly supplied.
    """

    def __init__(
        self,
        checkpoint_path: str | Path | None = None,
        device: str = "cpu",
    ):
        self.device = torch.device(device)
        self.model = SpectraXXception(num_classes=2).to(self.device)

        if checkpoint_path is not None:
            checkpoint = Path(checkpoint_path)

            if not checkpoint.exists():
                raise FileNotFoundError(
                    f"Xception checkpoint not found: {checkpoint}"
                )

            loaded = torch.load(
                checkpoint,
                map_location=self.device,
                weights_only=True,
            )

            # SpectraX training checkpoints wrap the model weights
            # inside "model_state_dict". Raw Xception checkpoints
            # contain the state dict directly.
            if "model_state_dict" in loaded:
                state_dict = loaded["model_state_dict"]
                trained_checkpoint = True
            else:
                state_dict = loaded
                trained_checkpoint = False

            converted = {}

            for name, weights in state_dict.items():
                if "pointwise" in name and weights.ndim == 2:
                    weights = weights.unsqueeze(-1).unsqueeze(-1)

                # Raw ImageNet Xception checkpoints may contain an
                # incompatible fc head. SpectraX training checkpoints
                # contain the compatible trained last_linear head.
                if "fc" in name and not trained_checkpoint:
                    continue

                converted[name] = weights

            result = self.model.load_state_dict(
                converted,
                strict=False,
            )

            allowed_missing = (
                set()
                if trained_checkpoint
                else {
                    "last_linear.weight",
                    "last_linear.bias",
                }
            )

            actual_missing = set(result.missing_keys)

            if actual_missing != allowed_missing:
                raise RuntimeError(
                    "Unexpected missing Xception checkpoint keys: "
                    f"{sorted(actual_missing)}"
                )

            if result.unexpected_keys:
                raise RuntimeError(
                    "Unexpected Xception checkpoint keys: "
                    f"{result.unexpected_keys}"
                )

        self.model.eval()

    @property
    def model_name(self) -> str:
        return "spectrax_xception"

    @property
    def model_version(self) -> str:
        return "spectrax-xception-ffpp-c23-v1"

    @torch.inference_mode()
    def predict(self, tensor: torch.Tensor) -> dict:
        tensor = tensor.to(self.device)

        logits = self.model(tensor)
        probabilities = torch.softmax(logits, dim=1)

        return {
            "real_probability": float(probabilities[0, 0].item()),
            "fake_probability": float(probabilities[0, 1].item()),
            "logits": logits[0].detach().cpu().tolist(),
        }
