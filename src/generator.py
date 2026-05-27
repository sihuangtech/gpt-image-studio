"""OpenAI GPT Image 生图核心封装。

CLI、GUI、Web 都调用本模块，保证三种入口的行为一致。
"""

from __future__ import annotations

import base64
import re
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from openai import OpenAI

from .config import get_config
from .models import load_model_config


SUPPORTED_MODELS = load_model_config().ids
SUPPORTED_SIZES = ("1024x1024", "1024x1536", "1536x1024", "auto")
SUPPORTED_QUALITIES = ("auto", "low", "medium", "high")
SUPPORTED_FORMATS = ("png", "jpeg", "webp")


@dataclass(frozen=True)
class ImageRequest:
    """一次生图请求的参数。"""

    prompt: str
    model: str = load_model_config().default
    size: str = "1024x1024"
    quality: str = "high"
    count: int = 1
    output_format: str = "png"
    background: str = "auto"
    output_dir: Path = Path("outputs")


@dataclass(frozen=True)
class GeneratedImage:
    """一次生成得到的本地文件信息。"""

    path: Path
    prompt: str
    model: str


def generate_images(request: ImageRequest, api_key: str | None = None) -> list[GeneratedImage]:
    """调用 OpenAI Image API 并将图片保存到本地。

    OpenAI SDK 返回可能包含 base64 图片数据，也可能包含临时 URL。
    这里两种情况都兼容处理。
    """

    if not request.prompt.strip():
        raise ValueError("提示词不能为空。")

    config = get_config()
    key = api_key or config.api_key
    if not key:
        raise RuntimeError("未设置 OPENAI_API_KEY。请先复制 .env.example 为 .env 并填写 API Key。")

    _validate_request(request)

    request.output_dir.mkdir(parents=True, exist_ok=True)
    client_options = {"api_key": key}
    if config.base_url:
        client_options["base_url"] = config.base_url
    client = OpenAI(**client_options)

    # GPT Image 系列模型支持 size、quality、output_format、background 等参数。
    response = client.images.generate(
        model=request.model,
        prompt=request.prompt,
        size=request.size,
        quality=request.quality,
        n=request.count,
        output_format=request.output_format,
        background=request.background,
    )

    images: list[GeneratedImage] = []
    for index, item in enumerate(response.data or [], start=1):
        suffix = request.output_format.lower()
        filename = _build_filename(request.prompt, index, suffix)
        path = request.output_dir / filename

        b64_json = getattr(item, "b64_json", None)
        url = getattr(item, "url", None)

        if b64_json:
            path.write_bytes(base64.b64decode(b64_json))
        elif url:
            _download_url(url, path)
        else:
            raise RuntimeError("OpenAI 返回中没有可保存的图片数据。")

        images.append(GeneratedImage(path=path, prompt=request.prompt, model=request.model))

    if not images:
        raise RuntimeError("OpenAI 没有返回图片。")

    return images


def build_request(
    prompt: str,
    model: str | None = None,
    size: str = "1024x1024",
    quality: str = "high",
    count: int = 1,
    output_format: str = "png",
    background: str = "auto",
    output_dir: str | Path | None = None,
) -> ImageRequest:
    """根据用户输入创建请求对象，并套用默认配置。"""

    config = get_config()
    return ImageRequest(
        prompt=prompt,
        model=model or config.default_model,
        size=size,
        quality=quality,
        count=count,
        output_format=output_format,
        background=background,
        output_dir=Path(output_dir) if output_dir else config.output_dir,
    )


def _validate_request(request: ImageRequest) -> None:
    """在请求 OpenAI 前做本地校验，让错误更早、更中文。"""

    _validate_choice("模型", request.model, SUPPORTED_MODELS)
    _validate_choice("尺寸", request.size, SUPPORTED_SIZES)
    _validate_choice("质量", request.quality, SUPPORTED_QUALITIES)
    _validate_choice("格式", request.output_format, SUPPORTED_FORMATS)

    if request.count < 1 or request.count > 10:
        raise ValueError("生成数量必须在 1 到 10 之间。")


def _validate_choice(label: str, value: str, choices: Iterable[str]) -> None:
    if value not in choices:
        allowed = "、".join(choices)
        raise ValueError(f"{label}不支持：{value}。可选值：{allowed}")


def _build_filename(prompt: str, index: int, suffix: str) -> str:
    """根据提示词生成较友好的文件名。"""

    slug = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff]+", "-", prompt.strip()).strip("-")
    slug = slug[:40] or "image"
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    return f"{timestamp}-{slug}-{index}.{suffix}"


def _download_url(url: str, path: Path) -> None:
    """保存 URL 形式的图片响应。"""

    with urllib.request.urlopen(url, timeout=120) as response:
        path.write_bytes(response.read())
