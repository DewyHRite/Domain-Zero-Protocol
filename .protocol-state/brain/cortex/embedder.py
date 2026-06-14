"""Embedding adapter for Cortex."""

from __future__ import annotations

import hashlib
import math
from pathlib import Path
from typing import Iterable

from .errors import DependencyError


class Embedder:
    def __init__(self, model: str, *, cache_dir: str | Path | None = None, stub: bool = False, dim: int = 384):
        self.model = model
        self.stub = stub or model.upper() == "STUB"
        self.dim = dim
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self._model = None

        if not self.stub:
            try:
                from fastembed import TextEmbedding
            except Exception as exc:  # pragma: no cover - depends on optional package
                raise DependencyError("fastembed is not installed; use model: STUB for tests or install requirements-brain.txt") from exc
            kwargs = {"model_name": model}
            if self.cache_dir:
                self.cache_dir.mkdir(parents=True, exist_ok=True)
                kwargs["cache_dir"] = str(self.cache_dir)
            self._model = TextEmbedding(**kwargs)

    def embed(self, text: str) -> list[float]:
        if self.stub:
            return _stub_vector(text, self.dim)
        assert self._model is not None
        vector = next(iter(self._model.embed([text])))
        return [float(x) for x in vector]

    def embed_many(self, texts: Iterable[str]) -> list[list[float]]:
        items = list(texts)
        if self.stub:
            return [self.embed(text) for text in items]
        assert self._model is not None
        return [[float(x) for x in vector] for vector in self._model.embed(items)]


def _stub_vector(text: str, dim: int) -> list[float]:
    seed = hashlib.sha256(text.encode("utf-8")).digest()
    values: list[float] = []
    counter = 0
    while len(values) < dim:
        block = hashlib.sha256(seed + counter.to_bytes(4, "big")).digest()
        values.extend(((byte / 255.0) * 2.0) - 1.0 for byte in block)
        counter += 1
    vector = values[:dim]
    norm = math.sqrt(sum(x * x for x in vector)) or 1.0
    return [x / norm for x in vector]
