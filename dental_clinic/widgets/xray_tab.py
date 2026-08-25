from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt, QDate, QSize
from PyQt6.QtGui import QIcon, QPixmap, QDesktopServices
from PyQt6.QtCore import QUrl
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QFileDialog, QLineEdit, QDateEdit, QMessageBox,
    QFormLayout, QSplitter,
)

from ..database import Database


class XrayTab(QWidget):
    """Attach and browse X-ray images for the current patient."""

    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.patient_id: int | None = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        self.header = QLabel("<b>No patient selected</b>")
        layout.addWidget(self.header)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        self.list_widget = QListWidget()
        self.list_widget.setIconSize(QSize(96, 96))
        self.list_widget.currentItemChanged.connect(self._on_select)
        splitter.addWidget(self.list_widget)

        preview_box = QVBoxLayout()
        preview_widget = QWidget()
        preview_widget.setLayout(preview_box)
        self.preview_label = QLabel("No X-ray selected")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setMinimumSize(300, 300)
        self.preview_label.setScaledContents(False)
        preview_box.addWidget(self.preview_label, 1)
        self.open_btn = QPushButton("Open in Viewer")
        self.open_btn.clicked.connect(self.open_selected)
        preview_box.addWidget(self.open_btn)
        splitter.addWidget(preview_widget)
        splitter.setSizes([260, 400])

        layout.addWidget(splitter, 1)

        form = QFormLayout()
        self.note_edit = QLineEdit()
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        form.addRow("Date taken:", self.date_edit)
        form.addRow("Note:", self.note_edit)
        layout.addLayout(form)

        buttons = QHBoxLayout()
        self.add_btn = QPushButton("Attach X-Ray Image...")
        self.remove_btn = QPushButton("Remove Selected")
        self.add_btn.clicked.connect(self.attach_image)
        self.remove_btn.clicked.connect(self.remove_selected)
        buttons.addWidget(self.add_btn)
        buttons.addWidget(self.remove_btn)
        buttons.addStretch()
        layout.addLayout(buttons)

        self.set_patient(None)

    def set_patient(self, patient_row):
        self.patient_id = patient_row["id"] if patient_row else None
        enabled = self.patient_id is not None
        for w in (self.list_widget, self.add_btn, self.remove_btn,
                  self.note_edit, self.date_edit, self.open_btn):
            w.setEnabled(enabled)
        if patient_row:
            self.header.setText(
                f"<b>X-Rays for {patient_row['name']} "
                f"({patient_row['reg_no']})</b>")
            self.refresh()
        else:
            self.header.setText("<b>Select a patient in the Patients tab</b>")
            self.list_widget.clear()
            self.preview_label.setText("No X-ray selected")
            self.preview_label.setPixmap(QPixmap())

    def refresh(self):
        if self.patient_id is None:
            return
        self.list_widget.clear()
        for row in self.db.get_xrays(self.patient_id):
            label = row["taken_on"]
            if row["note"]:
                label += f" — {row['note']}"
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, row["id"])
            abs_path = self.db.xray_abs_path(row)
            if abs_path.exists():
                pix = QPixmap(str(abs_path))
                if not pix.isNull():
                    item.setIcon(QIcon(pix.scaled(
                        96, 96, Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation)))
            self.list_widget.addItem(item)
        self.preview_label.setText("No X-ray selected")
        self.preview_label.setPixmap(QPixmap())

    def _current_xray_row(self):
        item = self.list_widget.currentItem()
        if not item:
            return None
        xray_id = item.data(Qt.ItemDataRole.UserRole)
        return next((r for r in self.db.get_xrays(self.patient_id)
                     if r["id"] == xray_id), None)

    def _on_select(self, current, previous):
        row = self._current_xray_row()
        if not row:
            return
        abs_path = self.db.xray_abs_path(row)
        if abs_path.exists():
            pix = QPixmap(str(abs_path))
            if not pix.isNull():
                self.preview_label.setPixmap(pix.scaled(
                    self.preview_label.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation))
                return
        self.preview_label.setText("Image file not found")

    def attach_image(self):
        if self.patient_id is None:
            return
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select X-Ray Image", "",
            "Images (*.png *.jpg *.jpeg *.bmp *.tif *.tiff)")
        if not file_path:
            return
        try:
            self.db.add_xray(
                self.patient_id,
                Path(file_path),
                self.note_edit.text().strip(),
                self.date_edit.date().toString("yyyy-MM-dd"),
            )
        except Exception as exc:
            QMessageBox.critical(
                self, "Could Not Attach X-Ray",
                f"The X-ray image could not be saved:\n\n{exc}")
            return
        self.note_edit.clear()
        self.refresh()

    def remove_selected(self):
        row = self._current_xray_row()
        if not row:
            return
        confirm = QMessageBox.question(
            self, "Remove X-Ray", "Delete this X-ray image?")
        if confirm != QMessageBox.StandardButton.Yes:
            return
        try:
            self.db.delete_xray(row["id"])
        except Exception as exc:
            QMessageBox.critical(
                self, "Could Not Remove X-Ray", str(exc))
            return
        self.refresh()

    def open_selected(self):
        row = self._current_xray_row()
        if not row:
            return
        abs_path = self.db.xray_abs_path(row)
        if abs_path.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(abs_path)))
