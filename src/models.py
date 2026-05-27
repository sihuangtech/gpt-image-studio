"""Model configuration loading."""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any


MODEL_CONFIG_PATH = Path(__file__).resolve().parent.parent / "models.json"


@dataclass(frozen=True)
class ImageModel:
    """A selectable OpenAI image model."""

    id: str
    label: str
    description: str = ""


@dataclass(frozen=True)
class ModelConfig:
    """Image model choices and project default."""

    default: str
    models: tuple[ImageModel, ...]

    @property
    def ids(self) -> tuple[str, ...]:
        return tuple(model.id for model in self.models)


@lru_cache
def load_model_config() -> ModelConfig:
    """Load image model choices from the project JSON config."""

    data = json.loads(MODEL_CONFIG_PATH.read_text(encoding="utf-8"))
    models = tuple(_parse_model(item) for item in data.get("models", []))
    if not models:
        raise ValueError(f"No image models configured in {MODEL_CONFIG_PATH}.")

    default = str(data.get("default") or models[0].id)
    ids = {model.id for model in models}
    if default not in ids:
        raise ValueError(f"Default image model {default!r} is not listed in {MODEL_CONFIG_PATH}.")

    return ModelConfig(default=default, models=models)


def _parse_model(item: Any) -> ImageModel:
    if not isinstance(item, dict):
        raise ValueError(f"Invalid image model entry in {MODEL_CONFIG_PATH}: {item!r}")

    model_id = str(item.get("id") or "").strip()
    if not model_id:
        raise ValueError(f"Image model entry is missing an id in {MODEL_CONFIG_PATH}.")

    return ImageModel(
        id=model_id,
        label=str(item.get("label") or model_id),
        description=str(item.get("description") or ""),
    )
