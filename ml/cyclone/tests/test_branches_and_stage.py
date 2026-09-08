"""Unit tests for EnvBranch (MLP), TrackBranch (GRU), StageHead, and non-image StageModel."""

import torch

from ml.cyclone.models.env_branch import EnvBranch
from ml.cyclone.models.heads import StageModel
from ml.cyclone.models.track_branch import TrackBranch


def test_env_branch_forward_shapes():
    """Asserts EnvBranch transforms 6-d atmospheric vector to 64-d embedding."""
    branch = EnvBranch(in_dim=6, hidden_dim=64, out_dim=64, dropout=0.1)
    dummy_env = torch.rand(4, 6, dtype=torch.float32)

    emb = branch(dummy_env)
    assert emb.shape == (4, 64)
    assert emb.dtype == torch.float32

    # Single-sample evaluation
    branch.eval()
    single_emb = branch(torch.rand(1, 6))
    assert single_emb.shape == (1, 64)


def test_track_branch_variable_length_and_length_one():
    """Asserts TrackBranch GRU handles 8-step history and minimal length-1 sequence."""
    branch = TrackBranch(input_dim=7, hidden_dim=128, num_layers=2, out_dim=128)

    # Multi-step sequence (B=3, N=8, F=7)
    multi_seq = torch.rand(3, 8, 7, dtype=torch.float32)
    multi_emb = branch(multi_seq)
    assert multi_emb.shape == (3, 128)

    # Length-1 sequence (B=2, N=1, F=7)
    len1_seq = torch.rand(2, 1, 7, dtype=torch.float32)
    len1_emb = branch(len1_seq)
    assert len1_emb.shape == (2, 128)

    # Packed sequence with explicit sequence lengths
    lengths = torch.tensor([8, 4, 1])
    packed_emb = branch(multi_seq, seq_lengths=lengths)
    assert packed_emb.shape == (3, 128)


def test_stage_head_and_stage_model_forward():
    """Asserts StageHead and StageModel output 6-class stage logits and probabilities."""
    model = StageModel(env_dim=6, env_out_dim=64, track_dim=7, track_hidden_dim=128, num_stages=6)

    dummy_env = torch.rand(4, 6, dtype=torch.float32)
    dummy_track = torch.rand(4, 8, 7, dtype=torch.float32)

    out = model(env_vector=dummy_env, track_sequence=dummy_track)

    assert "stage_logits" in out
    assert "stage_probs" in out
    assert "predicted_stage_idx" in out
    assert "embedding" in out

    assert out["stage_logits"].shape == (4, 6)
    assert out["stage_probs"].shape == (4, 6)
    assert out["predicted_stage_idx"].shape == (4,)
    assert out["embedding"].shape == (4, 192)  # 64 + 128 = 192-d


def test_stage_model_training_step():
    """Asserts backpropagation and loss reduction on StageModel."""
    model = StageModel(env_dim=6, env_out_dim=64, track_dim=7, track_hidden_dim=128, num_stages=6)
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)
    criterion = torch.nn.CrossEntropyLoss()

    dummy_env = torch.rand(4, 6, dtype=torch.float32)
    dummy_track = torch.rand(4, 8, 7, dtype=torch.float32)
    targets = torch.tensor([0, 2, 3, 1], dtype=torch.long)

    optimizer.zero_grad()
    out = model(env_vector=dummy_env, track_sequence=dummy_track)
    loss = criterion(out["stage_logits"], targets)
    loss.backward()
    optimizer.step()

    assert not torch.isnan(loss)
    assert loss.item() > 0.0
