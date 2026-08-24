from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QLineEdit, QDoubleSpinBox, QMessageBox,
    QHeaderView, QFormLayout,
)

from ..database import Database


class TreatmentPlanTab(QWidget):
    """Advised treatment plan and its estimated cost, per patient."""

    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.patient_id: int | None = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        self.header = QLabel("<b>No patient selected</b>")
        layout.addWidget(self.header)

        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Treatment Advised", "Cost"])
        self.table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.table, 1)

        self.total_label = QLabel("Total planned cost: 0.00")
        layout.addWidget(self.total_label)

        form = QFormLayout()
        self.desc_edit = QLineEdit()
        self.cost_spin = QDoubleSpinBox()
        self.cost_spin.setRange(0, 10_000_000)
        self.cost_spin.setDecimals(2)
        form.addRow("Treatment:", self.desc_edit)
        form.addRow("Cost:", self.cost_spin)
        layout.addLayout(form)

        buttons = QHBoxLayout()
        self.add_btn = QPushButton("Add Item")
        self.remove_btn = QPushButton("Remove Selected")
        self.add_btn.clicked.connect(self.add_item)
        self.remove_btn.clicked.connect(self.remove_selected)
        buttons.addWidget(self.add_btn)
        buttons.addWidget(self.remove_btn)
        buttons.addStretch()
        layout.addLayout(buttons)

        self.set_patient(None)

    def set_patient(self, patient_row):
        self.patient_id = patient_row["id"] if patient_row else None
        enabled = self.patient_id is not None
        for w in (self.table, self.desc_edit, self.cost_spin,
                  self.add_btn, self.remove_btn):
            w.setEnabled(enabled)
        if patient_row:
            self.header.setText(
                f"<b>Treatment Plan for {patient_row['name']} "
                f"({patient_row['reg_no']})</b>")
            self.refresh()
        else:
            self.header.setText("<b>Select a patient in the Patients tab</b>")
            self.table.setRowCount(0)
            self.total_label.setText("Total planned cost: 0.00")

    def refresh(self):
        if self.patient_id is None:
            return
        rows = self.db.get_treatment_plans(self.patient_id)
        self.table.setRowCount(len(rows))
        total = 0.0
        for r, row in enumerate(rows):
            desc_item = QTableWidgetItem(row["description"])
            desc_item.setData(Qt.ItemDataRole.UserRole, row["id"])
            cost_item = QTableWidgetItem(f"{row['cost']:.2f}")
            self.table.setItem(r, 0, desc_item)
            self.table.setItem(r, 1, cost_item)
            total += row["cost"]
        self.total_label.setText(f"Total planned cost: {total:.2f}")

    def add_item(self):
        if self.patient_id is None:
            return
        desc = self.desc_edit.text().strip()
        if not desc:
            QMessageBox.warning(self, "Missing information",
                                 "Enter a treatment description.")
            return
        self.db.add_treatment_plan(self.patient_id, desc, self.cost_spin.value())
        self.desc_edit.clear()
        self.cost_spin.setValue(0)
        self.refresh()

    def remove_selected(self):
        row = self.table.currentRow()
        if row < 0:
            return
        plan_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        self.db.delete_treatment_plan(plan_id)
        self.refresh()
