"""PySide6 desktop GUI entry.

界面层只负责收集输入、展示状态和预览图片；真正的 OpenAI 调用统一放在
generator.py，避免 CLI、GUI、Web 三套入口各自维护一份生图逻辑。
"""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QObject, QRunnable, Qt, QThreadPool, Signal, Slot
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .generator import SUPPORTED_MODELS, SUPPORTED_QUALITIES, SUPPORTED_SIZES, build_request, generate_images


class WorkerSignals(QObject):
    """后台线程和主界面之间的信号通道。"""

    finished = Signal(list)
    failed = Signal(str)


class GenerateWorker(QRunnable):
    """在后台线程执行生图，避免窗口卡死。"""

    def __init__(self, params: dict[str, object]) -> None:
        super().__init__()
        self.params = params
        self.signals = WorkerSignals()

    @Slot()
    def run(self) -> None:
        try:
            request = build_request(**self.params)
            images = generate_images(request)
            self.signals.finished.emit(images)
        except Exception as exc:  # noqa: BLE001 - GUI 需要把错误展示给用户
            self.signals.failed.emit(str(exc))


class ImageGeneratorWindow(QMainWindow):
    """PySide6 桌面端主窗口。"""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("GPT Image Studio")
        self.resize(1040, 720)
        self.thread_pool = QThreadPool.globalInstance()

        self.prompt_input = QTextEdit()
        self.prompt_input.setPlaceholderText("Describe the image you want to create...")
        self.prompt_input.setMinimumHeight(140)

        self.model_select = QComboBox()
        self.model_select.addItems(SUPPORTED_MODELS)

        self.size_select = QComboBox()
        self.size_select.addItems(SUPPORTED_SIZES)
        self.size_select.setCurrentText("1024x1024")

        self.quality_select = QComboBox()
        self.quality_select.addItems(SUPPORTED_QUALITIES)
        self.quality_select.setCurrentText("high")

        self.count_input = QSpinBox()
        self.count_input.setRange(1, 10)
        self.count_input.setValue(1)

        self.output_dir_input = QLineEdit("outputs")
        self.generate_button = QPushButton("Generate")
        self.status_label = QLabel("Ready")
        self.preview_label = QLabel("Generated images will appear here.")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumSize(520, 420)

        self._build_layout()
        self._apply_style()

    def _build_layout(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)

        root = QHBoxLayout(central)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(18)

        form_card = QFrame()
        form_card.setObjectName("card")
        form_card.setFixedWidth(390)
        form_layout = QVBoxLayout(form_card)
        form_layout.setContentsMargins(20, 20, 20, 20)
        form_layout.setSpacing(14)

        title = QLabel("GPT Image Studio")
        title.setObjectName("title")
        subtitle = QLabel("Generate images from prompts with OpenAI GPT Image models.")
        subtitle.setObjectName("subtitle")
        subtitle.setWordWrap(True)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignLeft)
        form.addRow("Prompt", self.prompt_input)
        form.addRow("Model", self.model_select)
        form.addRow("Size", self.size_select)
        form.addRow("Quality", self.quality_select)
        form.addRow("Count", self.count_input)

        output_row = QHBoxLayout()
        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self._choose_output_dir)
        output_row.addWidget(self.output_dir_input, 1)
        output_row.addWidget(browse_button)
        form.addRow("Output", output_row)

        self.generate_button.clicked.connect(self._start_generate)
        form_layout.addWidget(title)
        form_layout.addWidget(subtitle)
        form_layout.addLayout(form)
        form_layout.addWidget(self.generate_button)
        form_layout.addWidget(self.status_label)
        form_layout.addStretch()

        preview_card = QFrame()
        preview_card.setObjectName("previewCard")
        preview_layout = QVBoxLayout(preview_card)
        preview_layout.setContentsMargins(20, 20, 20, 20)
        preview_layout.addWidget(self.preview_label, 1)

        root.addWidget(form_card)
        root.addWidget(preview_card, 1)

    def _apply_style(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow { background: #eef2ef; }
            QFrame#card, QFrame#previewCard {
                background: #ffffff;
                border: 1px solid #d8ded7;
                border-radius: 8px;
            }
            QLabel#title {
                color: #17201c;
                font-size: 24px;
                font-weight: 700;
            }
            QLabel#subtitle, QLabel {
                color: #5c665f;
                font-size: 13px;
            }
            QTextEdit, QLineEdit, QComboBox, QSpinBox {
                background: #fbfcfa;
                border: 1px solid #cad3cc;
                border-radius: 6px;
                padding: 8px;
                color: #17201c;
            }
            QPushButton {
                background: #166b5f;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 10px 14px;
                font-weight: 700;
            }
            QPushButton:disabled {
                background: #9aa8a1;
            }
            QLabel[frameShape="4"] {
                border: 1px solid #d8ded7;
            }
            """
        )

    def _choose_output_dir(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Choose output directory", self.output_dir_input.text())
        if directory:
            self.output_dir_input.setText(directory)

    def _start_generate(self) -> None:
        prompt = self.prompt_input.toPlainText().strip()
        if not prompt:
            QMessageBox.warning(self, "Missing prompt", "Please enter a prompt first.")
            return

        self.generate_button.setEnabled(False)
        self.status_label.setText("Generating...")

        params = {
            "prompt": prompt,
            "model": self.model_select.currentText(),
            "size": self.size_select.currentText(),
            "quality": self.quality_select.currentText(),
            "count": self.count_input.value(),
            "output_dir": self.output_dir_input.text(),
        }
        worker = GenerateWorker(params)
        worker.signals.finished.connect(self._handle_success)
        worker.signals.failed.connect(self._handle_error)
        self.thread_pool.start(worker)

    def _handle_success(self, images: list[object]) -> None:
        self.generate_button.setEnabled(True)
        first_path = images[0].path
        self._show_preview(first_path)
        self.status_label.setText(f"Saved {len(images)} image(s). Latest: {first_path}")

    def _handle_error(self, message: str) -> None:
        self.generate_button.setEnabled(True)
        self.status_label.setText("Generation failed.")
        QMessageBox.critical(self, "Generation failed", message)

    def _show_preview(self, path: Path) -> None:
        pixmap = QPixmap(str(path))
        scaled = pixmap.scaled(self.preview_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.preview_label.setPixmap(scaled)


def main() -> None:
    app = QApplication(sys.argv)
    window = ImageGeneratorWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
