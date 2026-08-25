"""Entry point for the Radhika Dental Clinic desktop application."""

from __future__ import annotations

import sys
import traceback

from PyQt6.QtWidgets import QApplication, QMessageBox

from .database import Database
from .main_window import MainWindow


def _install_excepthook():
    """Show an error dialog instead of silently crashing on a bug.

    PyQt aborts the whole application if a Python exception escapes a
    signal/slot callback (e.g. a button click handler). Individual actions
    that do file or database I/O already catch their own errors, but this
    is a safety net for anything unexpected so the app stays open and the
    user doesn't just see the window vanish.
    """
    def handle_exception(exc_type, exc_value, exc_tb):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_tb)
            return
        traceback.print_exception(exc_type, exc_value, exc_tb)
        try:
            QMessageBox.critical(
                None, "Unexpected Error",
                "Something went wrong and the last action could not be "
                "completed. The application will stay open — please try "
                "again.\n\n"
                f"Details: {exc_value}")
        except Exception:
            pass

    sys.excepthook = handle_exception


def main():
    _install_excepthook()

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
