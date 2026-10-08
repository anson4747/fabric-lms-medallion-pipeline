from datetime import date

import pytest

from lms_pipeline import transforms as t
from lms_pipeline.schema import DIM_STUDENT_COLUMNS, FACT_COLUMNS, RAW_SCHEMA

RUN_DATE = "2026-10-03"


def raw_row(**overrides):
    row = {f.name: None for f in RAW_SCHEMA.fields}
    row.update(
        Student_ID="S1",
        Name="Ava Nguyen",
        Age=16,
        Gender="Female",
        Grade_Level="Grade 10",
        Course_ID="C101",
        Course_Name="Algebra I",
        Enrollment_Date="1/10/2023",
        Completion_Date="3/1/2023",
        Status="Completed",
        Final_Grade="A",
        Quiz_Average_Score=80.0,
        Assignment_Average_Score=70.0,
        Project_Score=90.0,
    )
    row.update(overrides)
    return tuple(row[f.name] for f in RAW_SCHEMA.fields)


@pytest.fixture
def make_df(spark):
    def _make(*rows):
        return spark.createDataFrame(list(rows), RAW_SCHEMA)

    return _make


def silver_of(make_df, *rows):
    return t.to_silver(t.to_bronze(t.to_landing(make_df(*rows), RUN_DATE), RUN_DATE))


def test_bronze_keeps_one_row_per_business_key(make_df):
    df = make_df(raw_row(), raw_row(Name="Ava N."), raw_row(Course_ID="C102"))
    bronze = t.to_bronze(t.to_landing(df, RUN_DATE), RUN_DATE)
    assert bronze.count() == 2
    assert {r.Processing_Date for r in bronze.collect()} == {date(2026, 10, 3)}


def test_silver_drops_rows_missing_critical_keys(make_df):
    silver = silver_of(make_df, raw_row(), raw_row(Student_ID=None, Course_ID="C102"), raw_row(Course_ID="C103", Enrollment_Date=None))
    assert [r.Course_ID for r in silver.collect()] == ["C101"]


def test_silver_parses_dates_and_computes_completion_days(make_df):
    row = silver_of(make_df, raw_row()).first()
    assert row.Enrollment_Date == date(2023, 1, 10)
    assert row.Completion_Date == date(2023, 3, 1)
    assert row.Completion_Time_Days == 50
    assert row.Course_Completion_Rate == "On-Time"


def test_in_progress_course_is_kept_with_null_completion(make_df):
    """Regression: a 12/31/9999 placeholder used to inflate Average Completion Days."""
    row = silver_of(make_df, raw_row(Completion_Date=None, Status=None, Final_Grade=None)).first()
    assert row.Completion_Date is None
    assert row.Completion_Time_Days is None
    assert row.Course_Completion_Rate == "In-Progress"
    assert row.Status == "In-progress"
    assert row.Final_Grade == "N/A"


def test_delayed_completion_over_threshold(make_df):
    row = silver_of(make_df, raw_row(Completion_Date="6/30/2023")).first()
    assert row.Completion_Time_Days == 171
    assert row.Course_Completion_Rate == "Delayed"


def test_completion_before_enrolment_is_rejected(make_df):
    silver = silver_of(make_df, raw_row(Enrollment_Date="3/1/2023", Completion_Date="1/10/2023"))
    assert silver.count() == 0


def test_performance_score_weighting(make_df):
    row = silver_of(make_df, raw_row()).first()
    assert row.Performance_Score == pytest.approx(80 * 0.2 + 70 * 0.2 + 90 * 0.1)


def test_defaults_fill_missing_descriptive_values(make_df):
    row = silver_of(make_df, raw_row(Gender=None, Age=None, Internet_Access=None)).first()
    assert (row.Gender, row.Age, row.Internet_Access) == ("Unknown", 0, "Unknown")


def test_dimensions_are_unique_on_business_key(make_df):
    """Regression: duplicate dimension keys made Delta MERGE fail on re-runs."""
    silver = silver_of(
        make_df,
        raw_row(),
        raw_row(Course_ID="C102", Course_Name="Biology"),
        raw_row(Student_ID="S2", Course_ID="C102", Course_Name="Biology"),
    )
    students = t.dim_student(silver)
    courses = t.dim_course(silver)
    assert students.columns == DIM_STUDENT_COLUMNS
    assert students.count() == students.select("Student_ID").distinct().count() == 2
    assert courses.count() == courses.select("Course_ID").distinct().count() == 2


def test_fact_grain_is_student_course(make_df):
    silver = silver_of(make_df, raw_row(), raw_row(Course_ID="C102"), raw_row(Student_ID="S2"))
    fact = t.fact_student_performance(silver)
    assert fact.columns == FACT_COLUMNS
    assert fact.count() == fact.select("Student_ID", "Course_ID").distinct().count() == 3
