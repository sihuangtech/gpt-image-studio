"""NiceGUI web entry.

NiceGUI 比传统模板更适合快速做一个漂亮的 Python Web 工具界面。
这里仍然复用 generator.py 中的核心生图逻辑。
"""

from __future__ import annotations

import base64
import mimetypes
import os
from pathlib import Path

from nicegui import run, ui

from .generator import SUPPORTED_MODELS, SUPPORTED_QUALITIES, SUPPORTED_SIZES, build_request, generate_images


def image_to_data_url(path: Path) -> str:
    """把生成后的本地图片转为浏览器可直接预览的 data URL。"""

    mime_type = mimetypes.guess_type(path.name)[0] or "image/png"
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{data}"


@ui.page("/")
def index() -> None:
    ui.colors(primary="#166b5f", secondary="#d97706", accent="#2563eb")
    ui.add_head_html(
        """
        <style>
          body {
            background:
              linear-gradient(135deg, rgba(22,107,95,.10), transparent 34%),
              linear-gradient(315deg, rgba(217,119,6,.12), transparent 30%),
              #eef2ef;
          }
          .glass {
            background: rgba(255, 255, 255, .86);
            border: 1px solid rgba(113, 128, 120, .22);
            box-shadow: 0 18px 55px rgba(23, 32, 28, .10);
            backdrop-filter: blur(14px);
          }
          .result-tile img {
            width: 100%;
            aspect-ratio: 1;
            object-fit: cover;
            border-radius: 8px;
          }
        </style>
        """
    )

    with ui.column().classes("w-full min-h-screen px-5 py-6 items-center"):
        with ui.row().classes("w-full max-w-7xl gap-5 items-stretch"):
            with ui.card().classes("glass w-full md:w-[430px] rounded-lg p-5"):
                ui.label("GPT Image Studio").classes("text-3xl font-bold text-[#17201c]")
                ui.label("Create image files with OpenAI GPT Image models from CLI, desktop, or browser.").classes(
                    "text-[#5c665f] leading-6"
                )

                prompt = ui.textarea("Prompt", placeholder="A cinematic poster of a warm cyberpunk morning...").classes(
                    "w-full"
                )
                model = ui.select(SUPPORTED_MODELS, value=SUPPORTED_MODELS[0], label="Model").classes("w-full")
                with ui.row().classes("w-full gap-3"):
                    size = ui.select(SUPPORTED_SIZES, value="1024x1024", label="Size").classes("flex-1")
                    quality = ui.select(SUPPORTED_QUALITIES, value="high", label="Quality").classes("flex-1")
                with ui.row().classes("w-full gap-3"):
                    count = ui.number("Count", value=1, min=1, max=10, step=1).classes("flex-1")
                    output_dir = ui.input("Output directory", value="outputs").classes("flex-[2]")

                status = ui.label("Ready").classes("text-sm text-[#5c665f]")

                async def submit() -> None:
                    if not prompt.value or not prompt.value.strip():
                        ui.notify("Please enter a prompt first.", type="warning")
                        return

                    generate_button.disable()
                    status.text = "Generating..."
                    results.clear()

                    try:
                        image_request = build_request(
                            prompt=prompt.value,
                            model=model.value,
                            size=size.value,
                            quality=quality.value,
                            count=int(count.value or 1),
                            output_dir=output_dir.value or "outputs",
                        )
                        images = await run.io_bound(generate_images, image_request)
                    except Exception as exc:  # noqa: BLE001 - Web 页面需要展示可读错误
                        status.text = "Generation failed."
                        ui.notify(str(exc), type="negative", multi_line=True)
                    else:
                        status.text = f"Saved {len(images)} image(s)."
                        with results:
                            for image in images:
                                with ui.card().classes("result-tile w-full sm:w-[260px] rounded-lg p-3"):
                                    ui.image(image_to_data_url(image.path)).classes("rounded-lg")
                                    ui.label(image.path.name).classes("text-xs text-[#5c665f] break-all")
                    finally:
                        generate_button.enable()

                generate_button = ui.button("Generate", on_click=submit).classes("w-full h-12 text-base font-bold")
                ui.label("Tip: GPT Image requests can take up to a couple of minutes for complex prompts.").classes(
                    "text-xs text-[#6b756f]"
                )

            with ui.card().classes("glass flex-1 rounded-lg p-5"):
                ui.label("Results").classes("text-2xl font-bold text-[#17201c]")
                ui.label("Generated images are saved locally and previewed here.").classes("text-[#5c665f]")
                results = ui.row().classes("w-full gap-4")
                with results:
                    with ui.column().classes("w-full h-[420px] items-center justify-center text-[#7a847e]"):
                        ui.icon("image", size="56px")
                        ui.label("Your generated images will appear here.")


def main() -> None:
    port = int(os.getenv("WEB_PORT", "5000"))
    ui.run(host="127.0.0.1", port=port, title="GPT Image Studio", reload=False)


if __name__ == "__main__":
    main()
