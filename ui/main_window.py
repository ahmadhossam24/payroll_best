import sys
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QFileDialog,
    QTabWidget          # correctly imported
)
from payroll.attendance import analyze_attendance
from ui.attendance_review import AttendanceReviewDialog
from ui.employee_management_tab import EmployeeManagementTab


class MainWindow(QWidget):

    def __init__(self):
        super().__init__()

        self.file_path = ""

        self.setWindowTitle("Salary Calculator")
        self.resize(600, 400)

        # --- Create Tab Widget ---
        tab_widget = QTabWidget()

        # --- Tab 1: Attendance (your existing UI) ---
        attendance_tab = QWidget()
        layout = QVBoxLayout(attendance_tab)   # ✅ Layout is now attached to the tab

        self.lbl_file = QLabel("No file selected")
        self.btn_select = QPushButton("Select Fingerprint Excel")
        self.btn_analyze = QPushButton("Analyze")

        self.btn_select.clicked.connect(self.select_file)
        self.btn_analyze.clicked.connect(self.analyze_attendance_method)

        layout.addWidget(self.lbl_file)
        layout.addWidget(self.btn_select)
        layout.addWidget(self.btn_analyze)
        layout.addStretch()

        tab_widget.addTab(attendance_tab, "Attendance")

        # --- Tab 2: Employee Management (your new tab) ---
        self.employee_tab = EmployeeManagementTab()
        tab_widget.addTab(self.employee_tab, "Employee Mapping")

        # --- Set the main layout once, with the tab widget ---
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(tab_widget)
        self.setLayout(main_layout)   # ✅ Only one setLayout

        # ❌ Remove the extra self.setLayout(layout) – it's gone

    # ---------- The rest of your methods remain exactly as they were ----------
    def analyze_attendance_method(self):
        attendance_data = analyze_attendance(self.file_path)
        dialog = AttendanceReviewDialog(attendance_data, self)
        dialog.exec()

    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Excel File",
            "",
            "Excel Files (*.xlsx *.xls)"
        )
        if file_path:
            self.file_path = file_path
            self.lbl_file.setText(file_path)