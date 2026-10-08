"""Pure PySpark transformations for each medallion layer.

These functions mirror the logic in the Fabric notebooks under ``fabric/`` so it can be
unit tested locally and in CI without a Fabric capacity. Storage (OneLake / ADLS) and
Delta MERGE are handled by the notebooks; everything here is DataFrame in, DataFrame out.
"""

from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from .schema import (
    BUSINESS_KEY,
    CRITICAL_COLUMNS,
    DIM_COURSE_COLUMNS,
    DIM_STUDENT_COLUMNS,
    FACT_COLUMNS,
    ON_TIME_THRESHOLD_DAYS,
    SILVER_DEFAULTS,
)

DATE_FORMAT = "M/d/yyyy"


# ---------------------------------------------------------------- Landing
def to_landing(raw: DataFrame, processing_date: str) -> DataFrame:
    """Stamp a raw extract with the processing date used to partition the landing zone."""
    return raw.withColumn("processing_date", F.lit(processing_date))


# ---------------------------------------------------------------- Bronze
def to_bronze(landing: DataFrame, processing_date: str) -> DataFrame:
    """One row per (Student_ID, Course_ID) for the day, ready to MERGE into bronze_data."""
    return landing.drop("processing_date").dropDuplicates(BUSINESS_KEY).withColumn("Processing_Date", F.to_date(F.lit(processing_date)))


# ---------------------------------------------------------------- Silver
def clean(bronze: DataFrame) -> DataFrame:
    """Remove duplicates and rows missing critical keys, then apply defaults."""
    return bronze.dropDuplicates().dropna(subset=CRITICAL_COLUMNS).fillna(SILVER_DEFAULTS)


def standardise_dates(df: DataFrame) -> DataFrame:
    return df.withColumn("Enrollment_Date", F.to_date("Enrollment_Date", DATE_FORMAT)).withColumn(
        "Completion_Date", F.to_date("Completion_Date", DATE_FORMAT)
    )


def enforce_date_consistency(df: DataFrame) -> DataFrame:
    """Keep in-progress rows (null completion) and drop completion-before-enrolment rows."""
    return df.filter(F.col("Completion_Date").isNull() | (F.col("Completion_Date") >= F.col("Enrollment_Date")))


def add_business_metrics(df: DataFrame) -> DataFrame:
    days = F.datediff("Completion_Date", "Enrollment_Date")
    return (
        df.withColumn("Completion_Time_Days", days)
        .withColumn(
            "Performance_Score",
            F.col("Quiz_Average_Score") * 0.2 + F.col("Assignment_Average_Score") * 0.2 + F.col("Project_Score") * 0.1,
        )
        .withColumn(
            "Course_Completion_Rate",
            F.when(days.isNull(), "In-Progress").when(days <= ON_TIME_THRESHOLD_DAYS, "On-Time").otherwise("Delayed"),
        )
    )


def to_silver(bronze: DataFrame) -> DataFrame:
    return add_business_metrics(enforce_date_consistency(standardise_dates(clean(bronze))))


# ---------------------------------------------------------------- Gold
def dim_student(silver: DataFrame) -> DataFrame:
    return silver.select(*DIM_STUDENT_COLUMNS).dropDuplicates(["Student_ID"])


def dim_course(silver: DataFrame) -> DataFrame:
    return silver.select(*DIM_COURSE_COLUMNS).dropDuplicates(["Course_ID"])


def fact_student_performance(silver: DataFrame) -> DataFrame:
    return silver.select(*FACT_COLUMNS).dropDuplicates(BUSINESS_KEY)
