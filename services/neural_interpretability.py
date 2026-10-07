from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import torch
import torch.nn as nn
from matplotlib.figure import Figure

ROOT = Path(__file__).resolve().parent.parent
CHECKPOINT_PATH = ROOT / "models" / "emnist_sae.pt"
BANK_PATH = ROOT / "models" / "emnist_latent_bank.npz"

EMNIST_BALANCED_CHARS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabdefghnqrt"


@dataclass(frozen=True)
class SAEConfig:
    input_dim: int = 28 * 28
    hidden_dim: int = 1024
    latent_dim: int = 24
    sparsity_lambda: float = 3e-4


class SparseAutoencoder(nn.Module):
    """L1 sparse autoencoder. Penalty is mean(|z|) with lambda 3e-4."""

    def __init__(self, config: SAEConfig | None = None) -> None:
        super().__init__()
        self.config = config or SAEConfig()
        c = self.config
        self.encoder = nn.Sequential(
            nn.Linear(c.input_dim, c.hidden_dim),
            nn.ReLU(),
            nn.Linear(c.hidden_dim, c.latent_dim),
            nn.ReLU(),
        )
        self.decoder = nn.Sequential(
            nn.Linear(c.latent_dim, c.hidden_dim),
            nn.ReLU(),
            nn.Linear(c.hidden_dim, c.input_dim),
            nn.Sigmoid(),
        )

    def encode(self, x: torch.Tensor) -> torch.Tensor:
        return self.encoder(x)

    def decode(self, z: torch.Tensor) -> torch.Tensor:
        return self.decoder(z)

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        z = self.encode(x)
        return self.decode(z), z


@dataclass(frozen=True)
class LatentBank:
    latents: np.ndarray
    images: np.ndarray
    labels: np.ndarray


def label_to_char(label: int) -> str:
    return EMNIST_BALANCED_CHARS[int(label)]


def load_model(path: Path | None = None) -> SparseAutoencoder:
    path = path or CHECKPOINT_PATH
    if not path.is_file():
        raise FileNotFoundError(path)
    try:
        payload = torch.load(path, map_location="cpu", weights_only=False)
    except TypeError:
        payload = torch.load(path, map_location="cpu")
    raw = payload.get("config") or {}
    if isinstance(raw, dict):
        config = SAEConfig(
            input_dim=int(raw.get("input_dim", 28 * 28)),
            hidden_dim=int(raw.get("hidden_dim", 1024)),
            latent_dim=int(raw.get("latent_dim", 24)),
            sparsity_lambda=float(raw.get("sparsity_lambda", 3e-4)),
        )
    else:
        config = SAEConfig(
            input_dim=int(getattr(raw, "input_dim", 28 * 28)),
            hidden_dim=int(getattr(raw, "hidden_dim", 1024)),
            latent_dim=int(getattr(raw, "latent_dim", 24)),
            sparsity_lambda=float(getattr(raw, "sparsity_lambda", 3e-4)),
        )
    model = SparseAutoencoder(config)
    model.load_state_dict(payload["state_dict"])
    model.eval()
    return model


def load_bank(path: Path | None = None) -> LatentBank:
    path = path or BANK_PATH
    if not path.is_file():
        raise FileNotFoundError(path)
    payload = np.load(path)
    return LatentBank(
        latents=np.asarray(payload["latents"], dtype=np.float32),
        images=np.asarray(payload["images"], dtype=np.float32),
        labels=np.asarray(payload["labels"], dtype=np.int64),
    )


def top_firing_examples(
    bank: LatentBank,
    neuron_idx: int,
    *,
    top_k: int = 8,
) -> list[tuple[np.ndarray, str, float]]:
    activations = bank.latents[:, neuron_idx]
    top_idx = np.argsort(activations)[::-1][:top_k]
    results: list[tuple[np.ndarray, str, float]] = []
    for idx in top_idx:
        results.append(
            (
                bank.images[idx],
                label_to_char(int(bank.labels[idx])),
                float(activations[idx]),
            )
        )
    return results


