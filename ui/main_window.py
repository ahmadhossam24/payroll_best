from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QFileDialog
)
from payroll.attendance import analyze_attendance
from ui.attendance_review import AttendanceReviewDialog

class MainWindow(QWidget):

    def __init__(self):
        super().__init__()

        self.file_path = ""

        self.setWindowTitle("Salary Calculator")
        self.resize(500, 200)

        layout = QVBoxLayout()

        self.lbl_file = QLabel("No file selected")

        self.btn_select = QPushButton(
            "Select Fingerprint Excel"
        )

        self.btn_analyze = QPushButton(
            "Analyze"
        )

        self.btn_select.clicked.connect(
            self.select_file
        )

        self.btn_analyze.clicked.connect(
            self.analyze_attendance_method
        )

        layout.addWidget(self.lbl_file)
        layout.addWidget(self.btn_select)
        layout.addWidget(self.btn_analyze)

        self.setLayout(layout)

    def analyze_attendance_method(self):
        # print(analyze_attendance(self.file_path))
        attendance_data = analyze_attendance(
            self.file_path
        )

        dialog = AttendanceReviewDialog(
            attendance_data,
            self
        )

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