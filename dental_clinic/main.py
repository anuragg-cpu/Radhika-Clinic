"""Entry point for the Radhika Dental Clinic desktop application."""

from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication

from .database import Database
from .main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Radhika Dental Clinic")

    db = Database()
    window = MainWindow(db)
    window.show()

    exit_code = app.exec()
    db.close()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
