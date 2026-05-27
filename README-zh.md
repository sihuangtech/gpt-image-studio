# GPT 系列生图客户端

这是一个基于 OpenAI GPT Image 系列模型的 Python 生图客户端，提供三种入口：

- CLI：适合终端使用和脚本批处理
- PySide6 桌面 GUI：适合本地可视化工作流
- NiceGUI Web 应用：适合在浏览器里使用更现代的界面

三种入口共用 `src/generator.py` 中的生图逻辑，避免重复维护 OpenAI Image API 调用。
可选模型统一配置在 `models.json`。

## 支持的模型

根据当前 OpenAI 图像生成文档，Image API 支持这些 GPT Image 模型：

- `gpt-image-2`：最新的 state-of-the-art GPT Image 模型
- `gpt-image-1.5`：上一代高质量 GPT Image 模型
- `gpt-image-1`：上一代 GPT Image 模型
- `gpt-image-1-mini`：更低成本的 GPT Image 模型

`chatgpt-image-latest` 会出现在 OpenAI 模型列表里，但这个客户端调用的是 `client.images.generate()`，所以可选模型只保留 Image API 的 GPT Image 模型。

Image API 文档里也提到旧的 DALL·E 模型。`dall-e-2` 和 `dall-e-3` 已被弃用，并且 API 支持已于 2026-05-12 结束，所以这个客户端默认聚焦 GPT Image 系列。

如果要新增、删除、排序模型，或者修改默认模型，编辑 `models.json` 即可。CLI 的参数校验、桌面 GUI 和 Web 页面的模型下拉列表都会读取这个文件。

## 安装

```bash
uv sync
cp .env.example .env
```

然后编辑 `.env`：

```bash
OPENAI_API_KEY=sk-your-api-key
```

可选配置：

```bash
OPENAI_IMAGE_MODEL=gpt-image-2
IMAGE_OUTPUT_DIR=outputs
```

`OPENAI_IMAGE_MODEL` 会覆盖 `models.json` 里的默认模型。

## CLI 使用

```bash
uv run python -m src.cli "一只戴着宇航头盔的橘猫，电影海报风格"
```

带参数示例：

```bash
uv run python -m src.cli \
  "未来城市的清晨，赛博朋克但温暖" \
  --model gpt-image-2 \
  --size 1024x1024 \
  --quality high \
  --output-dir outputs \
  --count 1
```

使用 `--model` 可以选择 `models.json` 中配置的任意模型。

## 桌面 GUI

```bash
uv run python -m src.gui
```

## Web 网页

```bash
uv run python -m src.web_app
```

打开浏览器访问：

```text
http://127.0.0.1:5000
```

如果 5000 端口被占用，可以换一个端口：

```bash
WEB_PORT=5001 uv run python -m src.web_app
```

## 目录结构

```text
src/
  config.py      # 读取环境变量和默认配置
  generator.py   # OpenAI Image API 核心封装
  models.py      # models.json 加载器
  cli.py         # 命令行入口
  gui.py         # PySide6 桌面 GUI
  web_app.py     # NiceGUI Web 应用
models.json      # 可选生图模型和默认模型
outputs/         # 默认图片输出目录，运行时自动创建
```

## 注意

- GPT Image 系列模型可能需要完成 OpenAI 组织验证。
- 复杂提示词生成时间可能更长。
- 默认输出 PNG 文件到 `outputs/` 目录。
- 依赖由 `uv` 通过 `pyproject.toml` 和 `uv.lock` 管理。
