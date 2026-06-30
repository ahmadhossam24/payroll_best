# from data.globals import attendance_result_dict
# from PySide6.QtWidgets import (
#     QDialog,
#     QVBoxLayout,
#     QTabWidget,
#     QWidget,
#     QLabel,
#     QGroupBox,
#     QFormLayout,
#     QScrollArea,
#     QPushButton,
#     QDialogButtonBox,
#     QHBoxLayout,
#     QCheckBox,
#     QSpinBox,
#     QLineEdit
# )


# class AttendanceReviewDialog(QDialog):

#     def __init__(self, attendance_data, parent=None):
#         super().__init__(parent)
#         self.review_widgets = {}
#         self.attendance_data = attendance_data

#         self.setWindowTitle("Attendance Review")
#         self.resize(1000, 700)

#         main_layout = QVBoxLayout(self)

#         self.tabs = QTabWidget()

#         for employee_name, employee_data in attendance_data.items():

#             employee_widget = self.build_employee_tab(
#                 employee_name,
#                 employee_data["summary"]
#             )

#             self.tabs.addTab(
#                 employee_widget,
#                 employee_name
#             )

#         main_layout.addWidget(self.tabs)

#         buttons = QDialogButtonBox(
#             QDialogButtonBox.Ok |
#             QDialogButtonBox.Cancel
#         )

#         buttons.accepted.connect(self.get_review_data)
#         buttons.rejected.connect(self.reject)

#         main_layout.addWidget(buttons)

#     def get_converted_review_widgets(self):
#         """
#         Returns a deep copy of review_widgets where:
#         - allowed_checkbox -> .isChecked()
#         - deduction_spin   -> .value()
#         - notes_edit       -> .text()
#         All other fields (absence, permission, etc.) are left unchanged.
#         """
#         converted = {}
#         for employee, categories in self.review_widgets.items():
#             converted[employee] = {}
#             for category, rows in categories.items():
#                 converted[employee][category] = []
#                 for row in rows:
#                     new_row = {}
#                     for key, value in row.items():
#                         if key == "allowed_checkbox":
#                             new_row[key] = value.isChecked()
#                         elif key == "deduction_spin":
#                             new_row[key] = value.value()
#                         elif key == "notes_edit":
#                             new_row[key] = value.text()
#                         else:
#                             new_row[key] = value   # e.g. absence, permission, latency, etc.
#                     converted[employee][category].append(new_row)
#         return converted

#     def get_review_data(self):
#         converted_data = self.get_converted_review_widgets()
#         attendance_result_dict.update(converted_data)
#         self.accept()

#     def build_employee_tab(self, employee_name, summary):

#         self.review_widgets[f"{employee_name}"]={"absences": [],"permissions": [],"latencies":[],"early_leaves":[],"need_reviews":[]}

#         container = QWidget()
#         layout = QVBoxLayout(container)

#         layout.addWidget(
#             QLabel(f"<h2>{employee_name}</h2>")
#         )

#         layout.addWidget(
#             self.create_absences_group(
#                 summary["absent_days"],employee_name
#             )
#         )

#         layout.addWidget(
#             self.create_permissions_group(
#                 summary["permissions"],employee_name
#             )
#         )

#         layout.addWidget(
#             self.create_latencies_group(
#                 summary["latencies"],employee_name
#             )
#         )

#         layout.addWidget(
#             self.create_early_leaves_group(
#                 summary["early_leaves"],employee_name
#             )
#         )

#         layout.addWidget(
#             self.create_needs_review_group(
#                 summary["needs_review"],employee_name
#             )
#         )

#         layout.addStretch()

#         scroll = QScrollArea()
#         scroll.setWidgetResizable(True)
#         scroll.setWidget(container)

#         wrapper = QWidget()
#         wrapper_layout = QVBoxLayout(wrapper)
#         wrapper_layout.addWidget(scroll)

#         return wrapper
    
#     def create_absences_group(self, absences,employee_name):

#         group = QGroupBox(
#             f"Absences ({len(absences)})"
#         )

#         form = QFormLayout(group)

#         for absence in absences:

#             form.addRow(
#                 self.create_absence_row(absence,employee_name)
#             )

#         return group
    
#     def create_permissions_group(self, permissions,employee_name):

#         group = QGroupBox(
#             f"Permissions ({len(permissions)})"
#         )

#         form = QFormLayout(group)

#         for permission in permissions:

#             form.addRow(
#                 self.create_permission_row(permission,employee_name)
#             )

