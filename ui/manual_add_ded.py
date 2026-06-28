from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QComboBox,
    QSpinBox,
    QLineEdit,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QDialogButtonBox,
    QLabel
)

from data.globals import attendance_result_dict


class ManualAddDedDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Manual Additions / Deductions")
        self.resize(700, 500)

        self.adjustments = []

        layout = QVBoxLayout(self)

        row = QHBoxLayout()

        self.employee_combo = QComboBox()
        self.employee_combo.addItems(
            attendance_result_dict.keys()
        )

        self.type_combo = QComboBox()
        self.type_combo.addItems([
            "Addition",
            "Deduction"
        ])

        self.value_spin = QSpinBox()
        self.value_spin.setMaximum(1000000)

        self.note_edit = QLineEdit()

        self.btn_add = QPushButton("Add")

        row.addWidget(QLabel("Employee"))
        row.addWidget(self.employee_combo)

        row.addWidget(QLabel("Type"))
        row.addWidget(self.type_combo)

        row.addWidget(QLabel("Value"))
        row.addWidget(self.value_spin)

        row.addWidget(QLabel("Note"))
        row.addWidget(self.note_edit)

        row.addWidget(self.btn_add)

        layout.addLayout(row)

        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)

        self.btn_delete = QPushButton(
            "Delete Selected"
        )

        layout.addWidget(self.btn_delete)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Save |
            QDialogButtonBox.Cancel
        )

        layout.addWidget(buttons)

        self.btn_add.clicked.connect(
            self.add_adjustment
        )

        self.btn_delete.clicked.connect(
            self.delete_selected
        )

        buttons.accepted.connect(
            self.save_data
        )

        buttons.rejected.connect(
            self.reject
        )

    def add_adjustment(self):

        adjustment = {

            "employee":
                self.employee_combo.currentText(),

            "type":
                self.type_combo.currentText(),

            "value":
                self.value_spin.value(),

            "note":
                self.note_edit.text()

        }

        self.adjustments.append(
            adjustment
        )

        text = (
            f"{adjustment['employee']} | "
            f"{adjustment['type']} | "
            f"{adjustment['value']} | "
            f"{adjustment['note']}"
        )

        self.list_widget.addItem(text)

        self.value_spin.setValue(0)
        self.note_edit.clear()
    
    def delete_selected(self):

        row = self.list_widget.currentRow()

        if row < 0:
            return

        self.list_widget.takeItem(row)

        self.adjustments.pop(row)

    def save_data(self):

        for employee in attendance_result_dict.values():

            employee["manually_additions"] = []

            employee["manually_deductions"] = []

        for adjustment in self.adjustments:

            employee = attendance_result_dict[
                adjustment["employee"]
            ]

            item = {
                "value": adjustment["value"],
                "note": adjustment["note"]
            }

            if adjustment["type"] == "Addition":

                employee[
                    "manually_additions"
                ].append(item)

            else:

                employee[
                    "manually_deductions"
                ].append(item)

        self.accept()