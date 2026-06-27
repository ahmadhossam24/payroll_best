from dataclasses import dataclass, field
import pandas as pd
from collections import defaultdict
from datetime import datetime, timedelta
import json

WORK_START_HOUR = 8
WORK_START_MINUTE = 40

WORK_END_HOUR = 17
WORK_END_MINUTE = 25

WORKING_DAYS = {0,1,2,3,5,6}

def build_employee_summary(days):

    result = {
        "absent_days": [],
        "permissions": [],
        "latencies": [],
        "early_leaves": [],
        "needs_review": []
    }

    result["absent_days"] = calculate_absent_days(days)

    for date, summary in days.items():

        if summary.latency_minutes > 0:

            result["latencies"].append({
                "date": date,
                "checkin_time":
                    summary.first_in.strftime("%H:%M"),
                "minutes":
                    summary.latency_minutes
            })

        if summary.early_leave_minutes > 0:

            result["early_leaves"].append({
                "date": date,
                "checkout_time":
                    summary.last_out.strftime("%H:%M"),
                "minutes":
                    summary.early_leave_minutes
            })

        result["permissions"].extend(
            summary.permissions
        )

        if summary.needs_review:

            result["needs_review"].append({
                "date": date,
                "reason": summary.review_reason
            })

    return result

def get_working_dates(start_date, end_date):

    result = []

    current = start_date

    while current <= end_date:

        if current.weekday() in WORKING_DAYS:
            result.append(current)

        current += timedelta(days=1)

    return result

def calculate_absent_days(employee_days):

    if not employee_days:
        return []

    present_dates = {
        datetime.strptime(
            day,
            "%Y-%m-%d"
        ).date()
        for day in employee_days.keys()
    }

    start_date = min(present_dates)
    end_date = max(present_dates)

    expected_dates = get_working_dates(
        start_date,
        end_date
    )

    absences = []

    for work_day in expected_dates:

        if work_day not in present_dates:

            absences.append({
                "date": work_day.isoformat()
            })

    return absences

def parse_datetime(text):

    text = text.strip()

    text = text.replace("ص", "AM")
    text = text.replace("م", "PM")

    return datetime.strptime(
        text,
        "%d/%m/%Y %I:%M %p"
    )

def analyze_attendance(excel_file):

    records = load_fingerprints(excel_file)

    grouped = group_records(records)

    result = {}

    for employee, days in grouped.items():

        employee_days = analyze_employee(days)

        result[employee] = {
            "days": employee_days,
            "summary": build_employee_summary(
                employee_days
            )
        }

    return result

def analyze_employee(days):

    summaries = {}

    for date, records in days.items():

        summaries[date] = analyze_day(
            records,
            date
        )

    return summaries

def analyze_day(records, date):

    records = sorted(
        records,
        key=lambda r: r["datetime"]
    )

    summary = DaySummary(date=date)

    summary.raw_records = records

    if not records:
        return summary

    # -------------------------
    # Missing checkin/checkout
    # -------------------------

    if records[0]["action"] == "انصراف":
        summary.missing_checkin = True
        summary.needs_review = True

    if records[-1]["action"] == "حضور":
        summary.missing_checkout = True
        summary.needs_review = True

    # -------------------------
    # Odd fingerprints count
    # -------------------------

    if len(records) % 2 != 0:
        summary.needs_review = True

    # -------------------------
    # First IN / Last OUT
    # -------------------------

    for record in records:

        action = record["action"]

        if action == "حضور":

            if summary.first_in is None:
                summary.first_in = record["datetime"]

        elif action == "انصراف":

            summary.last_out = record["datetime"]

    # -------------------------
    # Sequence Analysis
    # -------------------------

    for i in range(len(records) - 1):

        current = records[i]
        nxt = records[i + 1]

        current_action = current["action"]
        next_action = nxt["action"]

        # Consecutive actions
        if current_action == next_action:

            delta = (
                nxt["datetime"] -
                current["datetime"]
            ).total_seconds() / 60

            # Duplicate fingerprint
            if delta <= 5:

                summary.duplicate_fingerprints = True

            else:

                summary.needs_review = True

                if summary.review_reason:
                    summary.review_reason += " | "

                summary.review_reason += (
                    f"Consecutive '{current_action}' "
                    f"at {current['datetime'].strftime('%H:%M')} "
                    f"and {nxt['datetime'].strftime('%H:%M')}"
                )

        # Permission
        elif (
            current_action == "انصراف"
            and
            next_action == "حضور"
        ):

            duration = (
                nxt["datetime"] -
                current["datetime"]
            )

            summary.permissions.append({
                "start": current["datetime"],
                "end": nxt["datetime"],
                "duration_minutes": int(
                    duration.total_seconds() / 60
                )
            })

    # -------------------------
    # Latency
    # -------------------------

    if summary.first_in:

        expected_start = summary.first_in.replace(
            hour=WORK_START_HOUR,
            minute=WORK_START_MINUTE,
            second=0,
            microsecond=0
        )

        if summary.first_in > expected_start:

            summary.latency_minutes = int(
                (
                    summary.first_in -
                    expected_start
                ).total_seconds() / 60
            )

    # -------------------------
    # Early Leave
    # -------------------------

    if summary.last_out:

        expected_end = summary.last_out.replace(
            hour=WORK_END_HOUR,
            minute=WORK_END_MINUTE,
            second=0,
            microsecond=0
        )

        if summary.last_out < expected_end:

            summary.early_leave_minutes = int(
                (
                    expected_end -
                    summary.last_out
                ).total_seconds() / 60
            )

    return summary

def group_records(records):

    result = defaultdict(
        lambda: defaultdict(list)
    )

    for record in records:

        employee = record["name"]

        date_str = record["datetime"].date().isoformat()

        result[employee][date_str].append(record)

    return result

def load_fingerprints(excel_file):
    df = pd.read_excel(excel_file)

    records = []

    # Load employee mapping 
    with open("data/employee_mapping.json", "r") as f:
        employee_mapping = json.load(f)

    for _, row in df.iterrows():
        name = str(row.iloc[2]).strip()   # column C

        # Only proceed if name exists in mapping keys
        if name.lower() in employee_mapping.keys():

            records.append({
                "name": str(row.iloc[2]).strip(),      # column C
                "datetime": parse_datetime(row.iloc[3]),              # column D
                "action": str(row.iloc[4]).strip()    # column E
            })

    return records

@dataclass
class DaySummary:
    date: str

    first_in: datetime | None = None
    last_out: datetime | None = None

    permissions: list = field(default_factory=list)

    latency_minutes: int = 0
    early_leave_minutes: int = 0

    duplicate_fingerprints: bool = False

    missing_checkin: bool = False
    missing_checkout: bool = False

    needs_review: bool = False
    review_reason: str = ""

    raw_records: list = field(default_factory=list)


