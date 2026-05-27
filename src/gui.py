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
    QFrame,
    QGridLayout,
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
        self.resize(1120, 760)
        self.thread_pool = QThreadPool.globalInstance()

        self.prompt_input = QTextEdit()
        self.prompt_input.setPlaceholderText("Describe the image you want to create...")
        self.prompt_input.setMinimumHeight(190)

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
        self.browse_button = QPushButton("Browse")
        self.generate_button = QPushButton("Generate")
        self.status_label = QLabel("Ready")
        self.preview_label = QLabel("No image yet")
        self.preview_label.setObjectName("emptyPreview")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumSize(560, 500)
        self.preview_label.setWordWrap(True)

        self._build_layout()
        self._apply_style()

    def _build_layout(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)

        root = QHBoxLayout(central)
        root.setContentsMargins(22, 22, 22, 22)
        root.setSpacing(22)

        form_card = QFrame()
        form_card.setObjectName("card")
        form_card.setFixedWidth(430)
        form_layout = QVBoxLayout(form_card)
        form_layout.setContentsMargins(26, 26, 26, 26)
        form_layout.setSpacing(18)

        title = QLabel("GPT Image Studio")
        title.setObjectName("title")
        subtitle = QLabel("Prompt, tune, generate, and preview local image files.")
        subtitle.setObjectName("subtitle")
        subtitle.setWordWrap(True)

        options_grid = QGridLayout()
        options_grid.setHorizontalSpacing(12)
        options_grid.setVerticalSpacing(14)
        options_grid.addLayout(self._field("Model", self.model_select), 0, 0)
        options_grid.addLayout(self._field("Size", self.size_select), 0, 1)
        options_grid.addLayout(self._field("Quality", self.quality_select), 1, 0)
        options_grid.addLayout(self._field("Count", self.count_input), 1, 1)

        output_row = QHBoxLayout()
        output_row.setSpacing(10)
        self.browse_button.setObjectName("secondaryButton")
        self.browse_button.clicked.connect(self._choose_output_dir)
        output_row.addWidget(self.output_dir_input, 1)
        output_row.addWidget(self.browse_button)

        self.generate_button.clicked.connect(self._start_generate)
        self.generate_button.setObjectName("primaryButton")
        form_layout.addWidget(title)
        form_layout.addWidget(subtitle)
        form_layout.addSpacing(4)
        form_layout.addLayout(self._field("Prompt", self.prompt_input))
        form_layout.addLayout(options_grid)
        form_layout.addLayout(self._field("Output folder", output_row))
        form_layout.addSpacing(2)
        form_layout.addWidget(self.generate_button)
        form_layout.addWidget(self.status_label)
        form_layout.addStretch()

        preview_card = QFrame()
        preview_card.setObjectName("previewCard")
        preview_layout = QVBoxLayout(preview_card)
        preview_layout.setContentsMargins(24, 24, 24, 24)
        preview_layout.setSpacing(16)
        preview_header = QLabel("Preview")
        preview_header.setObjectName("sectionTitle")
        preview_hint = QLabel("Generated images are saved locally and shown here.")
        preview_hint.setObjectName("hint")
        preview_hint.setWordWrap(True)
        preview_layout.addWidget(preview_header)
        preview_layout.addWidget(preview_hint)
        preview_layout.addWidget(self.preview_label, 1)

        root.addWidget(form_card)
        root.addWidget(preview_card, 1)

    def _field(self, label_text: str, widget_or_layout: QWidget | QHBoxLayout) -> QVBoxLayout:
        layout = QVBoxLayout()
        layout.setSpacing(7)
        label = QLabel(label_text)
        label.setObjectName("fieldLabel")
        layout.addWidget(label)
        if isinstance(widget_or_layout, QWidget):
            layout.addWidget(widget_or_layout)
        else:
            layout.addLayout(widget_or_layout)
        return layout

    def _apply_style(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow { background: #f3f4f1; }
            QFrame#card, QFrame#previewCard {
                background: #ffffff;
                border: 1px solid #dfe4df;
                border-radius: 8px;
            }
            QLabel#title {
                color: #111815;
                font-size: 28px;
                font-weight: 700;
            }
            QLabel#subtitle {
                color: #68746d;
                font-size: 14px;
                line-height: 20px;
            }
            QLabel#sectionTitle {
                color: #111815;
                font-size: 18px;
                font-weight: 700;
            }
            QLabel#hint, QLabel#emptyPreview, QLabel {
                color: #68746d;
                font-size: 13px;
            }
            QLabel#fieldLabel {
                color: #35413b;
                font-size: 12px;
                font-weight: 700;
            }
            QTextEdit, QLineEdit, QComboBox, QSpinBox {
                background: #fbfcfb;
                border: 1px solid #cfd8d1;
                border-radius: 6px;
                color: #111815;
                font-size: 14px;
                min-height: 36px;
                padding: 8px 10px;
                selection-background-color: #0f766e;
            }
            QTextEdit {
                line-height: 20px;
            }
            QTextEdit:focus, QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
                border: 1px solid #0f766e;
                background: #ffffff;
            }
            QPushButton#primaryButton {
                background: #0f766e;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                min-height: 42px;
                padding: 10px 14px;
                font-size: 14px;
                font-weight: 700;
            }
            QPushButton#primaryButton:hover {
                background: #0b625c;
            }
            QPushButton#primaryButton:disabled {
                background: #9ca9a2;
            }
            QPushButton#secondaryButton {
                background: #eef3f0;
                color: #0f4f49;
                border: 1px solid #cfd8d1;
                border-radius: 6px;
                min-height: 36px;
                padding: 8px 14px;
                font-weight: 700;
            }
            QPushButton#secondaryButton:hover {
                background: #e3ebe7;
            }
            QLabel#emptyPreview {
                background: #f8faf8;
                border: 1px dashed #cbd6cf;
                border-radius: 8px;
                font-size: 15px;
            }
            QComboBox::drop-down {
                border: none;
                width: 28px;
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
