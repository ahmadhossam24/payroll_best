"""
ui/final_window.py

Payroll review dialog.

Usage (as requested):

    from ui.final_window import FinalDialog

    dialog = FinalDialog(self)
    if dialog.exec():
        ...

Notes / assumptions made while implementing this:
  - Uses PySide6. If you're on PySide2, only the import lines need changing
    (QtWidgets/QtCore/QtGui import paths are the same names either way).
  - `attendance_result_dict` values are mutated in place, so any edit made in
    the Details popup (add/delete a manual row, or edit deduction_points /
    spin_deduction / notes_edit / value / points / note) is reflected
    immediately in data.globals.attendance_result_dict - no extra "save back"
    step is needed for the in-memory dict. The "Save Data" button at the
    bottom is left as a stub for you to wire up to persistence (DB / file).
  - "final" formula literally uses fixed_salary (defaults to 3000 if a given
    employee dict doesn't define it) + target_bonus + quality + main+ - main-,
    matching the spec ("3000 + target_bonus + quality + main+ - main-").
"""

from __future__ import annotations

from datetime import datetime
from functools import partial

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from data.globals import attendance_result_dict


# ---------------------------------------------------------------------------
# Category configuration
# ---------------------------------------------------------------------------

# Categories that hold "deduction style" entries. Each entry has a nested
# dict (e.g. item["absence"]) with read-only descriptive fields, plus the
# three editable fields: deduction_points, spin_deduction, notes_edit.
DEDUCTION_CATEGORIES = {
    "absences": {
        "nested_key": "absence",
        "fields": ["date"],
        "title": "Absences",
    },
    "permissions": {
        "nested_key": "permission",
        "fields": ["start", "end", "duration_minutes"],
        "title": "Permissions",
    },
    "latencies": {
        "nested_key": "latency",
        "fields": ["date", "checkin_time", "minutes"],
        "title": "Latencies",
    },
    "early_leaves": {
        "nested_key": "early_leave",
        "fields": ["date", "checkout_time", "minutes"],
        "title": "Early Leaves",
    },
    "need_reviews": {
        "nested_key": "need_review",
        "fields": ["date", "reason"],
        "title": "Need Reviews",
    },
}

EDITABLE_DEDUCTION_COLUMNS = ["deduction_points", "spin_deduction", "notes_edit"]
EDITABLE_DEDUCTION_HEADERS = ["Deduction Points", "Spin Deduction", "Notes"]

# Categories that are simple flat lists the user can add/delete rows from.
MANUAL_CATEGORIES = {
    "manually_additions": "Manual Additions",
    "manually_deductions": "Manual Deductions",
}
MANUAL_COLUMNS = ["value", "points", "note"]
MANUAL_HEADERS = ["Value", "Points", "Note"]

def _to_number(value) -> float:
    """Coerce a value to a number, defaulting to 0 if it isn't numeric."""
    if value is None:
        return 0
    if isinstance(value, (int, float)):
        return value
    try:
        text = str(value).strip()
        if text == "":
            return 0
        if "." in text:
            return float(text)
        return int(text)
    except (ValueError, TypeError):
        return 0

def _fmt(value):
    """Human readable representation for read-only cells."""
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M")
    return "" if value is None else str(value)


def _parse_number(text: str):
    """Best-effort parse of a user-typed number, falling back to the raw text."""
    text = text.strip()
    if text == "":
        return 0
    try:
        as_int = int(text)
        return as_int
    except ValueError:
        pass
    try:
        return float(text)
    except ValueError:
        return text


# ---------------------------------------------------------------------------
# Calculations
# ---------------------------------------------------------------------------

def compute_employee_metrics(emp: dict) -> dict:
    """Compute all derived payroll values for a single employee dict."""

    def sum_spin_deduction():
        total = 0
        for cat in DEDUCTION_CATEGORIES:
            for item in emp.get(cat, []):
                total += _to_number(item.get("spin_deduction", 0)) or 0
        return total

    def sum_deduction_points():
        total = 0
        for cat in DEDUCTION_CATEGORIES:
            for item in emp.get(cat, []):
                total += _to_number(item.get("deduction_points", 0)) or 0
        return total

    main_plus = sum(_to_number(item.get("value", 0) )or 0 for item in emp.get("manually_additions", []))
    main_minus = sum(
        _to_number(item.get("value", 0) )or 0 for item in emp.get("manually_deductions", [])
    ) + sum_spin_deduction()

    points_plus = sum(_to_number(item.get("points", 0)) or 0 for item in emp.get("manually_additions", []))
    points_minus = (
        sum(_to_number(item.get("points", 0)) or 0 for item in emp.get("manually_deductions", []))
        + sum_deduction_points()
        + (emp.get("zero_accepts_deductions", 0) or 0)
    )

    quality = 1000 - (points_minus - points_plus * 100)
    if quality < 0:
        quality = 0
    elif quality > 1000:
        quality=1000

    fixed_salary = emp.get("fixed_salary", 3000) or 0
    target_bonus = emp.get("target_bonus", 0) or 0

    final = fixed_salary + target_bonus + quality + main_plus - main_minus

    return {
        "main_plus": main_plus,
        "main_minus": main_minus,
        "points_plus": points_plus,
        "points_minus": points_minus,
        "quality": quality,
        "final": final,
    }


