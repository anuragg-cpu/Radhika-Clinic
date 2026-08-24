"""Convenience launcher: `python run.py` starts the clinic application.

This is also the entry point PyInstaller builds into the standalone .exe.
"""

from dental_clinic.main import main

if __name__ == "__main__":
    main()
