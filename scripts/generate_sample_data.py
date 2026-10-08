"""Generate a synthetic LMS extract that matches the raw CSV contract.

The real course dataset is not redistributed. This file reproduces its shape, formats
and the data quality problems the pipeline is designed to handle:
duplicates, missing keys, in-progress courses and completion-before-enrolment rows.

Usage: python scripts/generate_sample_data.py --rows 500 --out data/sample/LMS_sample.csv
"""

import argparse
import csv
import random
from datetime import date, timedelta
from pathlib import Path

COURSES = [
    ("C101", "Algebra I", "Grade 9"),
    ("C102", "Biology", "Grade 10"),
    ("C103", "World History", "Grade 9"),
    ("C104", "Chemistry", "Grade 11"),
    ("C105", "English Literature", "Grade 12"),
    ("C106", "Computer Science", "Grade 11"),
    ("C107", "Geometry", "Grade 10"),
    ("C108", "Economics", "Grade 12"),
]
FIRST = ["Ava", "Liam", "Mia", "Noah", "Zoe", "Ethan", "Isla", "Leo", "Aria", "Kai", "Ruby", "Max"]
LAST = ["Nguyen", "Smith", "Patel", "Brown", "Wilson", "Kumar", "Taylor", "Lee", "Martin", "Singh"]
GRADES = ["A", "B", "C", "D", "F"]


def fmt(d):
    return f"{d.month}/{d.day}/{d.year}" if d else ""


def make_row(rng, student_id):
    course_id, course_name, grade_level = rng.choice(COURSES)
    enrolled = date(2023, 1, 1) + timedelta(days=rng.randint(0, 240))
    status = rng.choices(["Completed", "In-progress", "Dropped"], [0.7, 0.2, 0.1])[0]
    completed = enrolled + timedelta(days=rng.randint(20, 160)) if status == "Completed" else None
    quiz, assign, project = (round(rng.uniform(40, 100), 1) for _ in range(3))
    scores = [round(rng.uniform(40, 100)) for _ in range(4)]
    return {
        "Student_ID": student_id,
        "Name": f"{rng.choice(FIRST)} {rng.choice(LAST)}",
        "Age": rng.randint(14, 18),
        "Gender": rng.choice(["Male", "Female", "Other"]),
        "Grade_Level": grade_level,
        "Course_ID": course_id,
        "Course_Name": course_name,
        "Enrollment_Date": fmt(enrolled),
        "Completion_Date": fmt(completed),
        "Status": status,
        "Final_Grade": rng.choice(GRADES) if completed else "",
        "Attendance_Rate": round(rng.uniform(50, 100), 1),
        "Time_Spent_on_Course_hrs": round(rng.uniform(5, 120), 1),
        "Assignments_Completed": rng.randint(0, 12),
        "Quizzes_Completed": rng.randint(0, 10),
        "Forum_Posts": rng.randint(0, 30),
        "Messages_Sent": rng.randint(0, 50),
        "Quiz_Average_Score": quiz,
        "Assignment_Scores": str(scores),
        "Assignment_Average_Score": assign,
        "Project_Score": project,
        "Extra_Credit": round(rng.uniform(0, 5), 1),
        "Overall_Performance": round((quiz + assign + project) / 3, 1),
        "Feedback_Score": round(rng.uniform(1, 5), 1),
        "Parent_Involvement": rng.choice(["Low", "Medium", "High"]),
        "Demographic_Group": rng.choice(["Urban", "Suburban", "Rural"]),
        "Internet_Access": rng.choice(["Yes", "No"]),
        "Learning_Disabilities": rng.choice(["Yes", "No", "No", "No"]),
        "Preferred_Learning_Style": rng.choice(["Visual", "Auditory", "Kinesthetic", "Reading/Writing"]),
        "Language_Proficiency": rng.choice(["Basic", "Intermediate", "Advanced"]),
        "Participation_Rate": rng.choice(["Low", "Medium", "High"]),
        "Completion_Time_Days": "",
        "Performance_Score": "",
        "Course_Completion_Rate": "",
    }


def generate(rows, seed=42):
    rng = random.Random(seed)
    data = [make_row(rng, f"S{rng.randint(1000, 1000 + rows // 2):05d}") for _ in range(rows)]
    # Inject the data quality issues the pipeline must handle
    data += [dict(r) for r in rng.sample(data, k=max(1, rows // 50))]  # exact duplicates
    for r in rng.sample(data, k=max(1, rows // 100)):
        r["Student_ID"] = ""  # missing critical key
    for r in rng.sample([r for r in data if r["Completion_Date"]], k=max(1, rows // 100)):
        r["Completion_Date"], r["Enrollment_Date"] = r["Enrollment_Date"], r["Completion_Date"]
    rng.shuffle(data)
    return data


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", type=int, default=500)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default="data/sample/LMS_sample.csv")
    args = ap.parse_args()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="") as fh:
        rows = generate(args.rows, args.seed)
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
