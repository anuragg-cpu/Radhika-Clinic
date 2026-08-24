from __future__ import annotations

from PyQt6.QtCore import Qt, QDate
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QLabel, QLineEdit, QDoubleSpinBox,
    QDateEdit, QMessageBox, QHeaderView,
)

from ..database import Database


class TreatmentRecordTab(QWidget):
    """Dental treatment record: Date, Treatment, Amount, Paid, Balance."""

    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.patient_id: int | None = None
        self.editing_record_id: int | None = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        self.header = QLabel("<b>No patient selected</b>")
        layout.addWidget(self.header)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            ["Date", "Treatment", "Amount", "Paid", "Balance"])
        self.table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.itemSelectionChanged.connect(self._on_row_selected)
        layout.addWidget(self.table, 1)

        self.totals_label = QLabel("Total amount: 0.00   Total paid: 0.00   Total balance: 0.00")
        layout.addWidget(self.totals_label)

        form = QFormLayout()
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.treatment_edit = QLineEdit()
        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(0, 10_000_000)
        self.amount_spin.setDecimals(2)
        self.paid_spin = QDoubleSpinBox()
        self.paid_spin.setRange(0, 10_000_000)
        self.paid_spin.setDecimals(2)
        form.addRow("Date:", self.date_edit)
        form.addRow("Treatment:", self.treatment_edit)
        form.addRow("Amount:", self.amount_spin)
        form.addRow("Paid:", self.paid_spin)
        layout.addLayout(form)

        buttons = QHBoxLayout()
        self.add_btn = QPushButton("Add Entry")
        self.update_btn = QPushButton("Update Selected")
        self.remove_btn = QPushButton("Remove Selected")
        self.clear_btn = QPushButton("Clear Form")
        self.add_btn.clicked.connect(self.add_record)
        self.update_btn.clicked.connect(self.update_record)
        self.remove_btn.clicked.connect(self.remove_selected)
        self.clear_btn.clicked.connect(self.clear_form)
        buttons.addWidget(self.add_btn)
        buttons.addWidget(self.update_btn)
        buttons.addWidget(self.remove_btn)
        buttons.addWidget(self.clear_btn)
        buttons.addStretch()
        layout.addLayout(buttons)

        self.set_patient(None)

    def set_patient(self, patient_row):
        self.patient_id = patient_row["id"] if patient_row else None
        enabled = self.patient_id is not None
        for w in (self.table, self.date_edit, self.treatment_edit,
                  self.amount_spin, self.paid_spin, self.add_btn,
                  self.update_btn, self.remove_btn, self.clear_btn):
            w.setEnabled(enabled)
        if patient_row:
            self.header.setText(
                f"<b>Treatment Record for {patient_row['name']} "
                f"({patient_row['reg_no']})</b>")
            self.refresh()
        else:
            self.header.setText("<b>Select a patient in the Patients tab</b>")
            self.table.setRowCount(0)
            self.totals_label.setText(
                "Total amount: 0.00   Total paid: 0.00   Total balance: 0.00")
        self.clear_form()

    def refresh(self):
        if self.patient_id is None:
            return
        rows = self.db.get_treatment_records(self.patient_id)
        self.table.setRowCount(len(rows))
        total_amount = total_paid = 0.0
        for r, row in enumerate(rows):
            balance = row["amount"] - row["paid"]
            date_item = QTableWidgetItem(row["date"])
            date_item.setData(Qt.ItemDataRole.UserRole, row["id"])
            self.table.setItem(r, 0, date_item)
            self.table.setItem(r, 1, QTableWidgetItem(row["treatment"]))
            self.table.setItem(r, 2, QTableWidgetItem(f"{row['amount']:.2f}"))
            self.table.setItem(r, 3, QTableWidgetItem(f"{row['paid']:.2f}"))
            self.table.setItem(r, 4, QTableWidgetItem(f"{balance:.2f}"))
            total_amount += row["amount"]
            total_paid += row["paid"]
        total_balance = total_amount - total_paid
        self.totals_label.setText(
            f"Total amount: {total_amount:.2f}   "
            f"Total paid: {total_paid:.2f}   "
            f"Total balance: {total_balance:.2f}")

    def _on_row_selected(self):
        row = self.table.currentRow()
        if row < 0:
            return
        record_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        records = self.db.get_treatment_records(self.patient_id)
        match = next((r for r in records if r["id"] == record_id), None)
        if not match:
            return
        self.editing_record_id = record_id
        self.date_edit.setDate(QDate.fromString(match["date"], "yyyy-MM-dd"))
        self.treatment_edit.setText(match["treatment"])
        self.amount_spin.setValue(match["amount"])
        self.paid_spin.setValue(match["paid"])

    def clear_form(self):
        self.editing_record_id = None
        self.date_edit.setDate(QDate.currentDate())
        self.treatment_edit.clear()
        self.amount_spin.setValue(0)
        self.paid_spin.setValue(0)
        self.table.clearSelection()

    def _validate(self) -> str | None:
        if not self.treatment_edit.text().strip():
            return "Enter the treatment performed."
        return None

    def add_record(self):
        if self.patient_id is None:
            return
        error = self._validate()
        if error:
            QMessageBox.warning(self, "Missing information", error)
            return
        self.db.add_treatment_record(
            self.patient_id,
            self.date_edit.date().toString("yyyy-MM-dd"),
            self.treatment_edit.text().strip(),
            self.amount_spin.value(),
            self.paid_spin.value(),
        )
        self.clear_form()
        self.refresh()

    def update_record(self):
        if self.editing_record_id is None:
            QMessageBox.information(self, "No selection",
                                     "Select a record in the table to update.")
            return
        error = self._validate()
        if error:
            QMessageBox.warning(self, "Missing information", error)
            return
        self.db.update_treatment_record(
            self.editing_record_id,
            self.date_edit.date().toString("yyyy-MM-dd"),
            self.treatment_edit.text().strip(),
            self.amount_spin.value(),
            self.paid_spin.value(),
        )
        self.clear_form()
        self.refresh()

    def remove_selected(self):
        row = self.table.currentRow()
        if row < 0:
            return
        record_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        self.db.delete_treatment_record(record_id)
        self.clear_form()
        self.refresh()
