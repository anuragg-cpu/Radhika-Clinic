"""Local SQLite data layer for the Radhika Dental Clinic application.

All clinic data (patients, treatment plans, treatment records, X-ray
attachments and expenses) lives in a single SQLite database file stored on
the local machine, alongside a folder of X-ray image files. Nothing is sent
over the network -- backups are plain file copies made by the user.
"""

from __future__ import annotations

import shutil
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


def default_data_dir() -> Path:
    """Where clinic data lives on this machine.

    Kept under the user's home folder (Documents\\RadhikaClinicData on
    Windows, ~/RadhikaClinicData elsewhere) so it survives reinstalling or
    moving the application .exe, and so a plain folder copy is a full backup.
    """
    home = Path.home()
    documents = home / "Documents"
    base = documents if documents.exists() else home
    return base / "RadhikaClinicData"


SCHEMA = """
CREATE TABLE IF NOT EXISTS patients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reg_no TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    age INTEGER,
    sex TEXT,
    contact TEXT,
    address TEXT,
    chief_complaint TEXT,
    medical_history TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS treatment_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    description TEXT NOT NULL,
    cost REAL NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS treatment_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    date TEXT NOT NULL,
    treatment TEXT NOT NULL,
    amount REAL NOT NULL DEFAULT 0,
    paid REAL NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS xrays (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    note TEXT,
    taken_on TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    category TEXT,
    description TEXT,
    amount REAL NOT NULL DEFAULT 0
);
"""


@dataclass
class Patient:
    id: int
    reg_no: str
    name: str
    age: int | None
    sex: str
    contact: str
    address: str
    chief_complaint: str
    medical_history: str
    created_at: str


