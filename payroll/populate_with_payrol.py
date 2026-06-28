import json

import pandas as pd

from data.globals import attendance_result_dict


def calculate_target_bonus(achieved, target):
    """
    Placeholder.
    You will implement the actual formula later.
    """
    return 0


def update_data_dict_with_payroll(target_file):

    # -------------------------
    # Load employee mapping
    # -------------------------

    with open(
        "data/employee_mapping.json",
        "r",
        encoding="utf-8"
    ) as f:

        employee_mapping = json.load(f)

    # Reverse mapping
    # {"nour":"nor ahmed"}

    reverse_mapping = {
        value.strip().lower(): key
        for key, value in employee_mapping.items()
    }

    # -------------------------
    # Read both sheets
    # -------------------------

    excel = pd.ExcelFile(target_file)

    for sheet_name in excel.sheet_names:

        df = pd.read_excel(
            excel,
            sheet_name=sheet_name
        )

        # Skip title row
        for _, row in df.iloc[1:].iterrows():

            name = str(row.iloc[0]).strip()

            target = float(row.iloc[1])

            achieved = float(row.iloc[2])

            zero_accepts = float(row.iloc[3])

            target_bonus = calculate_target_bonus(
                achieved,
                target
            )

            zero_accepts_deductions = (
                25 * zero_accepts
            )

            # -------------------------
            # Find attendance name
            # -------------------------

            attendance_name = reverse_mapping.get(
                name.lower()
            )

            if attendance_name is None:
                continue

            if attendance_name not in attendance_result_dict:
                continue

            employee = attendance_result_dict[
                attendance_name
            ]

            employee["target_bonus"] = target_bonus

            employee["zero_accepts_deductions"] = (
                zero_accepts_deductions
            )

            employee["target"] = target

            employee["achieved"] = achieved