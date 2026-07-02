# import json

# import pandas as pd

# from data.globals import attendance_result_dict

# def calculate_target_bonus(achieved, target):
#     """
#     Placeholder.
#     You will implement the actual formula later.
#     """
#     return 0


# def update_data_dict_with_payroll(target_file):

#     # -------------------------
#     # Load employee mapping
#     # -------------------------

#     with open(
#         "data/employee_mapping.json",
#         "r",
#         encoding="utf-8"
#     ) as f:

#         employee_mapping = json.load(f)

#     # Reverse mapping
#     # {"nour":"nor ahmed"}

#     reverse_mapping = {
#         value.strip().lower(): key
#         for key, value in employee_mapping.items()
#     }

#     # -------------------------
#     # Read both sheets
#     # -------------------------

#     excel = pd.ExcelFile(target_file)

#     for sheet_name in excel.sheet_names:

#         df = pd.read_excel(
#             excel,
#             sheet_name=sheet_name
#         )

#         # Skip title row
#         for _, row in df.iloc[1:].iterrows():

#             name = str(row.iloc[0]).strip()

#             target = float(row.iloc[1])

#             achieved = float(row.iloc[2])

#             zero_accepts = float(row.iloc[3])

#             target_bonus = calculate_target_bonus(
#                 achieved,
#                 target
#             )

#             zero_accepts_deductions = (
#                 0.25 * zero_accepts
#             )

#             # -------------------------
#             # Find attendance name
#             # -------------------------

#             attendance_name = reverse_mapping.get(
#                 name.lower()
#             )

#             if attendance_name is None:
#                 continue

#             if attendance_name not in attendance_result_dict:
#                 continue

#             employee = attendance_result_dict[
#                 attendance_name
#             ]

#             employee["target_bonus"] = target_bonus

#             employee["zero_accepts_deductions"] = (
#                 zero_accepts_deductions
#             )

#             employee["target"] = target

#             employee["achieved"] = achieved

import json
import pandas as pd
from data.globals import attendance_result_dict


def safe_float(value):
    """Convert a value to float, handling empty strings and dashes."""
    if isinstance(value, str):
        value = value.strip()
        if value == "" or value == "-":
            return 0.0
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0


def update_data_dict_with_payroll(target_file):
    # -------------------------
    # Load employee mapping
    # -------------------------
    with open("data/employee_mapping.json", "r", encoding="utf-8") as f:
        employee_mapping = json.load(f)

    # Reverse mapping: value -> key (both lowercased and stripped)
    reverse_mapping = {
        value.strip().lower(): key
        for key, value in employee_mapping.items()
    }

    # -------------------------
    # Read all sheets
    # -------------------------
    excel = pd.ExcelFile(target_file)

    for sheet_index, sheet_name in enumerate(excel.sheet_names):
        df = pd.read_excel(excel, sheet_name=sheet_name)

        # Skip title row (row 0 is assumed to be header)
        for _, row in df.iloc[1:].iterrows():
            name = str(row.iloc[0]).strip()

            # Determine which sheet we are processing
            if sheet_index == 0:  # First sheet: target-based bonus
                target = safe_float(row.iloc[1])
                achieved = safe_float(row.iloc[2])
                zero_accepts = safe_float(row.iloc[3])

                # Compute target bonus and explanation
                if target > 0:
                    perc = (achieved / target) * 100
                    if perc < 60:
                        target_bonus = 0
                        explain = f"Achieved {perc:.1f}% of target (<60%) → 0"
                    elif 60 <= perc < 80:
                        target_bonus = 2000 * 0.6  # 1200
                        explain = f"Achieved {perc:.1f}% of target (60%–<80%) → 2000 × 0.6 = {target_bonus:.0f}"
                    elif 80 <= perc < 100:
                        target_bonus = 2000 * 0.8  # 1200 (same as previous per spec)
                        explain = f"Achieved {perc:.1f}% of target (80%–<100%) → 2000 × 0.8 = {target_bonus:.0f}"
                    else:  # >= 100%
                        target_bonus = 2000 * (perc / 100)
                        explain = f"Achieved {perc:.1f}% of target (>=100%) → 2000 × {perc/100:.2f} = {target_bonus:.0f}"
                else:
                    target_bonus = 0
                    explain = "Target is zero or invalid → 0"

            else:  # Second sheet (and any others): hard-coded ranges
                # Target is ignored; achieved is the active count
                achieved = safe_float(row.iloc[2])
                zero_accepts = safe_float(row.iloc[3])

                # Determine bonus based on active count ranges
                if achieved < 25:
                    target_bonus = 0
                    explain = f"Active count {achieved:.0f} < 25 → 0"
                elif 25 <= achieved <= 34:
                    target_bonus = 500
                    explain = f"Active count {achieved:.0f} (25–34) → 500"
                elif 35 <= achieved <= 44:
                    target_bonus = 1100
                    explain = f"Active count {achieved:.0f} (35–44) → 1100"
                elif 45 <= achieved <= 54:
                    target_bonus = 1800
                    explain = f"Active count {achieved:.0f} (45–54) → 1800"
                else:
                    target_bonus = 0
                    explain = f"Active count {achieved:.0f} outside ranges → 0"

            # Deduction for zero accepts
            zero_accepts_deductions = 0.25 * zero_accepts

            # -------------------------
            # Find attendance name
            # -------------------------
            attendance_name = reverse_mapping.get(name.lower())
            if attendance_name is None:
                continue

            if attendance_name not in attendance_result_dict:
                continue

            employee = attendance_result_dict[attendance_name]

            # Store computed values
            employee["target_bonus"] = target_bonus
            employee["target_bonus_explain"] = explain          # <-- NEW
            employee["zero_accepts_deductions"] = zero_accepts_deductions
            # Also store target and achieved for reference (second sheet stores achieved only)
            employee["target"] = target if sheet_index == 0 else None
            employee["achieved"] = achieved


