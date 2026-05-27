"""项目配置读取。

这里集中处理环境变量，避免 CLI、GUI、Web 三个入口各自读取配置。
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from .models import load_model_config


load_dotenv()


@dataclass(frozen=True)
class AppConfig:
    """应用运行所需的基础配置。"""

    api_key: str | None
    default_model: str
    output_dir: Path


def get_config() -> AppConfig:
    """从环境变量生成配置对象。"""

    model_config = load_model_config()
    return AppConfig(
        api_key=os.getenv("OPENAI_API_KEY"),
        default_model=os.getenv("OPENAI_IMAGE_MODEL", model_config.default),
        output_dir=Path(os.getenv("IMAGE_OUTPUT_DIR", "outputs")),
    )
