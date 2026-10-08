"""Schemas shared by every layer of the LMS medallion pipeline."""

from pyspark.sql.types import (
    DoubleType,
    IntegerType,
    StringType,
    StructField,
    StructType,
)

# Raw / landing CSV contract. Dates arrive as M/d/yyyy strings and are typed in Silver.
RAW_SCHEMA = StructType(
    [
        StructField("Student_ID", StringType(), True),
        StructField("Name", StringType(), True),
        StructField("Age", IntegerType(), True),
        StructField("Gender", StringType(), True),
        StructField("Grade_Level", StringType(), True),
        StructField("Course_ID", StringType(), True),
        StructField("Course_Name", StringType(), True),
        StructField("Enrollment_Date", StringType(), True),
        StructField("Completion_Date", StringType(), True),
        StructField("Status", StringType(), True),
        StructField("Final_Grade", StringType(), True),
        StructField("Attendance_Rate", DoubleType(), True),
        StructField("Time_Spent_on_Course_hrs", DoubleType(), True),
        StructField("Assignments_Completed", IntegerType(), True),
        StructField("Quizzes_Completed", IntegerType(), True),
        StructField("Forum_Posts", IntegerType(), True),
        StructField("Messages_Sent", IntegerType(), True),
        StructField("Quiz_Average_Score", DoubleType(), True),
        StructField("Assignment_Scores", StringType(), True),
        StructField("Assignment_Average_Score", DoubleType(), True),
        StructField("Project_Score", DoubleType(), True),
        StructField("Extra_Credit", DoubleType(), True),
        StructField("Overall_Performance", DoubleType(), True),
        StructField("Feedback_Score", DoubleType(), True),
        StructField("Parent_Involvement", StringType(), True),
        StructField("Demographic_Group", StringType(), True),
        StructField("Internet_Access", StringType(), True),
        StructField("Learning_Disabilities", StringType(), True),
        StructField("Preferred_Learning_Style", StringType(), True),
        StructField("Language_Proficiency", StringType(), True),
        StructField("Participation_Rate", StringType(), True),
        StructField("Completion_Time_Days", IntegerType(), True),
        StructField("Performance_Score", DoubleType(), True),
        StructField("Course_Completion_Rate", DoubleType(), True),
    ]
)

BUSINESS_KEY = ["Student_ID", "Course_ID"]
CRITICAL_COLUMNS = ["Student_ID", "Course_ID", "Enrollment_Date"]

DIM_STUDENT_COLUMNS = [
    "Student_ID",
    "Name",
    "Age",
    "Gender",
    "Demographic_Group",
    "Internet_Access",
    "Learning_Disabilities",
    "Preferred_Learning_Style",
    "Language_Proficiency",
    "Parent_Involvement",
]

DIM_COURSE_COLUMNS = ["Course_ID", "Course_Name", "Grade_Level"]

FACT_COLUMNS = [
    "Student_ID",
    "Course_ID",
    "Enrollment_Date",
    "Completion_Date",
    "Status",
    "Final_Grade",
    "Attendance_Rate",
    "Time_Spent_on_Course_hrs",
    "Assignments_Completed",
    "Quizzes_Completed",
    "Forum_Posts",
    "Messages_Sent",
    "Quiz_Average_Score",
    "Assignment_Scores",
    "Assignment_Average_Score",
    "Project_Score",
    "Extra_Credit",
    "Overall_Performance",
    "Feedback_Score",
    "Completion_Time_Days",
    "Performance_Score",
    "Course_Completion_Rate",
    "Processing_Date",
]

# Defaults applied in Silver. Completion_Date is deliberately absent: null means "in progress".
SILVER_DEFAULTS = {
    "Age": 0,
    "Gender": "Unknown",
    "Status": "In-progress",
    "Final_Grade": "N/A",
    "Attendance_Rate": 0.0,
    "Time_Spent_on_Course_hrs": 0.0,
    "Assignments_Completed": 0,
    "Quizzes_Completed": 0,
    "Forum_Posts": 0,
    "Messages_Sent": 0,
    "Quiz_Average_Score": 0.0,
    "Assignment_Average_Score": 0.0,
    "Project_Score": 0.0,
    "Extra_Credit": 0.0,
    "Overall_Performance": 0.0,
    "Feedback_Score": 0.0,
    "Parent_Involvement": "Unknown",
    "Demographic_Group": "Unknown",
    "Internet_Access": "Unknown",
    "Learning_Disabilities": "Unknown",
    "Preferred_Learning_Style": "Unknown",
    "Language_Proficiency": "Unknown",
    "Participation_Rate": "Unknown",
}

ON_TIME_THRESHOLD_DAYS = 90
