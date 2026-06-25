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
    Tab for managing the mapping between fingerprint names and target sheet names.
    Data is stored in 'employee_mapping.json' in the application root.
    """

    # Path to the shared JSON file
    MAPPING_FILE = "employee_mapping.json"

    def __init__(self):
        super().__init__()

        # In-memory dictionary: {fingerprint_name: target_name}
        self.mapping = {}

        # Setup UI
        self._setup_ui()

        # Load existing mapping from file
        self.load_data()

        # Populate the table
        self.populate_table()

    # ---------- UI Construction ----------
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)

        # ----- Table (read-only, selection triggers edit) -----
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Fingerprint Name", "Target Name"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)  # Read-only
        self.table.clicked.connect(self._on_row_selected)

        main_layout.addWidget(QLabel("Current Mappings:"))
        main_layout.addWidget(self.table)

        # ----- Input Form (for add / update) -----
        form_group = QGroupBox("Add / Edit Mapping")
        form_layout = QFormLayout(form_group)

        self.fingerprint_input = QLineEdit()
        self.fingerprint_input.setPlaceholderText("e.g. noor")
        form_layout.addRow("Fingerprint Name:", self.fingerprint_input)

        self.target_input = QLineEdit()
        self.target_input.setPlaceholderText("e.g. nour")
        form_layout.addRow("Target Sheet Name:", self.target_input)

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

        # Disable update/delete initially (no selection)
        self._set_action_buttons_enabled(False)

    def _set_action_buttons_enabled(self, enabled):
        self.btn_update.setEnabled(enabled)
        self.btn_delete.setEnabled(enabled)

    # ---------- Data Persistence ----------
    def load_data(self):
        """Load mapping from JSON file. If file doesn't exist, start empty."""
        if os.path.exists(self.MAPPING_FILE):
            try:
                with open(self.MAPPING_FILE, "r", encoding="utf-8") as f:
                    self.mapping = json.load(f)
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
        """Write the current mapping to the JSON file."""
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

        for row, (fingerprint, target) in enumerate(self.mapping.items()):
            self.table.setItem(row, 0, QTableWidgetItem(fingerprint))
            self.table.setItem(row, 1, QTableWidgetItem(target))

        # Clear selection after refresh
        self.table.clearSelection()
        self._set_action_buttons_enabled(False)

    # ---------- CRUD Operations ----------
    def add_employee(self):
        """Add a new mapping entry."""
        fingerprint = self.fingerprint_input.text().strip()
        target = self.target_input.text().strip()

        if not fingerprint or not target:
            QMessageBox.warning(self, "Missing Data", "Both fields are required.")
            return

        if fingerprint in self.mapping:
            QMessageBox.warning(
                self,
                "Duplicate Entry",
                f"Fingerprint name '{fingerprint}' already exists.\nUse Update to change it."
            )
            return

        # Add and save
        self.mapping[fingerprint] = target
        self.save_data()
        self.populate_table()
        self.clear_fields()

    def update_employee(self):
        """Update the currently selected mapping."""
        selected_row = self.table.currentRow()
        if selected_row < 0:
            QMessageBox.information(self, "No Selection", "Please select a row to update.")
            return

        old_fingerprint = self.table.item(selected_row, 0).text()
        new_fingerprint = self.fingerprint_input.text().strip()
        new_target = self.target_input.text().strip()

        if not new_fingerprint or not new_target:
            QMessageBox.warning(self, "Missing Data", "Both fields are required.")
            return

        # If fingerprint changed, check that the new name doesn't already exist
        if new_fingerprint != old_fingerprint and new_fingerprint in self.mapping:
            QMessageBox.warning(
                self,
                "Duplicate Entry",
                f"Fingerprint name '{new_fingerprint}' already exists.\nCannot rename to an existing entry."
            )
            return

        # Remove old key, insert new key
        del self.mapping[old_fingerprint]
        self.mapping[new_fingerprint] = new_target

        self.save_data()
        self.populate_table()
        self.clear_fields()

    def delete_employee(self):
        """Delete the currently selected mapping with confirmation."""
        selected_row = self.table.currentRow()
        if selected_row < 0:
            QMessageBox.information(self, "No Selection", "Please select a row to delete.")
            return

        fingerprint = self.table.item(selected_row, 0).text()
        target = self.table.item(selected_row, 1).text()

        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete the mapping:\n'{fingerprint}' -> '{target}'?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            del self.mapping[fingerprint]
            self.save_data()
            self.populate_table()
            self.clear_fields()

    def clear_fields(self):
        """Clear the input fields and deselect table row."""
        self.fingerprint_input.clear()
        self.target_input.clear()
        self.table.clearSelection()
        self._set_action_buttons_enabled(False)

    # ---------- UI Callbacks ----------
    def _on_row_selected(self):
        """When a table row is clicked, populate the input fields for editing."""
        selected_row = self.table.currentRow()
        if selected_row < 0:
            return

        fingerprint = self.table.item(selected_row, 0).text()
        target = self.table.item(selected_row, 1).text()

        self.fingerprint_input.setText(fingerprint)
        self.target_input.setText(target)

        self._set_action_buttons_enabled(True)