"""
ui/final_window.py

Payroll review dialog.

Usage (as requested):

    from ui.final_window import FinalDialog

    dialog = FinalDialog(self)
    if dialog.exec():
        ...

Notes / assumptions made while implementing this:
  - `attendance_result_dict` values are mutated in place, so any edit made in
    the Details popup (add/delete a manual row, or edit deduction_points /
    spin_deduction / notes_edit / value / points / note) is reflected
    immediately in data.globals.attendance_result_dict - no extra "save back"
    step is needed for the in-memory dict. The "Save Data" button at the
    bottom is left as a stub for you to wire up to persistence (DB / file).

  - Each employee row now also carries a working-date range:

        "start_working_date": "2026-06-01",
        "end_working_date":   "2026-06-30",

    rendered as two QDateEdit (calendar popup) cells in the main table,
    defaulting to 2026-06-01 / 2026-06-30. Editing either date:
      1. writes the new "yyyy-MM-dd" string straight back into
         attendance_result_dict[emp_name],
      2. drops every "absences" entry whose date falls outside the new
         [start, end] range (mutating the list in place),
      3. recomputes fixed_salary / quality / quality_base / final using
         "range work days" = (end - start).days + 1, via:

             fixed_salary = (range_work_days / 30) * 3000
             quality_base = (range_work_days / 30) * 1000
             quality      = quality_base - ((points_minus - points_plus) * 100)
             quality      = min(quality, quality_base)   # cap, like before

      4. refreshes only that row's numeric cells (the date-edit widgets
         themselves are never rebuilt mid-signal, to avoid Qt deleting a
         widget while it's still emitting its own signal).

  - Because compute_employee_metrics() now always derives fixed_salary /
    quality_base / range_work_days from start_working_date / end_working_date,
    an emp dict without those keys defaults to a 0-day range (fixed_salary=0,
    quality_base=0) until FinalDialog.refresh_table() seeds the defaults
    (2026-06-01 / 2026-06-30) on first render.

  - The Details popup re-reads emp_data (including the already-filtered
    "absences" list) every time it's opened, so it always reflects the
    current working-date range - no separate live-sync path is needed
    since it's a modal dialog (the main table can't be edited while it's
    open anyway).
"""

from __future__ import annotations

from datetime import date, datetime
from functools import partial

from PySide6.QtCore import Qt, QDate
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QDateEdit,
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
    QFileDialog
)

from data.globals import attendance_result_dict
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font

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

# ---------------------------------------------------------------------------
# Working-date-range defaults / helpers
# ---------------------------------------------------------------------------

DEFAULT_START_DATE_STR = "2026-08-01"
DEFAULT_END_DATE_STR = "2026-08-31"
DEFAULT_START_QDATE = QDate(2026, 8, 1)
DEFAULT_END_QDATE = QDate(2026, 8, 31)


