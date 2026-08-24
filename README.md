# Radhika Dental Clinic

A desktop application for managing patient records at Radhika Dental
Clinic, built with **PyQt6** and a local **SQLite** database. No internet
connection or external server is required — all data and X-ray images stay
on the clinic's own computer.

## Features

- **Patient registration** with a Reg No / Unique ID (auto-suggested, e.g.
  `RC-00001`), name, age, sex, contact info, address, chief complaint and
  medical history.
- **Patient lookup** — search by Reg No, name or contact number when a
  patient revisits.
- **Treatment plan** — record the treatments advised for a patient along
  with the estimated cost of each, and see the total planned cost.
- **Treatment record** — a running ledger per patient of Date, Treatment,
  Amount, Paid and (automatically calculated) Balance.
- **X-ray attachments** — attach X-ray images taken in-house to a patient's
  file, with thumbnails, a preview pane, and the ability to open the
  full-size image.
- **Income & Expenses** — a monthly income summary computed automatically
  from treatment payments, plus a place to log clinic expenses (supplies,
  rent, salaries, etc.) with a monthly net total.
- **Local backups** — one click to save a full backup (database + X-ray
  images) as a `.zip` file anywhere you choose (a USB drive, another
  folder, etc.), and to restore from one.

All data is stored in `Documents/RadhikaClinicData` in the current
Windows/Mac/Linux user's profile (`clinic.db` plus an `xrays/` folder of
images), so a plain copy of that folder is also a valid backup.

## Running from source

```bash
python -m venv .venv
.venv\Scripts\activate        # on Windows
# source .venv/bin/activate   # on macOS/Linux

pip install -r requirements.txt
python run.py
```

## Building a standalone Windows .exe

Build the `.exe` on a Windows machine (PyInstaller builds for the OS it
runs on):

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pyinstaller radhika_clinic.spec
```

The finished application appears in `dist\RadhikaClinic\RadhikaClinic.exe`.
Copy the entire `dist\RadhikaClinic` folder to give the app to your wife —
it's fully self-contained and doesn't need Python installed on her
computer. She can pin `RadhikaClinic.exe` to the Start menu or desktop.

For a single-file `.exe` instead of a folder, edit `radhika_clinic.spec`
and change the `EXE(...)` block to use `a.binaries` and `a.datas` directly
with `onefile=True` (see the PyInstaller docs) — a folder build is
recommended here since it starts faster.

## Project layout

```
dental_clinic/
    database.py           SQLite schema and all data access
    main_window.py         Main window, tab wiring, backup/restore
    main.py                Application entry point
    widgets/
        patients_tab.py         Registration + search/lookup
        treatment_plan_tab.py   Advised treatment plan + cost
        treatment_record_tab.py Treatment ledger (Date/Treatment/Amount/Paid/Balance)
        xray_tab.py             X-ray image attachments
        finance_tab.py          Monthly income summary + expenses
run.py                     Convenience launcher / PyInstaller entry point
radhika_clinic.spec        PyInstaller build spec
requirements.txt
```
