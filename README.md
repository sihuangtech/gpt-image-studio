# GPT Image Studio

A small Python client for OpenAI GPT Image models with three entry points:

- CLI for terminal use and scripting
- PySide6 desktop GUI for local visual workflows
- NiceGUI web app for a polished browser interface

The shared generation logic lives in `src/generator.py`, so all three surfaces use the same OpenAI Image API wrapper.
Selectable image models are configured in `models.json`.

## Supported Models

Based on the current OpenAI image generation docs, the Image API supports these GPT Image models:

- `gpt-image-2`: latest state-of-the-art GPT Image model
- `gpt-image-1.5`: previous high-quality GPT Image model
- `gpt-image-1`: previous GPT Image model
- `gpt-image-1-mini`: cost-efficient GPT Image model

`chatgpt-image-latest` appears in OpenAI model listings, but it is not included here because this client calls `client.images.generate()` and focuses on Image API GPT Image models.

The Image API docs also mention legacy DALL·E models. `dall-e-2` and `dall-e-3` are deprecated, and their API support ended on May 12, 2026, so this client defaults to GPT Image models.

To add, remove, reorder, or change the default model, edit `models.json`. CLI validation and the desktop/web model dropdowns all read from that file.

## Setup

```bash
uv sync
cp .env.example .env
```

Edit `.env` and set:

```bash
OPENAI_API_KEY=sk-your-api-key
```

Optional:

```bash
OPENAI_BASE_URL=https://your-proxy.example.com/v1
OPENAI_IMAGE_MODEL=gpt-image-2
IMAGE_OUTPUT_DIR=outputs
```

Leave `OPENAI_BASE_URL` unset when using the official OpenAI API. Set it only for OpenAI-compatible proxy providers or relay services, using the provider's API base URL.

`OPENAI_IMAGE_MODEL` overrides the default from `models.json`.

## CLI

```bash
uv run python -m src.cli "A cinematic poster of an orange cat wearing an astronaut helmet"
```

Example with options:

```bash
uv run python -m src.cli \
  "A warm cyberpunk city at sunrise, cinematic composition" \
  --model gpt-image-2 \
  --size 1024x1024 \
  --quality high \
  --output-dir outputs \
  --count 1
```

Use `--model` to choose any model listed in `models.json`.

## Desktop GUI

```bash
uv run python -m src.gui
```

## Web App

```bash
uv run python -m src.web_app
```

Open:

```text
http://127.0.0.1:5000
```

If port `5000` is already in use:

```bash
WEB_PORT=5001 uv run python -m src.web_app
```

## Project Structure

```text
src/
  config.py      # Environment and default configuration
  generator.py   # Shared OpenAI Image API wrapper
  models.py      # models.json loader
  cli.py         # CLI entry point
  gui.py         # PySide6 desktop GUI
  web_app.py     # NiceGUI web app
models.json      # Selectable image models and default model
outputs/         # Default image output directory, created at runtime
```

## Notes

- GPT Image models may require OpenAI organization verification.
- Complex prompts may take longer to generate.
- Generated files are saved as PNG by default under `outputs/`.
- Dependencies are managed by `uv` through `pyproject.toml` and `uv.lock`.
