import sys
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QFileDialog,
    QTabWidget, 
    QLineEdit, 
    QMessageBox,
    QDateEdit     
)
from PySide6.QtCore import QDate

from payroll.attendance import analyze_attendance
from payroll.populate_with_payrol import update_data_dict_with_payroll
from ui.attendance_review import AttendanceReviewDialog
from ui.employee_management_tab import EmployeeManagementTab
from data.globals import attendance_result_dict
from ui.final_review import FinalDialog
from ui.manual_add_ded import ManualAddDedDialog
import re

class MainWindow(QWidget):

    def __init__(self):
        super().__init__()

        self.attendance_file = ""
        self.target_file = ""

        self.setWindowTitle("حساب المرتبات")
        self.resize(600, 400)

        # --- Create Tab Widget ---
        tab_widget = QTabWidget()

        # --- Tab 1: Attendance  ---
        attendance_tab = QWidget()
        layout = QVBoxLayout(attendance_tab)

        # Attendance file selection
        self.lbl_attendance = QLabel("لم يتم اختيار ملف")
        self.btn_attendance = QPushButton("اختر ملف الحضور والانصراف")
        self.btn_attendance.clicked.connect(self.select_attendance_file)

        # Target file selection
        self.lbl_target = QLabel("لم يتم اختيار ملف")
        self.btn_target = QPushButton("اختر شيت الاكتيف")
        self.btn_target.clicked.connect(self.select_target_file)

        # label for the date range
        lbl_range = QLabel("احسب المرتبات من الى")

        # start and end date pickers (calendar popup, display format YYYY-MM-DD)
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDisplayFormat("yyyy-MM-dd")

        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDisplayFormat("yyyy-MM-dd")

        # compute previous month first and last day
        today = QDate.currentDate()
        prev = today.addMonths(-1)
        start_of_prev = QDate(prev.year(), prev.month(), 1)
        end_of_prev = QDate(prev.year(), prev.month(), prev.daysInMonth())

        # set defaults to previous month range
        self.start_date_edit.setDate(start_of_prev)
        self.end_date_edit.setDate(end_of_prev)

        self.btn_analyze = QPushButton("ابدأ")
        self.btn_analyze.clicked.connect(self.analyze_attendance_method)

        layout.addWidget(self.lbl_attendance)
        layout.addWidget(self.btn_attendance)
        layout.addWidget(self.lbl_target)
        layout.addWidget(self.btn_target)
        layout.addWidget(lbl_range)
        layout.addWidget(self.start_date_edit)
        layout.addWidget(self.end_date_edit)
        layout.addWidget(self.btn_analyze)
        layout.addStretch()

        tab_widget.addTab(attendance_tab, "الرئيسية")

        # --- Tab 2: Employee Management ---
        self.employee_tab = EmployeeManagementTab()
        tab_widget.addTab(self.employee_tab, "تجهيز اسماء الموظفين")

        # --- Set the main layout, with the tab widget ---
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(tab_widget)
        self.setLayout(main_layout)   

    def analyze_attendance_method(self):
        start_date = self.start_date_edit.date()
        end_date = self.end_date_edit.date()

        if not (start_date.isValid() and end_date.isValid()) or start_date > end_date:
            QMessageBox.warning(self, "لم يتم ادخال تواريخ", "اختر التواريخ")
            return

        # convert to strings in the requested format
        start_str = start_date.toString("yyyy-MM-dd")
        end_str = end_date.toString("yyyy-MM-dd")
        
        attendance_data = analyze_attendance(self.attendance_file,start_str, end_str)
        print(attendance_data)
        dialog = AttendanceReviewDialog(attendance_data, self)
        if dialog.exec():
            dialog = ManualAddDedDialog(self)
            if dialog.exec():
                update_data_dict_with_payroll(self.target_file)
                # print(attendance_result_dict)
                dialog = FinalDialog(start_str,end_str,self)
                dialog.exec()

        
    def select_attendance_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "اختر ملف الحضور والانصراف",
            "",
            "Excel Files (*.xlsx *.xls)"
        )
        if file_path:
            self.attendance_file = file_path
            self.lbl_attendance.setText(file_path)

    def select_target_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "اختر شيت الاكتيف",
            "",
            "Excel Files (*.xlsx *.xls)"
        )
        if file_path:
            self.target_file = file_path
            self.lbl_target.setText(file_path)

    def _is_valid_iso_date(self, s: str) -> bool:
        if not s:
            return False
        # simple YYYY-MM-DD regex, ensures numeric and valid basic format
        return bool(re.match(r"^\d{4}-\d{2}-\d{2}$", s))