#         return group
    
#     def create_latencies_group(self, latencies,employee_name):

#         group = QGroupBox(
#             f"Latencies ({len(latencies)})"
#         )

#         form = QFormLayout(group)

#         for latency in latencies:

#             form.addRow(
#                 self.create_latency_row(latency,employee_name)
#             )

#         return group
    
#     def create_early_leaves_group(self, early_leaves,employee_name):

#         group = QGroupBox(
#             f"Early Leaves ({len(early_leaves)})"
#         )

#         form = QFormLayout(group)

#         for leave in early_leaves:

#             form.addRow(
#                 self.create_early_leave_row(leave,employee_name)
#             )

#         return group
    
#     def create_needs_review_group(self, reviews,employee_name):

#         group = QGroupBox(
#             f"Needs Review ({len(reviews)})"
#         )

#         form = QFormLayout(group)

#         for review in reviews:

#             form.addRow(
#                 self.create_need_review_row(review,employee_name)
#             )

#         return group
    
#     def create_absence_row(self, absence,employee_name):

#         row = QWidget()

#         layout = QHBoxLayout(row)

#         date_label = QLabel(absence["date"])

#         allowed_checkbox = QCheckBox("Allowed")

#         deduction_spin = QSpinBox()
#         deduction_spin.setMaximum(100000)
#         deduction_spin.setValue(300)

#         notes_edit = QLineEdit()

#         def allowed_changed(state):

#             if allowed_checkbox.isChecked():
#                 deduction_spin.setValue(100)
#             else:
#                 deduction_spin.setValue(300)

#         allowed_checkbox.stateChanged.connect(
#             allowed_changed
#         )

#         layout.addWidget(date_label)
#         layout.addWidget(allowed_checkbox)
#         layout.addWidget(deduction_spin)
#         layout.addWidget(notes_edit)

#         row_data = {
#             "allowed_checkbox": allowed_checkbox,
#             "deduction_spin": deduction_spin,
#             "notes_edit": notes_edit,
#             "absence": absence
#         }
#         self.review_widgets.setdefault(
#             employee_name,
#             {"absences": [],"permissions": [],"latencies":[],"early_leaves":[],"need_reviews":[]}
#         )["absences"].append(row_data)

#         return row
    
#     def create_permission_row(self, permission,employee_name):

#         text = (
#                 f"{permission['start']} → "
#                 f"{permission['end']} "
#                 f"({permission['duration_minutes']} min)"
#             )

#         row = QWidget()

#         layout = QHBoxLayout(row)

#         date_label = QLabel(text)

#         allowed_checkbox = QCheckBox("Allowed")

#         deduction_spin = QSpinBox()
#         deduction_spin.setMaximum(100000)
#         deduction_spin.setValue(300)

#         notes_edit = QLineEdit()

#         def allowed_changed(state):

#             if allowed_checkbox.isChecked():
#                 deduction_spin.setValue(100)
#             else:
#                 deduction_spin.setValue(300)

#         allowed_checkbox.stateChanged.connect(
#             allowed_changed
#         )

#         layout.addWidget(date_label)
#         layout.addWidget(allowed_checkbox)
#         layout.addWidget(deduction_spin)
#         layout.addWidget(notes_edit)

#         row_data = {
#             "allowed_checkbox": allowed_checkbox,
#             "deduction_spin": deduction_spin,
#             "notes_edit": notes_edit,
#             "permission": permission
#         }
#         self.review_widgets.setdefault(
#             employee_name,
#             {"absences": [],"permissions": [],"latencies":[],"early_leaves":[],"need_reviews":[]}
#         )["permissions"].append(row_data)

#         return row

#     def create_latency_row(self, latency,employee_name):

#         text = (
#                 f"{latency['date']} | "
#                 f"{latency['checkin_time']} | "
#                 f"{latency['minutes']} min"
#             )

#         row = QWidget()

#         layout = QHBoxLayout(row)

#         date_label = QLabel(text)

#         allowed_checkbox = QCheckBox("Allowed")

#         deduction_spin = QSpinBox()
#         deduction_spin.setMaximum(100000)
#         deduction_spin.setValue(300)

#         notes_edit = QLineEdit()

#         def allowed_changed(state):

#             if allowed_checkbox.isChecked():
#                 deduction_spin.setValue(100)
#             else:
#                 deduction_spin.setValue(300)

#         allowed_checkbox.stateChanged.connect(
#             allowed_changed
#         )

