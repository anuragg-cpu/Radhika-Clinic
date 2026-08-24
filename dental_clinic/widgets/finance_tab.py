from __future__ import annotations

from PyQt6.QtCore import Qt, QDate
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QLabel, QLineEdit, QDoubleSpinBox,
    QDateEdit, QMessageBox, QHeaderView, QGroupBox, QComboBox,
)

from ..database import Database

EXPENSE_CATEGORIES = [
    "Dental Supplies", "Lab Fees", "Staff Salary", "Rent", "Utilities",
    "Equipment", "Marketing", "Miscellaneous",
]


class FinanceTab(QWidget):
    """Monthly income (from paid treatment amounts) and expense tracking."""

    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        income_group = QGroupBox("Income by Month (from treatment payments)")
        income_layout = QVBoxLayout()
        self.income_table = QTableWidget(0, 4)
        self.income_table.setHorizontalHeaderLabels(
            ["Month", "Income", "Expenses", "Net"])
        self.income_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch)
        income_layout.addWidget(self.income_table)
        income_group.setLayout(income_layout)
        layout.addWidget(income_group, 1)

        expense_group = QGroupBox("Expenses")
        expense_layout = QVBoxLayout()

        self.expense_table = QTableWidget(0, 4)
        self.expense_table.setHorizontalHeaderLabels(
            ["Date", "Category", "Description", "Amount"])
        self.expense_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Stretch)
        self.expense_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows)
        expense_layout.addWidget(self.expense_table, 1)

        form = QFormLayout()
        self.exp_date = QDateEdit()
        self.exp_date.setCalendarPopup(True)
        self.exp_date.setDate(QDate.currentDate())
        self.exp_category = QComboBox()
        self.exp_category.setEditable(True)
        self.exp_category.addItems(EXPENSE_CATEGORIES)
        self.exp_description = QLineEdit()
        self.exp_amount = QDoubleSpinBox()
        self.exp_amount.setRange(0, 10_000_000)
        self.exp_amount.setDecimals(2)
        form.addRow("Date:", self.exp_date)
        form.addRow("Category:", self.exp_category)
        form.addRow("Description:", self.exp_description)
        form.addRow("Amount:", self.exp_amount)
        expense_layout.addLayout(form)

        buttons = QHBoxLayout()
        self.add_btn = QPushButton("Add Expense")
        self.remove_btn = QPushButton("Remove Selected")
        self.add_btn.clicked.connect(self.add_expense)
        self.remove_btn.clicked.connect(self.remove_selected)
        buttons.addWidget(self.add_btn)
        buttons.addWidget(self.remove_btn)
        buttons.addStretch()
        expense_layout.addLayout(buttons)

        expense_group.setLayout(expense_layout)
        layout.addWidget(expense_group, 1)

    def refresh(self):
        income_rows = {r["month"]: r["income"] or 0 for r in self.db.monthly_income()}
        expense_rows = {r["month"]: r["expense"] or 0 for r in self.db.monthly_expenses()}
        months = sorted(set(income_rows) | set(expense_rows), reverse=True)

        self.income_table.setRowCount(len(months))
        for r, month in enumerate(months):
            income = income_rows.get(month, 0)
            expense = expense_rows.get(month, 0)
            net = income - expense
            self.income_table.setItem(r, 0, QTableWidgetItem(month))
            self.income_table.setItem(r, 1, QTableWidgetItem(f"{income:.2f}"))
            self.income_table.setItem(r, 2, QTableWidgetItem(f"{expense:.2f}"))
            self.income_table.setItem(r, 3, QTableWidgetItem(f"{net:.2f}"))

        expenses = self.db.get_expenses()
        self.expense_table.setRowCount(len(expenses))
        for r, row in enumerate(expenses):
            date_item = QTableWidgetItem(row["date"])
            date_item.setData(Qt.ItemDataRole.UserRole, row["id"])
            self.expense_table.setItem(r, 0, date_item)
            self.expense_table.setItem(r, 1, QTableWidgetItem(row["category"] or ""))
            self.expense_table.setItem(r, 2, QTableWidgetItem(row["description"] or ""))
            self.expense_table.setItem(r, 3, QTableWidgetItem(f"{row['amount']:.2f}"))

    def add_expense(self):
        amount = self.exp_amount.value()
        if amount <= 0:
            QMessageBox.warning(self, "Missing information",
                                 "Enter an expense amount greater than zero.")
            return
        self.db.add_expense(
            self.exp_date.date().toString("yyyy-MM-dd"),
            self.exp_category.currentText().strip(),
            self.exp_description.text().strip(),
            amount,
        )
        self.exp_description.clear()
        self.exp_amount.setValue(0)
        self.refresh()

    def remove_selected(self):
        row = self.expense_table.currentRow()
        if row < 0:
            return
        expense_id = self.expense_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        self.db.delete_expense(expense_id)
        self.refresh()
