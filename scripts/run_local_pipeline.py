"""Run the Landing -> Bronze -> Silver -> Gold transformations locally on a CSV extract.

Mirrors the Fabric pipeline without a Fabric capacity. Each layer is written as Parquet
under the output folder so it can be inspected. In Fabric the same logic MERGEs into
Delta tables in LH_Bronze, LH_Silver and LH_Gold.

Usage: python scripts/run_local_pipeline.py --input data/sample/LMS_sample.csv --out .local_lakehouse
"""

import argparse
import sys
from datetime import date
from pathlib import Path

from pyspark.sql import SparkSession

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from lms_pipeline import transforms as t  # noqa: E402
from lms_pipeline.schema import RAW_SCHEMA  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="data/sample/LMS_sample.csv")
    ap.add_argument("--out", default=".local_lakehouse")
    ap.add_argument("--date", default=date.today().isoformat())
    args = ap.parse_args()

    spark = (
        SparkSession.builder.master("local[*]")
        .appName("lms-medallion-local")
        .config("spark.ui.enabled", "false")
        .config("spark.sql.session.timeZone", "UTC")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("ERROR")
    out = Path(args.out)

    raw = spark.read.csv(args.input, header=True, schema=RAW_SCHEMA)
    landing = t.to_landing(raw, args.date)
    bronze = t.to_bronze(landing, args.date)
    silver = t.to_silver(bronze)
    gold = {
        "dim_student": t.dim_student(silver),
        "dim_course": t.dim_course(silver),
        "fact_student_performance": t.fact_student_performance(silver),
    }

    layers = {"bronze/bronze_data": bronze, "silver/silver_data": silver}
    layers.update({f"gold/{k}": v for k, v in gold.items()})
    print(f"{'layer':<32}{'rows':>8}")
    print(f"{'raw':<32}{raw.count():>8}")
    for name, df in layers.items():
        df.write.mode("overwrite").parquet(str(out / name))
        print(f"{name:<32}{df.count():>8}")

    fact = gold["fact_student_performance"]
    print("\nCompletion categories:")
    fact.groupBy("Course_Completion_Rate").count().orderBy("Course_Completion_Rate").show()
    spark.stop()


if __name__ == "__main__":
    main()