#         layout.addWidget(date_label)
#         layout.addWidget(allowed_checkbox)
#         layout.addWidget(deduction_spin)
#         layout.addWidget(notes_edit)

#         row_data = {
#             "allowed_checkbox": allowed_checkbox,
#             "deduction_spin": deduction_spin,
#             "notes_edit": notes_edit,
#             "latency": latency
#         }
#         self.review_widgets.setdefault(
#             employee_name,
#             {"absences": [],"permissions": [],"latencies":[],"early_leaves":[],"need_reviews":[]}
#         )["latencies"].append(row_data)

#         return row
    
#     def create_early_leave_row(self, leave,employee_name):
        
#         text = (
#                 f"{leave['date']} | "
#                 f"{leave['checkout_time']} | "
#                 f"{leave['minutes']} min"
#             )

#         row = QWidget()

#         layout = QHBoxLayout(row)

#         date_label = QLabel(text)

#         allowed_checkbox = QCheckBox("Allowed")

#         deduction_spin = QSpinBox()
#         deduction_spin.setMaximum(100000)
#         deduction_spin.setValue(300)

#         notes_edit = QLineEdit()

#         def allowed_changed(state):

#             if allowed_checkbox.isChecked():
#                 deduction_spin.setValue(100)
#             else:
#                 deduction_spin.setValue(300)

#         allowed_checkbox.stateChanged.connect(
#             allowed_changed
#         )

#         layout.addWidget(date_label)
#         layout.addWidget(allowed_checkbox)
#         layout.addWidget(deduction_spin)
#         layout.addWidget(notes_edit)

#         row_data = {
#             "allowed_checkbox": allowed_checkbox,
#             "deduction_spin": deduction_spin,
#             "notes_edit": notes_edit,
#             "early_leave": leave
#         }
#         self.review_widgets.setdefault(
#             employee_name,
#             {"absences": [],"permissions": [],"latencies":[],"early_leaves":[],"need_reviews":[]}
#         )["early_leaves"].append(row_data)

#         return row

#     def create_need_review_row(self, review,employee_name):

#         text = (
#                 f"{review['date']} | "
#                 f"{review['reason']}"
#             )

#         row = QWidget()

#         layout = QHBoxLayout(row)

#         date_label = QLabel(text)

#         allowed_checkbox = QCheckBox("Allowed")

#         deduction_spin = QSpinBox()
#         deduction_spin.setMaximum(100000)
#         deduction_spin.setValue(300)

#         notes_edit = QLineEdit()

#         def allowed_changed(state):

#             if allowed_checkbox.isChecked():
#                 deduction_spin.setValue(100)
#             else:
#                 deduction_spin.setValue(300)

#         allowed_checkbox.stateChanged.connect(
#             allowed_changed
#         )

#         layout.addWidget(date_label)
#         layout.addWidget(allowed_checkbox)
#         layout.addWidget(deduction_spin)
#         layout.addWidget(notes_edit)

#         row_data = {
#             "allowed_checkbox": allowed_checkbox,
#             "deduction_spin": deduction_spin,
#             "notes_edit": notes_edit,
#             "need_review": review
#         }
#         self.review_widgets.setdefault(
#             employee_name,
#             {"absences": [],"permissions": [],"latencies":[],"early_leaves":[],"need_reviews":[]}
#         )["need_reviews"].append(row_data)

#         return row

from data.globals import attendance_result_dict
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QTabWidget,
    QWidget,
    QLabel,
    QGroupBox,
    QFormLayout,
    QScrollArea,
    QPushButton,
    QDialogButtonBox,
    QHBoxLayout,
    QCheckBox,
    QSpinBox,
    QLineEdit,
    QComboBox          # <-- added for points dropdown
)


