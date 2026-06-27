import sys
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QFileDialog,
    QTabWidget          
)
from payroll.attendance import analyze_attendance
from ui.attendance_review import AttendanceReviewDialog
from ui.employee_management_tab import EmployeeManagementTab


class MainWindow(QWidget):

    def __init__(self):
        super().__init__()

        self.attendance_file = ""
        self.target_file = ""

        self.setWindowTitle("Salary Calculator")
        self.resize(600, 400)

        # --- Create Tab Widget ---
        tab_widget = QTabWidget()

        # --- Tab 1: Attendance  ---
        attendance_tab = QWidget()
        layout = QVBoxLayout(attendance_tab)

        # Attendance file selection
        self.lbl_attendance = QLabel("No attendance file selected")
        self.btn_attendance = QPushButton("Select Attendance Excel")
        self.btn_attendance.clicked.connect(self.select_attendance_file)

        # Target file selection
        self.lbl_target = QLabel("No target file selected")
        self.btn_target = QPushButton("Select Target Excel")
        self.btn_target.clicked.connect(self.select_target_file)

        self.btn_analyze = QPushButton("Analyze")
        self.btn_analyze.clicked.connect(self.analyze_attendance_method)

        layout.addWidget(self.lbl_attendance)
        layout.addWidget(self.btn_attendance)
        layout.addWidget(self.lbl_target)
        layout.addWidget(self.btn_target)
        layout.addWidget(self.btn_analyze)
        layout.addStretch()

        tab_widget.addTab(attendance_tab, "Attendance")

        # --- Tab 2: Employee Management ---
        self.employee_tab = EmployeeManagementTab()
        tab_widget.addTab(self.employee_tab, "Employee Mapping")

        # --- Set the main layout, with the tab widget ---
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(tab_widget)
        self.setLayout(main_layout)   

    def analyze_attendance_method(self):
        attendance_data = analyze_attendance(self.attendance_file)
        dialog = AttendanceReviewDialog(attendance_data, self)
        dialog.exec()

    def select_attendance_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Attendance Excel File",
            "",
            "Excel Files (*.xlsx *.xls)"
        )
        if file_path:
            self.attendance_file = file_path
            self.lbl_attendance.setText(file_path)

    def select_target_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Target Excel File",
            "",
            "Excel Files (*.xlsx *.xls)"
        )
        if file_path:
            self.target_file = file_path
            self.lbl_target.setText(file_path)