def tensor_to_image(tensor: torch.Tensor) -> np.ndarray:
    return tensor.detach().cpu().numpy().reshape(28, 28)


def plot_single_digit(digit: np.ndarray) -> Figure:
    fig, ax = plt.subplots(figsize=(2.2, 2.2))
    ax.imshow(digit, cmap="gray", vmin=0.0, vmax=1.0)
    ax.set_axis_off()
    ax.set_frame_on(False)
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
    return fig


def plot_latent_grid(activations: np.ndarray, *, grid_cols: int = 8) -> Figure:
    values = np.asarray(activations, dtype=np.float32).reshape(-1)
    values = np.where(values >= 0.05, values, 0.0)
    n_cells = values.size
    grid_rows = int(np.ceil(n_cells / grid_cols))
    padded = np.zeros(grid_rows * grid_cols, dtype=np.float32)
    padded[:n_cells] = values
    grid = padded.reshape(grid_rows, grid_cols)
    vmax = max(float(values.max()), 1.0)
    fig, ax = plt.subplots(figsize=(2.8, max(1.5, grid_rows * 0.26)))
    ax.imshow(grid, cmap="gray", vmin=0.0, vmax=vmax, aspect="equal")
    ax.set_xticks([])
    ax.set_yticks([])
    for row in range(grid_rows):
        for col in range(grid_cols):
            idx = row * grid_cols + col
            if idx < n_cells:
                ax.text(
                    col,
                    row,
                    str(idx),
                    ha="center",
                    va="center",
                    color="white" if grid[row, col] > 0.5 * vmax else "black",
                    fontsize=5,
                )
    fig.tight_layout()
    return fig


def plot_top_firing_examples(
    examples: list[tuple[np.ndarray, str, float]],
    *,
    neuron_idx: int,
    cols_per_row: int = 4,
) -> Figure:
    n = len(examples)
    title = f"Neuron {neuron_idx:02d}"
    if n == 0:
        fig, ax = plt.subplots(figsize=(4, 1))
        ax.axis("off")
        ax.set_title(title)
        return fig
    nrows = int(np.ceil(n / cols_per_row))
    fig, axes = plt.subplots(
        nrows, cols_per_row, figsize=(1.55 * cols_per_row, 1.75 * nrows)
    )
    axes = np.atleast_2d(axes)
    for plot_idx, (image, char, score) in enumerate(examples):
        row, col = divmod(plot_idx, cols_per_row)
        ax = axes[row, col]
        ax.imshow(image, cmap="gray", vmin=0.0, vmax=1.0)
        ax.set_title(f"'{char}'  ({score:.2f})", fontsize=9)
        ax.axis("off")
        for spine in ax.spines.values():
            spine.set_visible(True)
            spine.set_linewidth(1.0)
            spine.set_color("black")
    for plot_idx in range(n, nrows * cols_per_row):
        row, col = divmod(plot_idx, cols_per_row)
        axes[row, col].axis("off")
    fig.tight_layout(pad=0.7, h_pad=0.9, w_pad=0.8)
    return fig


def top_active_neurons(
    activations: np.ndarray,
    *,
    top_k: int = 10,
    min_activation: float = 0.05,
) -> list[tuple[int, float]]:
    values = np.asarray(activations, dtype=np.float32).reshape(-1)
    active = np.where(values >= min_activation)[0]
    if active.size == 0:
        return []
    ordered = active[np.argsort(values[active])[::-1]][:top_k]
    return [(int(i), float(values[i])) for i in ordered]


def format_top_neurons(rows: list[tuple[int, float]]) -> str:
    lines = [f"Neuron {idx:02d}: {value:.4f}" for idx, value in rows]
    return "\n".join(lines) if lines else "No active neurons."
