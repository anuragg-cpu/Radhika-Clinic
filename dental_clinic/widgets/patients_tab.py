from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QSpinBox,
    QComboBox, QTextEdit, QPushButton, QListWidget, QListWidgetItem,
    QMessageBox, QLabel, QGroupBox,
)

from ..database import Database


class PatientsTab(QWidget):
    """Register new patients and look up existing ones by Reg No / name."""

    patient_selected = pyqtSignal(object)  # emits patient row or None

    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.current_patient_id: int | None = None
        self._build_ui()
        self.refresh_list()

    def _build_ui(self):
        root = QHBoxLayout(self)

        # ---- left: search + list -----------------------------------
        left = QVBoxLayout()
        left.addWidget(QLabel("<b>Find Patient</b>"))
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search by Reg No, name or contact...")
        self.search_box.textChanged.connect(self.refresh_list)
        left.addWidget(self.search_box)

        self.patient_list = QListWidget()
        self.patient_list.itemClicked.connect(self._on_pick)
        left.addWidget(self.patient_list, 1)

        left_box = QWidget()
        left_box.setLayout(left)
        left_box.setMaximumWidth(320)
        root.addWidget(left_box)

        # ---- right: registration form --------------------------------
        form_group = QGroupBox("Patient Details")
        form = QFormLayout()

        self.reg_no_edit = QLineEdit()
        self.name_edit = QLineEdit()
        self.age_spin = QSpinBox()
        self.age_spin.setRange(0, 120)
        self.sex_combo = QComboBox()
        self.sex_combo.addItems(["Male", "Female", "Other"])
        self.contact_edit = QLineEdit()
        self.address_edit = QTextEdit()
        self.address_edit.setFixedHeight(60)
        self.address_edit.setTabChangesFocus(True)
        self.complaint_edit = QTextEdit()
        self.complaint_edit.setFixedHeight(60)
        self.complaint_edit.setTabChangesFocus(True)
        self.history_edit = QTextEdit()
        self.history_edit.setFixedHeight(60)
        self.history_edit.setTabChangesFocus(True)

        form.addRow("Reg No / Unique ID:", self.reg_no_edit)
        form.addRow("Name:", self.name_edit)
        form.addRow("Age:", self.age_spin)
        form.addRow("Sex:", self.sex_combo)
        form.addRow("Contact:", self.contact_edit)
        form.addRow("Address:", self.address_edit)
        form.addRow("Chief Complaint:", self.complaint_edit)
        form.addRow("Medical History:", self.history_edit)

        form_group.setLayout(form)
        root.addWidget(form_group, 1)

        buttons = QVBoxLayout()
        self.new_btn = QPushButton("New Patient")
        self.save_btn = QPushButton("Save")
        self.delete_btn = QPushButton("Delete")
        self.new_btn.clicked.connect(self.new_patient)
        self.save_btn.clicked.connect(self.save_patient)
        self.delete_btn.clicked.connect(self.delete_patient)
        buttons.addWidget(self.new_btn)
        buttons.addWidget(self.save_btn)
        buttons.addWidget(self.delete_btn)
        buttons.addStretch()
        root.addLayout(buttons)

    # ------------------------------------------------------------------
    def refresh_list(self):
        term = self.search_box.text().strip()
        rows = self.db.search_patients(term) if term else self.db.all_patients()
        self.patient_list.clear()
        for row in rows:
            item = QListWidgetItem(f"{row['reg_no']} — {row['name']}")
            item.setData(Qt.ItemDataRole.UserRole, row["id"])
            self.patient_list.addItem(item)

    def _on_pick(self, item: QListWidgetItem):
        patient_id = item.data(Qt.ItemDataRole.UserRole)
        self.load_patient(patient_id)

    def load_patient(self, patient_id: int):
        row = self.db.get_patient(patient_id)
        if not row:
            return
        self.current_patient_id = row["id"]
        self.reg_no_edit.setText(row["reg_no"])
        self.name_edit.setText(row["name"])
        self.age_spin.setValue(row["age"] or 0)
        idx = self.sex_combo.findText(row["sex"] or "Male")
        self.sex_combo.setCurrentIndex(idx if idx >= 0 else 0)
        self.contact_edit.setText(row["contact"] or "")
        self.address_edit.setPlainText(row["address"] or "")
        self.complaint_edit.setPlainText(row["chief_complaint"] or "")
        self.history_edit.setPlainText(row["medical_history"] or "")
        self.patient_selected.emit(row)

    def new_patient(self):
        self.current_patient_id = None
        self.reg_no_edit.setText(self.db.next_reg_no())
        self.name_edit.clear()
        self.age_spin.setValue(0)
        self.sex_combo.setCurrentIndex(0)
        self.contact_edit.clear()
        self.address_edit.clear()
        self.complaint_edit.clear()
        self.history_edit.clear()
        self.patient_selected.emit(None)
        self.name_edit.setFocus()

    def save_patient(self):
        reg_no = self.reg_no_edit.text().strip()
        name = self.name_edit.text().strip()
        if not reg_no or not name:
            QMessageBox.warning(self, "Missing information",
                                 "Reg No and Name are required.")
            return
        # If this is a brand-new patient but the name matches someone
        # already on file, ask whether to update that existing record
        # instead of creating a duplicate entry.
        if self.current_patient_id is None:
            matches = self.db.find_patients_by_name(name)
            if matches:
                existing = matches[0]
                choice = QMessageBox.question(
                    self, "Existing Patient Found",
                    f"A patient named '{name}' already exists "
                    f"(Reg No: {existing['reg_no']}).\n\n"
                    "Do you want to update that existing record instead of "
                    "creating a new one? Choose No to register a separate, "
                    "different patient with the same name.",
                    QMessageBox.StandardButton.Yes
                    | QMessageBox.StandardButton.No
                    | QMessageBox.StandardButton.Cancel,
                    QMessageBox.StandardButton.Yes,
                )
                if choice == QMessageBox.StandardButton.Cancel:
                    return
                if choice == QMessageBox.StandardButton.Yes:
                    self.current_patient_id = existing["id"]
                    reg_no = existing["reg_no"]
                    self.reg_no_edit.setText(reg_no)

        if self.db.reg_no_exists(reg_no, exclude_id=self.current_patient_id):
            QMessageBox.warning(self, "Duplicate Reg No",
                                 f"Reg No '{reg_no}' is already in use.")
            return

        age = self.age_spin.value()
        sex = self.sex_combo.currentText()
        contact = self.contact_edit.text().strip()
        address = self.address_edit.toPlainText().strip()
        complaint = self.complaint_edit.toPlainText().strip()
        history = self.history_edit.toPlainText().strip()

        is_new = self.current_patient_id is None
        if is_new:
            new_id = self.db.add_patient(reg_no, name, age, sex, contact,
                                          address, complaint, history)
            self.current_patient_id = new_id
        else:
            self.db.update_patient(self.current_patient_id, reg_no, name, age,
                                    sex, contact, address, complaint, history)

        self.refresh_list()
        self.load_patient(self.current_patient_id)
        if is_new:
            QMessageBox.information(self, "Saved", f"Patient '{name}' saved.")
        else:
            QMessageBox.information(
                self, "Updated",
                f"Existing record for '{name}' (Reg No: {reg_no}) updated.")

    def delete_patient(self):
        if self.current_patient_id is None:
            return
        confirm = QMessageBox.question(
            self, "Delete Patient",
            "This will permanently delete the patient and all of their "
            "treatment plans, records and X-rays. Continue?",
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        self.db.delete_patient(self.current_patient_id)
        self.current_patient_id = None
        self.refresh_list()
        self.new_patient()
