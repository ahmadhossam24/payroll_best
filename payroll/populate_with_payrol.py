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
    # -------------------------
    # Read all sheets
    # -------------------------
    excel = pd.ExcelFile(target_file)

    for sheet_index, sheet_name in enumerate(excel.sheet_names):
        df = pd.read_excel(excel, sheet_name=sheet_name)

        # Skip title row (row 0 is assumed to be header)
        for _, row in df.iloc[0:].iterrows():
            name = str(row.iloc[0]).strip().lower()
            print(name)
            # Determine which sheet we are processing
            if sheet_index == 0:  # First sheet: target-based bonus
                target = safe_float(row.iloc[1])
                achieved = safe_float(row.iloc[2])
                zero_accepts = safe_float(row.iloc[3]) if pd.notna(row.iloc[3]) else 0.0

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
                print(f"{name} achieved",achieved)
                zero_accepts = safe_float(row.iloc[3]) if pd.notna(row.iloc[3]) else 0.0

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
            attendance_name = next(
                (key for key, val in employee_mapping.items() if val["target_sheet_name"] == name),
                None
            )
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