class Database:
    def __init__(self, data_dir: Path | None = None):
        self.data_dir = data_dir or default_data_dir()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.xray_dir = self.data_dir / "xrays"
        self.xray_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.data_dir / "clinic.db"
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    # ---------------------------------------------------------- patients --
    def next_reg_no(self) -> str:
        row = self.conn.execute("SELECT MAX(id) AS m FROM patients").fetchone()
        next_id = (row["m"] or 0) + 1
        return f"RC-{next_id:05d}"

    def add_patient(self, reg_no, name, age, sex, contact, address,
                     chief_complaint, medical_history) -> int:
        cur = self.conn.execute(
            """INSERT INTO patients
               (reg_no, name, age, sex, contact, address, chief_complaint,
                medical_history, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (reg_no, name, age, sex, contact, address, chief_complaint,
             medical_history, datetime.now().isoformat(timespec="seconds")),
        )
        self.conn.commit()
        return cur.lastrowid

    def update_patient(self, patient_id, reg_no, name, age, sex, contact,
                        address, chief_complaint, medical_history):
        self.conn.execute(
            """UPDATE patients SET reg_no=?, name=?, age=?, sex=?, contact=?,
               address=?, chief_complaint=?, medical_history=? WHERE id=?""",
            (reg_no, name, age, sex, contact, address, chief_complaint,
             medical_history, patient_id),
        )
        self.conn.commit()

    def delete_patient(self, patient_id):
        self.conn.execute("DELETE FROM patients WHERE id=?", (patient_id,))
        self.conn.commit()

    def get_patient(self, patient_id) -> sqlite3.Row | None:
        return self.conn.execute(
            "SELECT * FROM patients WHERE id=?", (patient_id,)
        ).fetchone()

    def reg_no_exists(self, reg_no, exclude_id=None) -> bool:
        if exclude_id is None:
            row = self.conn.execute(
                "SELECT 1 FROM patients WHERE reg_no=?", (reg_no,)
            ).fetchone()
        else:
            row = self.conn.execute(
                "SELECT 1 FROM patients WHERE reg_no=? AND id!=?",
                (reg_no, exclude_id),
            ).fetchone()
        return row is not None

    def search_patients(self, term: str) -> list[sqlite3.Row]:
        term = f"%{term.strip()}%"
        return self.conn.execute(
            """SELECT * FROM patients
               WHERE reg_no LIKE ? OR name LIKE ? OR contact LIKE ?
               ORDER BY name COLLATE NOCASE""",
            (term, term, term),
        ).fetchall()

    def all_patients(self) -> list[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM patients ORDER BY name COLLATE NOCASE"
        ).fetchall()

    # --------------------------------------------------- treatment plans --
    def add_treatment_plan(self, patient_id, description, cost):
        self.conn.execute(
            """INSERT INTO treatment_plans (patient_id, description, cost, created_at)
               VALUES (?, ?, ?, ?)""",
            (patient_id, description, cost, datetime.now().isoformat(timespec="seconds")),
        )
        self.conn.commit()

    def update_treatment_plan(self, plan_id, description, cost):
        self.conn.execute(
            "UPDATE treatment_plans SET description=?, cost=? WHERE id=?",
            (description, cost, plan_id),
        )
        self.conn.commit()

    def delete_treatment_plan(self, plan_id):
        self.conn.execute("DELETE FROM treatment_plans WHERE id=?", (plan_id,))
        self.conn.commit()

    def get_treatment_plans(self, patient_id) -> list[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM treatment_plans WHERE patient_id=? ORDER BY created_at",
            (patient_id,),
        ).fetchall()

    # ------------------------------------------------- treatment records --
    def add_treatment_record(self, patient_id, date, treatment, amount, paid):
        self.conn.execute(
            """INSERT INTO treatment_records (patient_id, date, treatment, amount, paid)
               VALUES (?, ?, ?, ?, ?)""",
            (patient_id, date, treatment, amount, paid),
        )
        self.conn.commit()

    def update_treatment_record(self, record_id, date, treatment, amount, paid):
        self.conn.execute(
            """UPDATE treatment_records SET date=?, treatment=?, amount=?, paid=?
               WHERE id=?""",
            (date, treatment, amount, paid, record_id),
        )
        self.conn.commit()

    def delete_treatment_record(self, record_id):
        self.conn.execute("DELETE FROM treatment_records WHERE id=?", (record_id,))
        self.conn.commit()

    def get_treatment_records(self, patient_id) -> list[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM treatment_records WHERE patient_id=? ORDER BY date",
            (patient_id,),
        ).fetchall()

    # ------------------------------------------------------------ xrays --
    def add_xray(self, patient_id, source_file: Path, note: str, taken_on: str) -> Path:
        source_file = Path(source_file)
        patient = self.get_patient(patient_id)
        patient_dir = self.xray_dir / patient["reg_no"]
        patient_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d%H%M%S")
        dest_name = f"{stamp}_{source_file.name}"
        dest_path = patient_dir / dest_name
        shutil.copy2(source_file, dest_path)
        rel_path = str(dest_path.relative_to(self.data_dir))
        self.conn.execute(
            "INSERT INTO xrays (patient_id, file_path, note, taken_on) VALUES (?, ?, ?, ?)",
            (patient_id, rel_path, note, taken_on),
        )
        self.conn.commit()
        return dest_path

    def delete_xray(self, xray_id):
        row = self.conn.execute("SELECT * FROM xrays WHERE id=?", (xray_id,)).fetchone()
        if row:
            file_path = self.data_dir / row["file_path"]
            if file_path.exists():
                file_path.unlink()
            self.conn.execute("DELETE FROM xrays WHERE id=?", (xray_id,))
            self.conn.commit()

    def get_xrays(self, patient_id) -> list[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM xrays WHERE patient_id=? ORDER BY taken_on",
            (patient_id,),
        ).fetchall()

    def xray_abs_path(self, row) -> Path:
        return self.data_dir / row["file_path"]

    # --------------------------------------------------------- expenses --
    def add_expense(self, date, category, description, amount):
        self.conn.execute(
            "INSERT INTO expenses (date, category, description, amount) VALUES (?, ?, ?, ?)",
            (date, category, description, amount),
        )
        self.conn.commit()

    def update_expense(self, expense_id, date, category, description, amount):
        self.conn.execute(
            "UPDATE expenses SET date=?, category=?, description=?, amount=? WHERE id=?",
            (date, category, description, amount, expense_id),
        )
        self.conn.commit()

    def delete_expense(self, expense_id):
        self.conn.execute("DELETE FROM expenses WHERE id=?", (expense_id,))
        self.conn.commit()

    def get_expenses(self) -> list[sqlite3.Row]:
        return self.conn.execute("SELECT * FROM expenses ORDER BY date DESC").fetchall()

    # ------------------------------------------------------- reporting --
    def monthly_income(self) -> list[sqlite3.Row]:
        return self.conn.execute(
            """SELECT strftime('%Y-%m', date) AS month, SUM(paid) AS income
               FROM treatment_records GROUP BY month ORDER BY month DESC"""
        ).fetchall()

    def monthly_expenses(self) -> list[sqlite3.Row]:
        return self.conn.execute(
            """SELECT strftime('%Y-%m', date) AS month, SUM(amount) AS expense
               FROM expenses GROUP BY month ORDER BY month DESC"""
        ).fetchall()

    def close(self):
        self.conn.close()
