from __future__ import annotations

import argparse
from pathlib import Path

import torch
from torch.utils.data import DataLoader

from app.services.visual.model.xception.detector import SpectraXXception
from ml.visual_training.dataset import FFPPFaceDataset


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path(
            "datasets/visual/manifests/"
            "visual_samples_test_v2.jsonl"
        ),
    )
    parser.add_argument(
        "--checkpoint",
        type=Path,
        default=Path(
            "ml/visual_training/checkpoints/"
            "spectrax_xception_v1.pt"
        ),
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=4,
    )

    args = parser.parse_args()

    device = torch.device(
        "cuda" if torch.cuda.is_available() else "cpu"
    )

    print("Device:", device)
    print("Manifest:", args.manifest)
    print("Checkpoint:", args.checkpoint)

    dataset = FFPPFaceDataset(
        manifest_path=args.manifest,
        split="test",
        resolution=256,
    )

    loader = DataLoader(
        dataset,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=0,
    )

    model = SpectraXXception(num_classes=2)

    checkpoint = torch.load(
        args.checkpoint,
        map_location=device,
        weights_only=True,
    )

    model.load_state_dict(
        checkpoint["model_state_dict"]
    )

    model.to(device)
    model.eval()

    y_true = []
    y_pred = []

    with torch.no_grad():
        for images, labels in loader:
            images = images.to(device)

            logits = model(images)
            predictions = logits.argmax(dim=1).cpu()

            y_true.extend(labels.tolist())
            y_pred.extend(predictions.tolist())

    if not y_true:
        raise RuntimeError("Test dataset is empty")

    tp = sum(
        1 for y, p in zip(y_true, y_pred)
        if y == 1 and p == 1
    )
    tn = sum(
        1 for y, p in zip(y_true, y_pred)
        if y == 0 and p == 0
    )
    fp = sum(
        1 for y, p in zip(y_true, y_pred)
        if y == 0 and p == 1
    )
    fn = sum(
        1 for y, p in zip(y_true, y_pred)
        if y == 1 and p == 0
    )

    total = len(y_true)

    accuracy = (tp + tn) / total

    precision = (
        tp / (tp + fp)
        if (tp + fp)
        else 0.0
    )

    recall = (
        tp / (tp + fn)
        if (tp + fn)
        else 0.0
    )

    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall)
        else 0.0
    )

    print("\n=== TEST RESULTS ===")
    print("Samples:", total)
    print(f"Accuracy : {accuracy:.4f}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall   : {recall:.4f}")
    print(f"F1       : {f1:.4f}")

    print("\n=== CONFUSION MATRIX ===")
    print("              Pred Real   Pred Fake")
    print(f"Actual Real     {tn:8d}   {fp:9d}")
    print(f"Actual Fake     {fn:8d}   {tp:9d}")

    print("\n=== CHECKPOINT ===")
    print("Epoch:", checkpoint.get("epoch"))
    print("Validation loss:", checkpoint.get("val_loss"))
    print("Validation accuracy:", checkpoint.get("val_accuracy"))


if __name__ == "__main__":
    main()
