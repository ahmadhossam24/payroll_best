import json
import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QHeaderView, QMessageBox, QGroupBox,
    QFormLayout
)
from PySide6.QtCore import Qt


class EmployeeManagementTab(QWidget):
    """
    Tab for managing employee mappings.
    Stores:
        key = fingerprint name (used for matching)
        value = {"target_sheet_name": ..., "display_name": ...}
    Data is stored in 'employee_mapping.json' in the application root.
    """

    MAPPING_FILE = "data/employee_mapping.json"

    def __init__(self):
        super().__init__()

        # In-memory dictionary: {fingerprint_name: {"target_sheet_name": ..., "display_name": ...}}
        self.mapping = {}

        self._setup_ui()
        self.load_data()
        self.populate_table()

    # ---------- UI Construction ----------
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)

        # ----- Table (read-only, selection triggers edit) -----
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Fingerprint Name", "Target Sheet Name", "Display Name"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.clicked.connect(self._on_row_selected)

        main_layout.addWidget(QLabel("Current Mappings:"))
        main_layout.addWidget(self.table)

        # ----- Input Form -----
        form_group = QGroupBox("Add / Edit Mapping")
        form_layout = QFormLayout(form_group)

        self.fingerprint_input = QLineEdit()
        self.fingerprint_input.setPlaceholderText("e.g. noor")
        form_layout.addRow("Fingerprint Name:", self.fingerprint_input)

        self.target_input = QLineEdit()
        self.target_input.setPlaceholderText("e.g. nour")
        form_layout.addRow("Target Sheet Name:", self.target_input)

        self.display_input = QLineEdit()
        self.display_input.setPlaceholderText("e.g. Noor Ahmed")
        form_layout.addRow("Display Name:", self.display_input)

        main_layout.addWidget(form_group)

        # ----- Action Buttons -----
        button_layout = QHBoxLayout()

        self.btn_add = QPushButton("➕ Add")
        self.btn_update = QPushButton("✏️ Update")
        self.btn_delete = QPushButton("🗑️ Delete")
        self.btn_clear = QPushButton("🧹 Clear Fields")

        self.btn_add.clicked.connect(self.add_employee)
        self.btn_update.clicked.connect(self.update_employee)
        self.btn_delete.clicked.connect(self.delete_employee)
        self.btn_clear.clicked.connect(self.clear_fields)

        button_layout.addWidget(self.btn_add)
        button_layout.addWidget(self.btn_update)
        button_layout.addWidget(self.btn_delete)
        button_layout.addWidget(self.btn_clear)
        button_layout.addStretch()

        main_layout.addLayout(button_layout)

        self._set_action_buttons_enabled(False)

    def _set_action_buttons_enabled(self, enabled):
        self.btn_update.setEnabled(enabled)
        self.btn_delete.setEnabled(enabled)

    # ---------- Data Persistence ----------
    def load_data(self):
        """Load mapping from JSON file. If file doesn't exist or is old format, start empty."""
        if os.path.exists(self.MAPPING_FILE):
            try:
                with open(self.MAPPING_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                # Validate structure (nested dict)
                if isinstance(data, dict) and all(isinstance(v, dict) for v in data.values()):
                    self.mapping = data
                else:
                    # Old format: {fingerprint: target} -> convert to new structure
                    new_mapping = {}
                    for k, v in data.items():
                        new_mapping[k] = {
                            "target_sheet_name": v,
                            "display_name": k  # use fingerprint as display name by default
                        }
                    self.mapping = new_mapping
                    self.save_data()  # overwrite with new format
            except (json.JSONDecodeError, IOError) as e:
                QMessageBox.warning(
                    self,
                    "Load Error",
                    f"Failed to load mapping file.\nError: {e}\nStarting with empty mapping."
                )
                self.mapping = {}
        else:
            self.mapping = {}

    def save_data(self):
        """Write the current mapping to the JSON file, converting keys to lowercase (target/display kept as-is)."""
        # Convert only the key (fingerprint) to lowercase
        lower_mapping = {}
        for k, v in self.mapping.items():
            lower_key = k.lower()
            lower_mapping[lower_key] = {
                "target_sheet_name": v.get("target_sheet_name", "").lower(),
                "display_name": v.get("display_name", "")  # keep display name as entered
            }
        self.mapping = lower_mapping

        try:
            with open(self.MAPPING_FILE, "w", encoding="utf-8") as f:
                json.dump(self.mapping, f, indent=4, ensure_ascii=False)
        except IOError as e:
            QMessageBox.critical(
                self,
                "Save Error",
                f"Failed to save mapping file.\nError: {e}"
            )

    # ---------- Table Population ----------
    def populate_table(self):
        """Refresh the table to reflect the current mapping dict."""
        self.table.setRowCount(len(self.mapping))

        for row, (fingerprint, details) in enumerate(self.mapping.items()):
            self.table.setItem(row, 0, QTableWidgetItem(fingerprint))
            self.table.setItem(row, 1, QTableWidgetItem(details.get("target_sheet_name", "")))
            self.table.setItem(row, 2, QTableWidgetItem(details.get("display_name", "")))

        self.table.clearSelection()
        self._set_action_buttons_enabled(False)

    # ---------- CRUD Operations ----------
    def add_employee(self):
        fingerprint = self.fingerprint_input.text().strip()
        target = self.target_input.text().strip()
        display = self.display_input.text().strip()

        if not fingerprint or not target or not display:
            QMessageBox.warning(self, "Missing Data", "All three fields are required.")
            return

        if fingerprint in self.mapping:
            QMessageBox.warning(
                self,
                "Duplicate Entry",
                f"Fingerprint name '{fingerprint}' already exists.\nUse Update to change it."
            )
            return

        self.mapping[fingerprint] = {
            "target_sheet_name": target,
            "display_name": display
        }
        self.save_data()
        self.populate_table()
        self.clear_fields()

    def update_employee(self):
        selected_row = self.table.currentRow()
        if selected_row < 0:
            QMessageBox.information(self, "No Selection", "Please select a row to update.")
            return

        old_fingerprint = self.table.item(selected_row, 0).text()
        new_fingerprint = self.fingerprint_input.text().strip()
        new_target = self.target_input.text().strip()
        new_display = self.display_input.text().strip()

        if not new_fingerprint or not new_target or not new_display:
            QMessageBox.warning(self, "Missing Data", "All three fields are required.")
            return

        # If fingerprint changed, check that the new name doesn't already exist (except itself)
        if new_fingerprint != old_fingerprint and new_fingerprint in self.mapping:
            QMessageBox.warning(
                self,
                "Duplicate Entry",
                f"Fingerprint name '{new_fingerprint}' already exists.\nCannot rename to an existing entry."
            )
            return

        # Remove old key, insert new key
        del self.mapping[old_fingerprint]
        self.mapping[new_fingerprint] = {
            "target_sheet_name": new_target,
            "display_name": new_display
        }

        self.save_data()
        self.populate_table()
        self.clear_fields()

    def delete_employee(self):
        selected_row = self.table.currentRow()
        if selected_row < 0:
            QMessageBox.information(self, "No Selection", "Please select a row to delete.")
            return

        fingerprint = self.table.item(selected_row, 0).text()
        display = self.table.item(selected_row, 2).text()

        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete the mapping for:\n'{fingerprint}' (Display: {display})?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            del self.mapping[fingerprint]
            self.save_data()
            self.populate_table()
            self.clear_fields()

    def clear_fields(self):
        self.fingerprint_input.clear()
        self.target_input.clear()
        self.display_input.clear()
        self.table.clearSelection()
        self._set_action_buttons_enabled(False)

    # ---------- UI Callbacks ----------
    def _on_row_selected(self):
        selected_row = self.table.currentRow()
        if selected_row < 0:
            return

        fingerprint = self.table.item(selected_row, 0).text()
        target = self.table.item(selected_row, 1).text()
        display = self.table.item(selected_row, 2).text()

        self.fingerprint_input.setText(fingerprint)
        self.target_input.setText(target)
        self.display_input.setText(display)

        self._set_action_buttons_enabled(True)