def _coerce_to_date(value):
    """Best-effort conversion of a stored date-ish value to a datetime.date."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        # Tolerate "2026-06-01" as well as "2026-06-01 08:00" style values.
        candidate = text.split(" ")[0]
        try:
            return datetime.strptime(candidate, "%Y-%m-%d").date()
        except ValueError:
            return None
    return None


def _str_to_qdate(value: str, fallback: QDate) -> QDate:
    """Parse a 'yyyy-MM-dd' string into a QDate, falling back if invalid."""
    if isinstance(value, str):
        qd = QDate.fromString(value.strip(), "yyyy-MM-dd")
        if qd.isValid():
            return qd
    return fallback


def compute_range_work_days(emp: dict) -> float:
    """Inclusive day-count between start_working_date and end_working_date."""
    start = _coerce_to_date(emp.get("start_working_date"))
    end = _coerce_to_date(emp.get("end_working_date"))
    if not start or not end or end < start:
        return 0
    return (end - start).days + 1


def filter_absences_in_range(emp_data: dict, start: date, end: date) -> bool:
    """
    Drops every "absences" entry whose nested date falls outside [start, end]
    (inclusive), mutating emp_data["absences"] in place. Entries whose date
    can't be parsed are kept as-is (fail safe rather than silently dropped).
    Returns True if the list was changed.
    """
    absences = emp_data.get("absences", [])
    kept = []
    changed = False
    for entry in absences:
        nested = entry.get("absence", {}) or {}
        entry_date = _coerce_to_date(nested.get("date"))
        if entry_date is None:
            kept.append(entry)
            continue
        if start <= entry_date <= end:
            kept.append(entry)
        else:
            changed = True
    if changed:
        emp_data["absences"] = kept
    return changed


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
    
def _is_empty(value) -> bool:
    """True for values that should be omitted from generated note text."""
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ""
    if isinstance(value, (int, float)):
        return value == 0
    return False

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

    range_work_days = compute_range_work_days(emp)

    # quality_base replaces the old flat "1000": both the base quality you'd
    # get with zero net deduction points, and the cap on quality, now scale
    # with the employee's working-date range.
    quality_base = (range_work_days / 31) * 1000
    quality = quality_base - ((points_minus - points_plus) * 100)

    if quality > quality_base:
        quality = quality_base

    quality_cancelled = bool(emp.get("quality_cancelled", False))
    if quality_cancelled:
        quality = 0

    fixed_salary = (range_work_days / 31) * 3000
    target_bonus = emp.get("target_bonus", 0) or 0

    final = fixed_salary + target_bonus + quality + main_plus - main_minus

    return {
        "main_plus": main_plus,
        "main_minus": main_minus,
        "points_plus": points_plus,
        "points_minus": points_minus,
        "range_work_days": range_work_days,
        "quality_base": quality_base,
        "quality_cancelled": quality_cancelled,
        "quality": quality,
        "fixed_salary": fixed_salary,
        "final": final,
    }

# ---------------------------------------------------------------------------
# Notes text generation (for the Excel export)
# ---------------------------------------------------------------------------

def _deduction_suffix(deduction_points, spin_deduction, notes_edit) -> str:
    """
    Builds the "خصم X نقاط وY من الاساسي <notes_edit>" tail shared by
    absences / permissions / latencies / early_leaves / need_reviews.
    Any part that is 0 / "" / None is skipped entirely.
    """
    dp_empty = _is_empty(deduction_points)
    sd_empty = _is_empty(spin_deduction)

    parts = []
    if not dp_empty and not sd_empty:
        parts.append(f"خصم {deduction_points} نقاط و{spin_deduction} من الاساسي")
    elif not dp_empty:
        parts.append(f"خصم {deduction_points} نقاط")
    elif not sd_empty:
        parts.append(f"خصم {spin_deduction} من الاساسي")

    if not _is_empty(notes_edit):
        parts.append(str(notes_edit))

    return " ".join(parts)


def _note_for_absence(entry: dict) -> str:
    date = entry.get("absence", {}).get("date", "")
    base = f"غياب يوم {date}" if not _is_empty(date) else "غياب"
    suffix = _deduction_suffix(
        entry.get("deduction_points"), entry.get("spin_deduction"), entry.get("notes_edit")
    )
    return " ".join(p for p in (base, suffix) if p)


def _note_for_permission(entry: dict) -> str:
    nested = entry.get("permission", {})
    start, end = nested.get("start"), nested.get("end")
    duration = nested.get("duration_minutes")

    base = ""
    if not _is_empty(duration):
        base = f"اذن لمدة {duration} دقيقة"
        if not _is_empty(start) and not _is_empty(end):
            base += f" من {_fmt(start)} الى {_fmt(end)}"

    suffix = _deduction_suffix(
        entry.get("deduction_points"), entry.get("spin_deduction"), entry.get("notes_edit")
    )
    return " ".join(p for p in (base, suffix) if p)


def _note_for_latency(entry: dict) -> str:
    nested = entry.get("latency", {})
    minutes, date = nested.get("minutes"), nested.get("date")

    base = ""
    if not _is_empty(minutes):
        base = f"تأخير لمدة {minutes} دقيقة"
        if not _is_empty(date):
            base += f" يوم {date}"

    suffix = _deduction_suffix(
        entry.get("deduction_points"), entry.get("spin_deduction"), entry.get("notes_edit")
    )
    return " ".join(p for p in (base, suffix) if p)


def _note_for_early_leave(entry: dict) -> str:
    nested = entry.get("early_leave", {})
    minutes, date = nested.get("minutes"), nested.get("date")

    base = ""
    if not _is_empty(minutes):
        base = f"مغادرة مبكرة {minutes} دقيقة"
        if not _is_empty(date):
            base += f" يوم {date}"

    suffix = _deduction_suffix(
        entry.get("deduction_points"), entry.get("spin_deduction"), entry.get("notes_edit")
    )
    return " ".join(p for p in (base, suffix) if p)


def _note_for_need_review(entry: dict) -> str:
    nested = entry.get("need_review", {})
    date, reason = nested.get("date"), nested.get("reason")

    base = ""
    if not _is_empty(date):
        base = f"مراجعة يوم {date}"
    if not _is_empty(reason):
        base = f"{base} السبب {reason}" if base else f"مراجعة - السبب {reason}"

    suffix = _deduction_suffix(
        entry.get("deduction_points"), entry.get("spin_deduction"), entry.get("notes_edit")
    )
    return " ".join(p for p in (base, suffix) if p)


def _note_for_manual_addition(entry: dict) -> str:
    value, note = entry.get("value"), entry.get("note")
    parts = []
    if not _is_empty(value):
        parts.append(f"اضافة {value}")
    if not _is_empty(note):
        parts.append(f"السبب {note}")
    return " ".join(parts)


def _note_for_manual_deduction(entry: dict) -> str:
    value, points, note = entry.get("value"), entry.get("points"), entry.get("note")
    v_empty, p_empty = _is_empty(value), _is_empty(points)

    parts = []
    if not v_empty and not p_empty:
        parts.append(f"خصم {value} و{points} نقطة")
    elif not v_empty:
        parts.append(f"خصم {value}")
    elif not p_empty:
        parts.append(f"خصم {points} نقطة")

    if not _is_empty(note):
        parts.append(f"السبب {note}")

    return " ".join(parts)


_NOTE_BUILDERS = {
    "absences": _note_for_absence,
    "permissions": _note_for_permission,
    "latencies": _note_for_latency,
    "early_leaves": _note_for_early_leave,
    "need_reviews": _note_for_need_review,
    "manually_additions": _note_for_manual_addition,
    "manually_deductions": _note_for_manual_deduction,
}


def build_employee_notes(emp: dict) -> str:
    """
    Concatenates one readable Arabic line per record (absences, permissions,
    latencies, early_leaves, need_reviews, manual additions/deductions),
    skipping any sub-part whose value is 0 / "" / None, plus the
    target_bonus_explain line if present.
    """
    lines = []

    for cat_key, builder in _NOTE_BUILDERS.items():
        for entry in emp.get(cat_key, []):
            line = builder(entry)
            if line:
                lines.append(line)

    explain = emp.get("target_bonus_explain")
    if not _is_empty(explain):
        lines.append(str(explain))

    return "\n".join(lines)
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

    The "absences" tab always reflects whatever is currently in
    emp_data["absences"] - since FinalDialog already drops out-of-range
    absences the moment a working date is changed, this popup shows the
    filtered list automatically each time it's opened (no extra syncing
    needed, as it's opened modally).
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
            f"Range: {self.emp_data.get('start_working_date', '')} \u2192 "
            f"{self.emp_data.get('end_working_date', '')} "
            f"({metrics['range_work_days']} days)   |   "
            f"Fixed Salary: {metrics['fixed_salary']:.2f}   |   "
            f"Main +: {metrics['main_plus']}   |   Main -: {metrics['main_minus']}   |   "
            f"Points +: {metrics['points_plus']}   |   Points -: {metrics['points_minus']}   |   "
            f"Quality: {metrics['quality']:.2f}   |   Final: {metrics['final']:.2f}"
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
        "Start Working Date",
        "End Working Date",
        "Main +",
        "Main -",
        "Points +",
        "Points -",
        "Quality",
        "Cancel Quality",
        "Final",
        "Details",
    ]

    # Column indices, named for readability.
    COL_EMPLOYEE = 0
    COL_ACHIEVED_TARGET = 1
    COL_TARGET_BONUS = 2
    COL_START_DATE = 3
    COL_END_DATE = 4
    COL_MAIN_PLUS = 5
    COL_MAIN_MINUS = 6
    COL_POINTS_PLUS = 7
    COL_POINTS_MINUS = 8
    COL_QUALITY = 9
    COL_CANCEL_QUALITY = 10
    COL_FINAL = 11
    COL_DETAILS = 12

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Payroll Review")
        self.resize(1350, 700)

        # emp_name -> current row index, kept up to date by refresh_table()
        # so date-edit callbacks can find "their" row without needing to
        # rebuild/search the whole table.
        self.emp_name_to_row: dict[str, int] = {}

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
        self.emp_name_to_row = {}

        for row, (emp_name, emp_data) in enumerate(attendance_result_dict.items()):
            self.emp_name_to_row[emp_name] = row

            # Seed default working-date range the first time we see this
            # employee, mirroring it straight into attendance_result_dict.
            emp_data.setdefault("start_working_date", DEFAULT_START_DATE_STR)
            emp_data.setdefault("end_working_date", DEFAULT_END_DATE_STR)

            metrics = compute_employee_metrics(emp_data)

            achieved = emp_data.get("achieved", 0)
            target = emp_data.get("target", 0)

            # -- static text columns -----------------------------------
            static_values = {
                self.COL_EMPLOYEE: emp_name,
                self.COL_ACHIEVED_TARGET: f"{achieved}/{target}",
                self.COL_TARGET_BONUS: emp_data.get("target_bonus", 0),
                self.COL_MAIN_PLUS: metrics["main_plus"],
                self.COL_MAIN_MINUS: metrics["main_minus"],
                self.COL_POINTS_PLUS: metrics["points_plus"],
                self.COL_POINTS_MINUS: metrics["points_minus"],
                self.COL_QUALITY: metrics["quality"],
                self.COL_FINAL: metrics["final"],
            }
            for col, value in static_values.items():
                cell = QTableWidgetItem(str(value))
                cell.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, col, cell)

            # -- start / end working date pickers -----------------------
            start_edit = QDateEdit()
            start_edit.setCalendarPopup(True)
            start_edit.setDisplayFormat("yyyy-MM-dd")
            start_edit.setDate(_str_to_qdate(emp_data["start_working_date"], DEFAULT_START_QDATE))
            start_edit.dateChanged.connect(partial(self._on_start_date_changed, emp_name=emp_name))
            self.table.setCellWidget(row, self.COL_START_DATE, start_edit)

            end_edit = QDateEdit()
            end_edit.setCalendarPopup(True)
            end_edit.setDisplayFormat("yyyy-MM-dd")
            end_edit.setDate(_str_to_qdate(emp_data["end_working_date"], DEFAULT_END_QDATE))
            end_edit.dateChanged.connect(partial(self._on_end_date_changed, emp_name=emp_name))
            self.table.setCellWidget(row, self.COL_END_DATE, end_edit)

            # -- cancel-quality checkbox ---------------------------------
            cancel_checkbox = QCheckBox()
            cancel_checkbox.setChecked(bool(emp_data.get("quality_cancelled", False)))
            cancel_checkbox.stateChanged.connect(
                partial(self._on_cancel_quality_changed, emp_name=emp_name)
            )
            checkbox_container = QWidget()
            checkbox_layout = QHBoxLayout(checkbox_container)
            checkbox_layout.addWidget(cancel_checkbox)
            checkbox_layout.setAlignment(Qt.AlignCenter)
            checkbox_layout.setContentsMargins(0, 0, 0, 0)
            self.table.setCellWidget(row, self.COL_CANCEL_QUALITY, checkbox_container)

            # -- details button -------------------------------------------
            details_btn = QPushButton("Details")
            details_btn.clicked.connect(partial(self.open_details, emp_name=emp_name))
            self.table.setCellWidget(row, self.COL_DETAILS, details_btn)

        self.table.resizeRowsToContents()

    # -- live date-range editing ----------------------------------------

    def _on_start_date_changed(self, qdate: QDate, emp_name: str):
        self._handle_date_change(emp_name, "start_working_date", qdate)

    def _on_end_date_changed(self, qdate: QDate, emp_name: str):
        self._handle_date_change(emp_name, "end_working_date", qdate)

    def _on_cancel_quality_changed(self, state: int, emp_name: str):
        emp_data = attendance_result_dict.get(emp_name)
        if emp_data is None:
            return

        # state is a Qt.CheckState int (0 = unchecked, 2 = checked for a
        # non-tristate checkbox), so bool(state) is exactly what we want.
        emp_data["quality_cancelled"] = bool(state)

        row = self.emp_name_to_row.get(emp_name)
        if row is not None:
            self._update_row_metrics(row, emp_data)

    def _handle_date_change(self, emp_name: str, key: str, qdate: QDate):
        emp_data = attendance_result_dict.get(emp_name)
        if emp_data is None:
            return

        emp_data[key] = qdate.toString("yyyy-MM-dd")

        start = _coerce_to_date(emp_data.get("start_working_date"))
        end = _coerce_to_date(emp_data.get("end_working_date"))
        if start and end and end >= start:
            filter_absences_in_range(emp_data, start, end)

        row = self.emp_name_to_row.get(emp_name)
        if row is not None:
            # Only touch the numeric item cells here - never rebuild the
            # date-edit widgets themselves while one of them is still
            # emitting this very signal.
            self._update_row_metrics(row, emp_data)

    def _update_row_metrics(self, row: int, emp_data: dict):
        metrics = compute_employee_metrics(emp_data)
        achieved = emp_data.get("achieved", 0)
        target = emp_data.get("target", 0)

        values = {
            self.COL_ACHIEVED_TARGET: f"{achieved}/{target}",
            self.COL_TARGET_BONUS: emp_data.get("target_bonus", 0),
            self.COL_MAIN_PLUS: metrics["main_plus"],
            self.COL_MAIN_MINUS: metrics["main_minus"],
            self.COL_POINTS_PLUS: metrics["points_plus"],
            self.COL_POINTS_MINUS: metrics["points_minus"],
            self.COL_QUALITY: metrics["quality"],
            self.COL_FINAL: metrics["final"],
        }
        for col, value in values.items():
            item = self.table.item(row, col)
            if item is None:
                item = QTableWidgetItem()
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, col, item)
            item.setText(str(value))

    def open_details(self, emp_name: str):
        emp_data = attendance_result_dict.get(emp_name)
        if emp_data is None:
            return

        dialog = DetailsDialog(emp_name, emp_data, self)
        dialog.exec()

        # attendance_result_dict was mutated in place while the popup was
        # open; re-render the main table's numeric cells so everything
        # (including achieved values) is up to date. Full refresh_table()
        # is safe here since we're not inside a widget's own signal.
        self.refresh_table()

    # -- bottom action buttons (stubs) -----------------------------------

    def export_pdf(self):
        """TODO: implement PDF export."""
        pass

    def export_excel(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export to Excel", "payroll.xlsx", "Excel Files (*.xlsx)"
        )
        if not path:
            return

        headers = [
            "Employee Name",
            "Start Working Date",
            "End Working Date",
            "Main",
            "Main After Deductions/Additions",
            "Quality",
            "Quality After Deductions/Additions",
            "Target",
            "Achieved",
            "Target Bonus",
            "Final Salary",
            "Notes",
        ]

        wb = Workbook()
        sheet = wb.active
        sheet.title = "Payroll"

        header_font = Font(name="Arial", bold=True)
        cell_font = Font(name="Arial")
        wrap_align = Alignment(wrap_text=True, vertical="top")

        sheet.append(headers)
        for cell in sheet[1]:
            cell.font = header_font

        for emp_name, emp_data in attendance_result_dict.items():
            metrics = compute_employee_metrics(emp_data)

            main = metrics["fixed_salary"]
            main_after = main + metrics["main_plus"] - metrics["main_minus"]

            quality_base = 0 if metrics["quality_cancelled"] else metrics["quality_base"]
            quality_after = 0 if metrics["quality_cancelled"] else quality_base + (metrics["points_plus"]*100) - (metrics["points_minus"]*100)

            target = emp_data.get("target", 0)
            achieved = emp_data.get("achieved", 0)
            target_bonus = emp_data.get("target_bonus", 0)
            final_salary = metrics["final"]

            notes = build_employee_notes(emp_data)

            row = [
                emp_name,
                emp_data.get("start_working_date", ""),
                emp_data.get("end_working_date", ""),
                main,
                main_after,
                quality_base,
                quality_after,
                target,
                achieved,
                target_bonus,
                final_salary,
                notes,
            ]
            sheet.append(row)

            note_cell = sheet.cell(row=sheet.max_row, column=len(headers))
            note_cell.alignment = wrap_align
            for col in range(1, len(headers) + 1):
                sheet.cell(row=sheet.max_row, column=col).font = cell_font

        widths = [22, 16, 16, 10, 26, 10, 28, 10, 10, 14, 14, 60]
        for col_idx, width in enumerate(widths, start=1):
            sheet.column_dimensions[chr(64 + col_idx)].width = width

        try:
            wb.save(path)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Export Failed", f"Could not save file:\n{exc}")
            return

        QMessageBox.information(self, "Export Complete", f"Excel file saved to:\n{path}")

    def save_data(self):
        """TODO: implement persistence of attendance_result_dict."""
        pass