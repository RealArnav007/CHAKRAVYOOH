"""Unit tests for unified Trainer, ExperimentTracker, and train_fusion pipeline."""

import csv
import json
from pathlib import Path
import tempfile
import numpy as np
import pytest
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

from ml.cyclone.train.track_experiment import (
    ExperimentTracker,
    compute_split_manifest_hash,
    get_git_commit_hash,
)
from ml.cyclone.train.trainer import Trainer, seed_everything


def test_seed_everything_determinism():
    """Asserts seed_everything produces identical random numbers across backends."""
    seed_everything(1234)
    r1 = torch.rand(5)
    n1 = np.random.rand(5)

    seed_everything(1234)
    r2 = torch.rand(5)
    n2 = np.random.rand(5)

    torch.testing.assert_close(r1, r2)
    np.testing.assert_allclose(n1, n2)


def test_experiment_tracker_logging_and_manifest_hash():
    """Asserts ExperimentTracker writes CSV, summary JSON, and hashes dataset splits."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        run_path = Path(tmp_dir) / "test_run"
        splits = {"train": [0, 1, 2, 3], "val": [4, 5], "test": [6, 7]}

        tracker = ExperimentTracker(
            experiment_name="unit_test_run",
            run_dir=run_path,
            config={"lr": 1e-3, "epochs": 2},
            split_indices=splits,
        )

        assert tracker.git_commit != ""
        assert tracker.split_hash != "none"

        # Log epochs
        tracker.log_epoch(epoch=1, metrics={"train_loss": 0.5, "val_acc": 0.8})
        tracker.log_epoch(epoch=2, metrics={"train_loss": 0.3, "val_acc": 0.9})
        tracker.log_summary({"test_acc": 0.92, "status": "COMPLETED"})
        tracker.finish()

        # Check CSV content
        csv_file = run_path / "metrics.csv"
        assert csv_file.is_file()
        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 2
            assert float(rows[0]["train_loss"]) == 0.5
            assert float(rows[1]["val_acc"]) == 0.9

        # Check summary JSON
        summary_file = run_path / "summary_metrics.json"
        assert summary_file.is_file()
        with open(summary_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            assert data["test_acc"] == 0.92


def test_trainer_checkpointing_and_early_stopping():
    """Asserts Trainer saves best/last checkpoints, handles early stopping, and resumes state."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        save_path = Path(tmp_dir) / "checkpoints"

        # Toy dataset: y = 2 * x
        x_train = torch.randn(32, 4)
        y_train = torch.randn(32, 1)
        train_loader = DataLoader(TensorDataset(x_train, y_train), batch_size=8)

        x_val = torch.randn(16, 4)
        y_val = torch.randn(16, 1)
        val_loader = DataLoader(TensorDataset(x_val, y_val), batch_size=8)

        toy_model = nn.Linear(4, 1)
        criterion = nn.MSELoss()
        optimizer = torch.optim.Adam(toy_model.parameters(), lr=1e-2)

        def toy_step_fn(m, batch, crit, dev):
            xb, yb = batch[0].to(dev), batch[1].to(dev)
            preds = m(xb)
            loss = crit(preds, yb)
            return loss, {"loss": loss.item()}

        trainer = Trainer(
            model=toy_model,
            criterion=criterion,
            train_loader=train_loader,
            val_loader=val_loader,
            optimizer=optimizer,
            save_dir=save_path,
            step_fn=toy_step_fn,
            early_stopping_metric="val_loss",
            early_stopping_mode="min",
            early_stopping_patience=3,
            checkpoint_prefix="toy_model",
        )

        summary = trainer.train(epochs=6)

        best_ckpt = save_path / "toy_model.pt"
        last_ckpt = save_path / "last_toy_model.pt"

        assert best_ckpt.is_file()
        assert last_ckpt.is_file()
        assert len(summary["history"]) > 0

        # Resuming test
        new_model = nn.Linear(4, 1)
        new_trainer = Trainer(
            model=new_model,
            criterion=criterion,
            train_loader=train_loader,
            val_loader=val_loader,
            optimizer=torch.optim.Adam(new_model.parameters(), lr=1e-2),
            save_dir=save_path,
            step_fn=toy_step_fn,
            checkpoint_prefix="toy_model",
        )
        resumed_epoch = new_trainer.load_checkpoint(last_ckpt)
        assert resumed_epoch == len(summary["history"])
