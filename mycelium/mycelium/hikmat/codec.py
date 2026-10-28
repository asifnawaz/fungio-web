"""CODON codec: compress a latent vector to 2-bit symbols (4 per byte).

A fixed random rotation spreads information evenly across dimensions, then each
dimension is quantized to one of 4 levels at the quartiles of a standard normal.
A 64-dim float32 vector (256 bytes) becomes 16 bytes. The rotation is derived from the
model version, so codes from a different model version are deliberately incompatible.
"""

from __future__ import annotations

import numpy as np

from mycelium.evals.datasets import stable_seed

_THRESHOLDS = np.array([-0.6745, 0.0, 0.6745])
# Mean of a standard normal within each quartile bin.
_CENTROIDS = np.array([-1.2711, -0.3177, 0.3177, 1.2711])


class CodonCodec:
    def __init__(self, dim: int, version: str):
        if dim % 4:
            raise ValueError("dim must be a multiple of 4")
        self.dim = dim
        self.version = version
        gaussian = np.random.default_rng(stable_seed("codon", version, dim)).normal(size=(dim, dim))
        self._rotation, _ = np.linalg.qr(gaussian)

    @property
    def nbytes(self) -> int:
        return self.dim // 4

    def encode(self, vector: np.ndarray) -> bytes:
        v = np.asarray(vector, dtype=float)
        z = self._rotation @ (v / np.linalg.norm(v)) * np.sqrt(self.dim)
        symbols = np.digitize(z, _THRESHOLDS).astype(np.uint8).reshape(-1, 4)
        packed = symbols[:, 0] | symbols[:, 1] << 2 | symbols[:, 2] << 4 | symbols[:, 3] << 6
        return packed.astype(np.uint8).tobytes()

    def decode(self, codes: bytes) -> np.ndarray:
        packed = np.frombuffer(codes, dtype=np.uint8)
        symbols = np.stack([(packed >> shift) & 0b11 for shift in (0, 2, 4, 6)], axis=1).reshape(-1)
        v = self._rotation.T @ _CENTROIDS[symbols]
        return v / np.linalg.norm(v)