class AttendanceReviewDialog(QDialog):

    def __init__(self, attendance_data, parent=None):
        super().__init__(parent)
        self.review_widgets = {}
        self.attendance_data = attendance_data

        self.setWindowTitle("Attendance Review")
        self.resize(1000, 700)

        main_layout = QVBoxLayout(self)

        self.tabs = QTabWidget()

        for employee_name, employee_data in attendance_data.items():

            employee_widget = self.build_employee_tab(
                employee_name,
                employee_data["summary"]
            )

            self.tabs.addTab(
                employee_widget,
                employee_name
            )

        main_layout.addWidget(self.tabs)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok |
            QDialogButtonBox.Cancel
        )

        buttons.accepted.connect(self.get_review_data)
        buttons.rejected.connect(self.reject)

        main_layout.addWidget(buttons)

    def get_converted_review_widgets(self):
        """
        Returns a deep copy of review_widgets where:
        - deduction_points  -> float(combo.currentText())
        - spin_deduction    -> spin_box.value()
        - notes_edit        -> .text()
        All other fields (absence, permission, etc.) are left unchanged.
        """
        converted = {}
        for employee, categories in self.review_widgets.items():
            converted[employee] = {}
            for category, rows in categories.items():
                converted[employee][category] = []
                for row in rows:
                    new_row = {}
                    for key, value in row.items():
                        if key == "deduction_points":
                            # combo box: get the selected text and convert to float
                            new_row[key] = float(value.currentText())
                        elif key == "spin_deduction":
                            # spin box: get the integer value
                            new_row[key] = value.value()
                        elif key == "notes_edit":
                            new_row[key] = value.text()
                        else:
                            new_row[key] = value   # e.g. absence, permission, latency, etc.
                    converted[employee][category].append(new_row)
        return converted

    def get_review_data(self):
        converted_data = self.get_converted_review_widgets()
        attendance_result_dict.update(converted_data)
        self.accept()

    def build_employee_tab(self, employee_name, summary):

        self.review_widgets[f"{employee_name}"] = {
            "absences": [],
            "permissions": [],
            "latencies": [],
            "early_leaves": [],
            "need_reviews": []
        }

        container = QWidget()
        layout = QVBoxLayout(container)

        layout.addWidget(
            QLabel(f"<h2>{employee_name}</h2>")
        )

        layout.addWidget(
            self.create_absences_group(
                summary["absent_days"], employee_name
            )
        )

        layout.addWidget(
            self.create_permissions_group(
                summary["permissions"], employee_name
            )
        )

        layout.addWidget(
            self.create_latencies_group(
                summary["latencies"], employee_name
            )
        )

        layout.addWidget(
            self.create_early_leaves_group(
                summary["early_leaves"], employee_name
            )
        )

        layout.addWidget(
            self.create_needs_review_group(
                summary["needs_review"], employee_name
            )
        )

        layout.addStretch()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(container)

        wrapper = QWidget()
        wrapper_layout = QVBoxLayout(wrapper)
        wrapper_layout.addWidget(scroll)

        return wrapper

    def create_absences_group(self, absences, employee_name):

        group = QGroupBox(
            f"Absences ({len(absences)})"
        )

        form = QFormLayout(group)

        for absence in absences:

            form.addRow(
                self.create_absence_row(absence, employee_name)
            )

        return group

    def create_permissions_group(self, permissions, employee_name):

        group = QGroupBox(
            f"Permissions ({len(permissions)})"
        )

        form = QFormLayout(group)

        for permission in permissions:

            form.addRow(
                self.create_permission_row(permission, employee_name)
            )

        return group

    def create_latencies_group(self, latencies, employee_name):

        group = QGroupBox(
            f"Latencies ({len(latencies)})"
        )

        form = QFormLayout(group)

        for latency in latencies:

            form.addRow(
                self.create_latency_row(latency, employee_name)
            )

        return group

    def create_early_leaves_group(self, early_leaves, employee_name):

        group = QGroupBox(
            f"Early Leaves ({len(early_leaves)})"
        )

        form = QFormLayout(group)

        for leave in early_leaves:

            form.addRow(
                self.create_early_leave_row(leave, employee_name)
            )

        return group

    def create_needs_review_group(self, reviews, employee_name):

        group = QGroupBox(
            f"Needs Review ({len(reviews)})"
        )

        form = QFormLayout(group)

        for review in reviews:

            form.addRow(
                self.create_need_review_row(review, employee_name)
            )

        return group

    # ---------- Helper to build a points combo box ----------
    def _create_points_combo(self):
        combo = QComboBox()
        points = ["0", "0.25", "0.50", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]
        combo.addItems(points)
        combo.setCurrentIndex(0)   # default "0"
        return combo

    # ---------- Row builders (all identical except the data key) ----------
    def create_absence_row(self, absence, employee_name):

        row = QWidget()
        layout = QHBoxLayout(row)

        date_label = QLabel(absence["date"])

        # Points combo (replaces the checkbox)
        points_combo = self._create_points_combo()

        # Spin box for deduction (labelled "spin deduction")
        spin_deduction = QSpinBox()
        spin_deduction.setMaximum(100000)
        spin_deduction.setValue(0)      # default 0

        notes_edit = QLineEdit()

        layout.addWidget(date_label)
        layout.addWidget(points_combo)
        layout.addWidget(spin_deduction)
        layout.addWidget(notes_edit)

        row_data = {
            "deduction_points": points_combo,
            "spin_deduction": spin_deduction,
            "notes_edit": notes_edit,
            "absence": absence
        }
        self.review_widgets.setdefault(
            employee_name,
            {"absences": [], "permissions": [], "latencies": [], "early_leaves": [], "need_reviews": []}
        )["absences"].append(row_data)

        return row

    def create_permission_row(self, permission, employee_name):

        text = (
            f"{permission['start']} → "
            f"{permission['end']} "
            f"({permission['duration_minutes']} min)"
        )

        row = QWidget()
        layout = QHBoxLayout(row)

        date_label = QLabel(text)

        points_combo = self._create_points_combo()

        spin_deduction = QSpinBox()
        spin_deduction.setMaximum(100000)
        spin_deduction.setValue(0)

        notes_edit = QLineEdit()

        layout.addWidget(date_label)
        layout.addWidget(points_combo)
        layout.addWidget(spin_deduction)
        layout.addWidget(notes_edit)

        row_data = {
            "deduction_points": points_combo,
            "spin_deduction": spin_deduction,
            "notes_edit": notes_edit,
            "permission": permission
        }
        self.review_widgets.setdefault(
            employee_name,
            {"absences": [], "permissions": [], "latencies": [], "early_leaves": [], "need_reviews": []}
        )["permissions"].append(row_data)

        return row

    def create_latency_row(self, latency, employee_name):

        text = (
            f"{latency['date']} | "
            f"{latency['checkin_time']} | "
            f"{latency['minutes']} min"
        )

        row = QWidget()
        layout = QHBoxLayout(row)

        date_label = QLabel(text)

        points_combo = self._create_points_combo()

        spin_deduction = QSpinBox()
        spin_deduction.setMaximum(100000)
        spin_deduction.setValue(0)

        notes_edit = QLineEdit()

        layout.addWidget(date_label)
        layout.addWidget(points_combo)
        layout.addWidget(spin_deduction)
        layout.addWidget(notes_edit)

        row_data = {
            "deduction_points": points_combo,
            "spin_deduction": spin_deduction,
            "notes_edit": notes_edit,
            "latency": latency
        }
        self.review_widgets.setdefault(
            employee_name,
            {"absences": [], "permissions": [], "latencies": [], "early_leaves": [], "need_reviews": []}
        )["latencies"].append(row_data)

        return row

    def create_early_leave_row(self, leave, employee_name):

        text = (
            f"{leave['date']} | "
            f"{leave['checkout_time']} | "
            f"{leave['minutes']} min"
        )

        row = QWidget()
        layout = QHBoxLayout(row)

        date_label = QLabel(text)

        points_combo = self._create_points_combo()

        spin_deduction = QSpinBox()
        spin_deduction.setMaximum(100000)
        spin_deduction.setValue(0)

        notes_edit = QLineEdit()

        layout.addWidget(date_label)
        layout.addWidget(points_combo)
        layout.addWidget(spin_deduction)
        layout.addWidget(notes_edit)

        row_data = {
            "deduction_points": points_combo,
            "spin_deduction": spin_deduction,
            "notes_edit": notes_edit,
            "early_leave": leave
        }
        self.review_widgets.setdefault(
            employee_name,
            {"absences": [], "permissions": [], "latencies": [], "early_leaves": [], "need_reviews": []}
        )["early_leaves"].append(row_data)

        return row

    def create_need_review_row(self, review, employee_name):

        text = (
            f"{review['date']} | "
            f"{review['reason']}"
        )

        row = QWidget()
        layout = QHBoxLayout(row)

        date_label = QLabel(text)

        points_combo = self._create_points_combo()

        spin_deduction = QSpinBox()
        spin_deduction.setMaximum(100000)
        spin_deduction.setValue(0)

        notes_edit = QLineEdit()

        layout.addWidget(date_label)
        layout.addWidget(points_combo)
        layout.addWidget(spin_deduction)
        layout.addWidget(notes_edit)

        row_data = {
            "deduction_points": points_combo,
            "spin_deduction": spin_deduction,
            "notes_edit": notes_edit,
            "need_review": review
        }
        self.review_widgets.setdefault(
            employee_name,
            {"absences": [], "permissions": [], "latencies": [], "early_leaves": [], "need_reviews": []}
        )["need_reviews"].append(row_data)

        return row