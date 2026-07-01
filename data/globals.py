attendance_result_dict={}
#example
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