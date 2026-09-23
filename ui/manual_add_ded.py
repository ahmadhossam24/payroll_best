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
from PySide6.QtCore import QEvent, QObject
import json 

from data.globals import attendance_result_dict
with open("data/employee_mapping.json", "r") as f:
    employee_mapping = json.load(f) 
display_names= [val["display_name"] for val in employee_mapping.values()]

class WheelEventFilter(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._wheel_enabled = False  # flip to True if you want wheel control later

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Wheel and not self._wheel_enabled:
            event.ignore()
            return True  # block the event from reaching the combo
        return super().eventFilter(obj, event)
    
class ManualAddDedDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("اضافة خصم او زيادة")
        self.resize(700, 500)

        self.adjustments = []

        self.wheel_filter = WheelEventFilter(self)
        layout = QVBoxLayout(self)

        row = QHBoxLayout()

        self.employee_combo = QComboBox()
        self.employee_combo.installEventFilter(self.wheel_filter) # prevent scroll
        self.employee_combo.addItems(
            # attendance_result_dict.keys()
            display_names
        )

        self.type_combo = QComboBox()
        self.type_combo.installEventFilter(self.wheel_filter) # prevent scroll
        self.type_combo.addItems([
            "اضف زيادة",
            "اضف خصم"
        ])

        self.value_spin = QSpinBox()
        self.value_spin.installEventFilter(self.wheel_filter) # prevent scroll
        self.value_spin.setMaximum(1000000)

        # Points combo
        self.points_combo = QComboBox()
        self.points_combo.installEventFilter(self.wheel_filter)
        points_values = ["0","0.25", "0.50", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]
        self.points_combo.addItems(points_values)
        self.points_combo.setCurrentIndex(0)   # default to "0"

        self.note_edit = QLineEdit()

        self.btn_add = QPushButton("اضافة")

        row.addWidget(QLabel("الموظف"))
        row.addWidget(self.employee_combo)

        row.addWidget(QLabel("النوع"))
        row.addWidget(self.type_combo)

        row.addWidget(QLabel("قيمة الزيادة او الخصم من الاساسي"))
        row.addWidget(self.value_spin)

        row.addWidget(QLabel("عدد النقاط"))
        row.addWidget(self.points_combo)

        row.addWidget(QLabel("ملاحظات"))
        row.addWidget(self.note_edit)

        row.addWidget(self.btn_add)

        layout.addLayout(row)

        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)

        self.btn_delete = QPushButton(
            "مسح"
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
        fingerprint_name = next((k for k, v in employee_mapping.items() if v["display_name"] == self.employee_combo.currentText()), None)
        adjustment = {
            # "employee": self.employee_combo.currentText(),
            "employee": fingerprint_name,
            "type": self.type_combo.currentText(),
            "value": self.value_spin.value(),
            "points": self.points_combo.currentText(),   # store as string or float? Keep as string for display
            "note": self.note_edit.text()
        }

        self.adjustments.append(adjustment)

        text = (
            f"{adjustment['employee']} | "
            f"{adjustment['type']} | "
            f"{adjustment['value']} | "
            f"Points: {adjustment['points']} | "
            f"{adjustment['note']}"
        )

        self.list_widget.addItem(text)

        self.value_spin.setValue(0)
        self.points_combo.setCurrentIndex(2)   # reset to "1"
        self.note_edit.clear()

    def delete_selected(self):

        row = self.list_widget.currentRow()

        if row < 0:
            return

        self.list_widget.takeItem(row)
        self.adjustments.pop(row)

    def save_data(self):

        # Reset manual lists for all employees
        for employee in attendance_result_dict.values():
            employee["manually_additions"] = []
            employee["manually_deductions"] = []
            employee["fixed_salary"] = 3000
            employee["target_bonus"] = 0
            employee["target_bonus_explain"] = ""
            employee["zero_accepts_deductions"] = 0
            employee["target"] = 0
            employee["achieved"] = 0

        for adjustment in self.adjustments:

            employee = attendance_result_dict[adjustment["employee"]]

            item = {
                "value": adjustment["value"],
                "points": adjustment["points"],   # added
                "note": adjustment["note"]
            }

            if adjustment["type"] == "اضف زيادة":
                employee["manually_additions"].append(item)
            else:
                employee["manually_deductions"].append(item)

        self.accept()