# ---------------------------------------------------------------------------
# Details popup
# ---------------------------------------------------------------------------

class DetailsDialog(QDialog):
    """
    Popup showing every record for one employee:
    absences / permissions / latencies / early_leaves / need_reviews
    (deduction_points, spin_deduction, notes_edit are editable)
    and manually_additions / manually_deductions
    (value, points, note are editable, rows can be added/deleted).

    All edits write straight back into the employee dict that lives inside
    attendance_result_dict, so the underlying data is updated immediately.
    """

    def __init__(self, emp_name: str, emp_data: dict, parent=None):
        super().__init__(parent)
        self.emp_name = emp_name
        self.emp_data = emp_data

        self.setWindowTitle(f"Details - {emp_name}")
        self.resize(900, 600)

        self.deduction_tables: dict[str, QTableWidget] = {}
        self.manual_tables: dict[str, QTableWidget] = {}

        layout = QVBoxLayout(self)

        self.summary_label = QLabel()
        self.summary_label.setStyleSheet("font-weight: bold; padding: 4px;")
        layout.addWidget(self.summary_label)

        tabs = QTabWidget()
        layout.addWidget(tabs)

        for cat_key, config in DEDUCTION_CATEGORIES.items():
            tab = self._build_deduction_tab(cat_key, config)
            tabs.addTab(tab, config["title"])

        for cat_key, title in MANUAL_CATEGORIES.items():
            tab = self._build_manual_tab(cat_key, title)
            tabs.addTab(tab, title)

        close_layout = QHBoxLayout()
        close_layout.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        close_layout.addWidget(close_btn)
        layout.addLayout(close_layout)

        self._refresh_summary()

    # -- summary -----------------------------------------------------------

    def _refresh_summary(self):
        metrics = compute_employee_metrics(self.emp_data)
        self.summary_label.setText(
            f"Main +: {metrics['main_plus']}   |   Main -: {metrics['main_minus']}   |   "
            f"Points +: {metrics['points_plus']}   |   Points -: {metrics['points_minus']}   |   "
            f"Quality: {metrics['quality']}   |   Final: {metrics['final']}"
        )

    # -- deduction-style tabs (absences, permissions, latencies, ...) -----

    def _build_deduction_tab(self, cat_key: str, config: dict) -> QWidget:
        widget = QWidget()
        vlayout = QVBoxLayout(widget)

        fields = config["fields"]
        headers = [f.replace("_", " ").title() for f in fields] + EDITABLE_DEDUCTION_HEADERS

        table = QTableWidget()
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)

        self.deduction_tables[cat_key] = table
        vlayout.addWidget(table)

        self._populate_deduction_table(cat_key, config)

        table.itemChanged.connect(partial(self._on_deduction_item_changed, cat_key=cat_key, config=config))

        return widget

    def _populate_deduction_table(self, cat_key: str, config: dict):
        table = self.deduction_tables[cat_key]
        table.blockSignals(True)

        items = self.emp_data.get(cat_key, [])
        fields = config["fields"]
        nested_key = config["nested_key"]
        n_fields = len(fields)

        table.setRowCount(len(items))
        for row, entry in enumerate(items):
            nested = entry.get(nested_key, {}) or {}

            # read-only descriptive fields
            for col, field_name in enumerate(fields):
                cell = QTableWidgetItem(_fmt(nested.get(field_name)))
                cell.setFlags(cell.flags() & ~Qt.ItemIsEditable)
                table.setItem(row, col, cell)

            # editable fields: deduction_points, spin_deduction, notes_edit
            for offset, key in enumerate(EDITABLE_DEDUCTION_COLUMNS):
                col = n_fields + offset
                value = entry.get(key, "")
                cell = QTableWidgetItem(_fmt(value))
                table.setItem(row, col, cell)

        table.blockSignals(False)

    def _on_deduction_item_changed(self, item: QTableWidgetItem, cat_key: str, config: dict):
        row = item.row()
        col = item.column()
        n_fields = len(config["fields"])

        if col < n_fields:
            return  # read-only descriptive column, ignore

        key = EDITABLE_DEDUCTION_COLUMNS[col - n_fields]
        text = item.text()
        value = text if key == "notes_edit" else _parse_number(text)

        try:
            self.emp_data[cat_key][row][key] = value
        except IndexError:
            return

        self._refresh_summary()

    # -- manual tabs (manually_additions / manually_deductions) -----------

    def _build_manual_tab(self, cat_key: str, title: str) -> QWidget:
        widget = QWidget()
        vlayout = QVBoxLayout(widget)

        table = QTableWidget()
        table.setColumnCount(len(MANUAL_HEADERS))
        table.setHorizontalHeaderLabels(MANUAL_HEADERS)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)

        self.manual_tables[cat_key] = table
        vlayout.addWidget(table)

        self._populate_manual_table(cat_key)

        table.itemChanged.connect(partial(self._on_manual_item_changed, cat_key=cat_key))

        btn_layout = QHBoxLayout()
        add_btn = QPushButton(f"Add {title[:-1] if title.endswith('s') else title}")
        delete_btn = QPushButton("Delete Selected")
        add_btn.clicked.connect(partial(self._add_manual_row, cat_key=cat_key))
        delete_btn.clicked.connect(partial(self._delete_manual_rows, cat_key=cat_key))
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(delete_btn)
        btn_layout.addStretch()
        vlayout.addLayout(btn_layout)

        return widget

    def _populate_manual_table(self, cat_key: str):
        table = self.manual_tables[cat_key]
        table.blockSignals(True)

        items = self.emp_data.get(cat_key, [])
        table.setRowCount(len(items))
        for row, entry in enumerate(items):
            for col, key in enumerate(MANUAL_COLUMNS):
                value = entry.get(key, "")
                cell = QTableWidgetItem(_fmt(value))
                table.setItem(row, col, cell)

        table.blockSignals(False)

    def _on_manual_item_changed(self, item: QTableWidgetItem, cat_key: str):
        row = item.row()
        col = item.column()
        key = MANUAL_COLUMNS[col]
        text = item.text()
        value = text if key == "note" else _parse_number(text)

        try:
            self.emp_data[cat_key][row][key] = value
        except IndexError:
            return

        self._refresh_summary()

    def _add_manual_row(self, cat_key: str):
        self.emp_data.setdefault(cat_key, []).append({"value": 0, "points": 0, "note": ""})
        self._populate_manual_table(cat_key)
        self._refresh_summary()

    def _delete_manual_rows(self, cat_key: str):
        table = self.manual_tables[cat_key]
        selected_rows = sorted({idx.row() for idx in table.selectedIndexes()}, reverse=True)
        if not selected_rows:
            QMessageBox.information(self, "Delete", "Select a row first.")
            return

        items = self.emp_data.get(cat_key, [])
        for row in selected_rows:
            if 0 <= row < len(items):
                del items[row]

        self._populate_manual_table(cat_key)
        self._refresh_summary()