# final shape
# attendance_result_dict = {

#     "employee_name": {

#         # ============================
#         # Attendance Review
#         # ============================

#         "absences": [
#             {
#                 "absence": {
#                     "date": "2026-06-02"
#                 },
#                 "deduction_points": 2.0,
#                 "spin_deduction": 200,
#                 "notes_edit": "Disallowed absence"
#             }
#         ],

#         "permissions": [
#             {
#                 "permission": {
#                     "start": datetime,
#                     "end": datetime,
#                     "duration_minutes": 120
#                 },
#                 "deduction_points": 0,
#                 "spin_deduction": 0,
#                 "notes_edit": ""
#             }
#         ],

#         "latencies": [
#             {
#                 "latency": {
#                     "date": "2026-06-01",
#                     "checkin_time": "09:50",
#                     "minutes": 70
#                 },
#                 "deduction_points": 0,
#                 "spin_deduction": 0,
#                 "notes_edit": ""
#             }
#         ],

#         "early_leaves": [
#             {
#                 "early_leave": {
#                     "date": "2026-06-09",
#                     "checkout_time": "16:39",
#                     "minutes": 46
#                 },
#                 "deduction_points": 0,
#                 "spin_deduction": 0,
#                 "notes_edit": ""
#             }
#         ],

#         "need_reviews": [
#             {
#                 "need_review": {
#                     "date": "2026-06-08",
#                     "reason": "Consecutive حضور"
#                 },
#                 "deduction_points": 0,
#                 "spin_deduction": 0,
#                 "notes_edit": ""
#             }
#         ],

#         # ============================
#         # Manual Adjustments
#         # ============================

#         "manually_additions": [
#             {
#                 "value": 50,
#                 "points": 0,
#                 "note": "Excellent work"
#             }
#         ],

#         "manually_deductions": [
#             {
#                 "value": 100,
#                 "points": 0.5,
#                 "note": "Phone usage"
#             }
#         ],

#         # ============================
#         # Payroll Data
#         # ============================

#         "fixed_salary": 3000,

#         "target": 40,

#         "achieved": 20,

#         "target_bonus": 0,

#         "target_bonus_explain":
#             "Achieved 50% of target (<60%) → 0",

#         "zero_accepts_deductions": 1.5
#     }
# }