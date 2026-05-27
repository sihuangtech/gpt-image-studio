"""命令行入口。"""

from __future__ import annotations

import argparse

from .generator import (
    SUPPORTED_FORMATS,
    SUPPORTED_MODELS,
    SUPPORTED_QUALITIES,
    SUPPORTED_SIZES,
    build_request,
    generate_images,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="使用 OpenAI GPT Image 系列模型生成图片。")
    parser.add_argument("prompt", help="生图提示词，例如：一只在月球喝咖啡的猫")
    parser.add_argument("--model", choices=SUPPORTED_MODELS, default=None, help="生图模型")
    parser.add_argument("--size", choices=SUPPORTED_SIZES, default="1024x1024", help="图片尺寸")
    parser.add_argument("--quality", choices=SUPPORTED_QUALITIES, default="high", help="图片质量")
    parser.add_argument("--format", choices=SUPPORTED_FORMATS, default="png", help="输出格式")
    parser.add_argument("--background", default="auto", help="背景模式，例如 auto、transparent")
    parser.add_argument("--count", type=int, default=1, help="生成数量，1-10")
    parser.add_argument("--output-dir", default=None, help="输出目录，默认 outputs")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    request = build_request(
        prompt=args.prompt,
        model=args.model,
        size=args.size,
        quality=args.quality,
        count=args.count,
        output_format=args.format,
        background=args.background,
        output_dir=args.output_dir,
    )

    print("正在生成图片，请稍候...")
    images = generate_images(request)
    for image in images:
        print(f"已保存：{image.path}")


if __name__ == "__main__":
    main()
