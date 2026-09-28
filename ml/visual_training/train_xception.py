from __future__ import annotations

import argparse
import random
from pathlib import Path

import numpy as np
import torch
from torch import nn
from torch.optim import AdamW
from torch.utils.data import DataLoader

from app.services.visual.model.xception.detector import SpectraXXception
from ml.visual_training.dataset import FFPPFaceDataset


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def evaluate(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    device: torch.device,
) -> tuple[float, float]:

    model.eval()

    total_loss = 0.0
    total = 0
    correct = 0

    with torch.no_grad():
        for images, labels in loader:
            images = images.to(device)
            labels = labels.to(device)

            logits = model(images)
            loss = criterion(logits, labels)

            batch_size = labels.size(0)

            total_loss += loss.item() * batch_size
            total += batch_size

            correct += (
                logits.argmax(dim=1) == labels
            ).sum().item()

    if total == 0:
        raise RuntimeError("Validation loader is empty")

    return total_loss / total, correct / total


def train_one_epoch(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    optimizer: torch.optim.Optimizer,
    device: torch.device,
) -> tuple[float, float]:

    model.train()

    total_loss = 0.0
    total = 0
    correct = 0

    for images, labels in loader:
        images = images.to(device)
        labels = labels.to(device)

        optimizer.zero_grad(set_to_none=True)

        logits = model(images)
        loss = criterion(logits, labels)

        loss.backward()
        optimizer.step()

        batch_size = labels.size(0)

        total_loss += loss.item() * batch_size
        total += batch_size

        correct += (
            logits.argmax(dim=1) == labels
        ).sum().item()

    if total == 0:
        raise RuntimeError("Training loader is empty")

    return total_loss / total, correct / total


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--train-manifest",
        type=Path,
        default=Path(
            "datasets/visual/manifests/visual_samples_train.jsonl"
        ),
    )

    parser.add_argument(
        "--val-manifest",
        type=Path,
        default=Path(
            "datasets/visual/manifests/visual_samples_val.jsonl"
        ),
    )

    parser.add_argument(
        "--epochs",
        type=int,
        default=1,
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=4,
    )

    parser.add_argument(
        "--learning-rate",
        type=float,
        default=1e-4,
    )

    parser.add_argument(
        "--weight-decay",
        type=float,
        default=1e-4,
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
    )

    parser.add_argument(
        "--checkpoint",
        type=Path,
        default=Path(
            "ml/visual_training/checkpoints/"
            "spectrax_xception_best.pt"
        ),
    )

    parser.add_argument(
        "--pretrained-checkpoint",
        type=Path,
        default=Path(
            "ml/visual_training/checkpoints/"
            "xception-b5690688.pth"
        ),
    )

    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume training from the output checkpoint.",
    )

    args = parser.parse_args()

    set_seed(args.seed)

    device = torch.device(
        "cuda" if torch.cuda.is_available() else "cpu"
    )

    print("Device:", device)

    train_dataset = FFPPFaceDataset(
        args.train_manifest,
        split="train",
    )

    train_loader = DataLoader(
        train_dataset,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=0,
    )

    val_dataset = FFPPFaceDataset(
        args.val_manifest,
        split="val",
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=0,
    )

    model = SpectraXXception(
        num_classes=2,
    )

    if not args.pretrained_checkpoint.exists():
        raise FileNotFoundError(
            "Pretrained Xception checkpoint not found: "
            f"{args.pretrained_checkpoint}"
        )

    state_dict = torch.load(
        args.pretrained_checkpoint,
        map_location=device,
        weights_only=True,
    )

    converted = {}

    for name, weights in state_dict.items():
        if "pointwise" in name and weights.ndim == 2:
            weights = weights.unsqueeze(-1).unsqueeze(-1)

        if "fc" in name:
            continue

        converted[name] = weights

    load_result = model.load_state_dict(
        converted,
        strict=False,
    )

    allowed_missing = {
        "last_linear.weight",
        "last_linear.bias",
    }

    actual_missing = set(load_result.missing_keys)

    if actual_missing != allowed_missing:
        raise RuntimeError(
            "Unexpected missing Xception checkpoint keys: "
            f"{sorted(actual_missing)}"
        )

    if load_result.unexpected_keys:
        raise RuntimeError(
            "Unexpected Xception checkpoint keys: "
            f"{load_result.unexpected_keys}"
        )

    model = model.to(device)

    print(
        "Loaded ImageNet Xception backbone:",
        args.pretrained_checkpoint,
    )

    class_counts = torch.bincount(
        torch.tensor(
            [int(record["label"]) for record in train_dataset.records],
            dtype=torch.long,
        ),
        minlength=2,
    )

    if torch.any(class_counts == 0):
        raise RuntimeError(
            "Training manifest must contain both classes: "
            f"counts={class_counts.tolist()}"
        )

    total_samples = class_counts.sum().item()
    class_weights = total_samples / (
        2.0 * class_counts.float()
    )

    class_weights = class_weights.to(device)

    print(
        "Training class counts:",
        class_counts.tolist(),
    )
    print(
        "Training class weights:",
        class_weights.tolist(),
    )

    criterion = nn.CrossEntropyLoss(
        weight=class_weights,
    )

    optimizer = AdamW(
        model.parameters(),
        lr=args.learning_rate,
        weight_decay=args.weight_decay,
    )

    best_val_loss = float("inf")
    start_epoch = 1

    if args.resume:
        if not args.checkpoint.exists():
            raise FileNotFoundError(
                "Resume checkpoint not found: "
                f"{args.checkpoint}"
            )

        resume_checkpoint = torch.load(
            args.checkpoint,
            map_location=device,
            weights_only=True,
        )

        required_resume_keys = {
            "model_state_dict",
            "optimizer_state_dict",
            "epoch",
            "best_val_loss",
        }

        missing_resume_keys = (
            required_resume_keys
            - resume_checkpoint.keys()
        )

        if missing_resume_keys:
            raise RuntimeError(
                "Checkpoint does not support exact resume. "
                f"Missing keys: {sorted(missing_resume_keys)}"
            )

        model.load_state_dict(
            resume_checkpoint["model_state_dict"]
        )

        optimizer.load_state_dict(
            resume_checkpoint["optimizer_state_dict"]
        )

        start_epoch = int(resume_checkpoint["epoch"]) + 1
        best_val_loss = float(
            resume_checkpoint["best_val_loss"]
        )

        print(
            "Resumed training from epoch:",
            resume_checkpoint["epoch"],
        )

    for epoch in range(start_epoch, args.epochs + 1):
        train_loss, train_accuracy = train_one_epoch(
            model,
            train_loader,
            criterion,
            optimizer,
            device,
        )

        val_loss, val_accuracy = evaluate(
            model,
            val_loader,
            criterion,
            device,
        )

        print(
            f"epoch={epoch} "
            f"train_loss={train_loss:.6f} "
            f"train_accuracy={train_accuracy:.4f} "
            f"val_loss={val_loss:.6f} "
            f"val_accuracy={val_accuracy:.4f}"
        )

        if val_loss < best_val_loss:
            best_val_loss = val_loss

            args.checkpoint.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            torch.save(
                {
                    "model_state_dict": model.state_dict(),
                    "optimizer_state_dict": optimizer.state_dict(),
                    "epoch": epoch,
                    "best_val_loss": best_val_loss,
                    "train_loss": train_loss,
                    "train_accuracy": train_accuracy,
                    "val_loss": val_loss,
                    "val_accuracy": val_accuracy,
                },
                args.checkpoint,
            )

            print(
                "Saved checkpoint:",
                args.checkpoint,
            )



if __name__ == "__main__":
    main()
