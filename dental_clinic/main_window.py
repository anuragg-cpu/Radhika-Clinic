from __future__ import annotations

import shutil
import zipfile
from datetime import datetime
from pathlib import Path

from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QFileDialog, QMessageBox,
)

from .database import Database
from .widgets.patients_tab import PatientsTab
from .widgets.treatment_plan_tab import TreatmentPlanTab
from .widgets.treatment_record_tab import TreatmentRecordTab
from .widgets.xray_tab import XrayTab
from .widgets.finance_tab import FinanceTab


class MainWindow(QMainWindow):
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.setWindowTitle("Radhika Dental Clinic")
        self.resize(1100, 720)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.patients_tab = PatientsTab(db)
        self.plan_tab = TreatmentPlanTab(db)
        self.record_tab = TreatmentRecordTab(db)
        self.xray_tab = XrayTab(db)
        self.finance_tab = FinanceTab(db)

        self.tabs.addTab(self.patients_tab, "Patients")
        self.tabs.addTab(self.plan_tab, "Treatment Plan")
        self.tabs.addTab(self.record_tab, "Treatment Record")
        self.tabs.addTab(self.xray_tab, "X-Rays")
        self.tabs.addTab(self.finance_tab, "Income && Expenses")

        self.patients_tab.patient_selected.connect(self._on_patient_selected)
        self.tabs.currentChanged.connect(self._on_tab_changed)

        self._build_menu()

    def _build_menu(self):
        menu = self.menuBar().addMenu("&File")
        backup_action = menu.addAction("Backup Data...")
        backup_action.triggered.connect(self.backup_data)
        restore_action = menu.addAction("Restore from Backup...")
        restore_action.triggered.connect(self.restore_data)
        menu.addSeparator()
        exit_action = menu.addAction("Exit")
        exit_action.triggered.connect(self.close)

    def _on_patient_selected(self, patient_row):
        self.plan_tab.set_patient(patient_row)
        self.record_tab.set_patient(patient_row)
        self.xray_tab.set_patient(patient_row)

    def _on_tab_changed(self, index):
        if self.tabs.widget(index) is self.finance_tab:
            self.finance_tab.refresh()

    # -------------------------------------------------------- backups --
    def backup_data(self):
        suggested = f"RadhikaClinic_Backup_{datetime.now():%Y%m%d_%H%M%S}.zip"
        dest, _ = QFileDialog.getSaveFileName(
            self, "Save Backup As", suggested, "Zip Archive (*.zip)")
        if not dest:
            return
        try:
            self.db.conn.commit()
            archive_base = dest[:-4] if dest.endswith(".zip") else dest
            zip_path = shutil.make_archive(
                archive_base, "zip", root_dir=self.db.data_dir)
            QMessageBox.information(
                self, "Backup Complete", f"Backup saved to:\n{zip_path}")
        except Exception as exc:
            QMessageBox.critical(self, "Backup Failed", str(exc))

    def restore_data(self):
        confirm = QMessageBox.question(
            self, "Restore from Backup",
            "This will replace all current patient data with the contents "
            "of the chosen backup file. This cannot be undone. Continue?",
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        src, _ = QFileDialog.getOpenFileName(
            self, "Select Backup File", "", "Zip Archive (*.zip)")
        if not src:
            return
        try:
            self.db.close()
            data_dir = self.db.data_dir
            for item in data_dir.iterdir():
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
            with zipfile.ZipFile(src) as zf:
                zf.extractall(data_dir)
            self.db = Database(data_dir)
            self._reload_all_tabs()
            QMessageBox.information(self, "Restore Complete",
                                     "Data restored successfully.")
        except Exception as exc:
            QMessageBox.critical(self, "Restore Failed", str(exc))

    def _reload_all_tabs(self):
        for tab in (self.patients_tab, self.plan_tab, self.record_tab,
                    self.xray_tab, self.finance_tab):
            tab.db = self.db
        self.patients_tab.refresh_list()
        self.patients_tab.new_patient()
        self.finance_tab.refresh()