# ---------------------------------------------------------------------------
# Main payroll dialog
# ---------------------------------------------------------------------------

class FinalDialog(QDialog):
    """Main payroll review dialog listing every employee."""

    COLUMNS = [
        "Employee",
        "Achieved/Target",
        "Target Bonus",
        "Main +",
        "Main -",
        "Points +",
        "Points -",
        "Quality",
        "Final",
        "Details",
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Payroll Review")
        self.resize(1250, 700)

        layout = QVBoxLayout(self)

        self.table = QTableWidget()
        self.table.setColumnCount(len(self.COLUMNS))
        self.table.setHorizontalHeaderLabels(self.COLUMNS)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        self.export_pdf_btn = QPushButton("Export PDF")
        self.export_excel_btn = QPushButton("Export Excel")
        self.save_btn = QPushButton("Save Data")

        self.export_pdf_btn.clicked.connect(self.export_pdf)
        self.export_excel_btn.clicked.connect(self.export_excel)
        self.save_btn.clicked.connect(self.save_data)

        btn_layout.addStretch()
        btn_layout.addWidget(self.export_pdf_btn)
        btn_layout.addWidget(self.export_excel_btn)
        btn_layout.addWidget(self.save_btn)
        layout.addLayout(btn_layout)

        self.refresh_table()

    # -- table rendering -----------------------------------------------

    def refresh_table(self):
        self.table.setRowCount(0)
        self.table.setRowCount(len(attendance_result_dict))

        for row, (emp_name, emp_data) in enumerate(attendance_result_dict.items()):
            metrics = compute_employee_metrics(emp_data)

            achieved = emp_data.get("achieved", 0)
            target = emp_data.get("target", 0)

            row_values = [
                emp_name,
                f"{achieved}/{target}",
                emp_data.get("target_bonus", 0),
                metrics["main_plus"],
                metrics["main_minus"],
                metrics["points_plus"],
                metrics["points_minus"],
                metrics["quality"],
                metrics["final"],
            ]

            for col, value in enumerate(row_values):
                cell = QTableWidgetItem(str(value))
                cell.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, col, cell)

            details_btn = QPushButton("Details")
            details_btn.clicked.connect(partial(self.open_details, emp_name=emp_name))
            self.table.setCellWidget(row, len(self.COLUMNS) - 1, details_btn)

        self.table.resizeRowsToContents()

    def open_details(self, emp_name: str):
        emp_data = attendance_result_dict.get(emp_name)
        if emp_data is None:
            return

        dialog = DetailsDialog(emp_name, emp_data, self)
        dialog.exec()

        # attendance_result_dict was mutated in place while the popup was
        # open; re-render the main table so achieved values are up to date.
        self.refresh_table()

    # -- bottom action buttons (stubs) -----------------------------------

    def export_pdf(self):
        """TODO: implement PDF export."""
        pass

    def export_excel(self):
        """TODO: implement Excel export."""
        pass

    def save_data(self):
        """TODO: implement persistence of attendance_result_dict."""
        pass
