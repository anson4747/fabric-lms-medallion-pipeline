# Engineering review

After finishing the build I reviewed the definitions committed from the Dev workspace to Azure DevOps and fixed the issues below in the exported items under `fabric/`. Each fix that changes data has a regression test in `tests/`.

## Fixed

### 1. Ingestion loop passed static parameters
`PL_01_Raw_to_Landing` iterated over the new files but passed the literal values `today_file = "file"` and `processed_date = "9999-09-09"` to the notebook, so every iteration read `raw/file` and wrote to a placeholder partition.

**Fix:** `today_file = @item().name`, `processed_date = @formatDateTime(utcNow(),'yyyy-MM-dd')`.

### 2. Hard-coded and invalid workspace names
The orchestrator passed `workspace = "NA"` to the Gold notebook, so it tried to read `abfss://NA@onelake...`. Bronze and Silver were hard-coded to `fabric_DEV`, so a run in Prod would write to the Dev Lakehouses.

**Fix:** `workspace_name`, `storage_account` and `storage_container` are pipeline parameters, passed to every notebook. `scripts/validate_fabric_items.py` now fails CI if a pipeline passes a literal workspace name.

### 3. Placeholder completion date skewed metrics
Silver filled missing `Completion_Date` with `12/31/9999`. For in-progress courses this produced `Completion_Time_Days` of roughly 2.9 million, inflating the `Average Completion Days` measure on the report, and labelled every in-progress course as `Delayed`.

**Fix:** completion stays null, `Completion_Time_Days` is null for in-progress rows (so `AVERAGE` ignores them), and `Course_Completion_Rate` has an explicit `In-Progress` value. The consistency filter keeps null completions. Days are computed with `datediff` rather than casting a date interval.

Tests: `test_in_progress_course_is_kept_with_null_completion`, `test_delayed_completion_over_threshold`.

### 4. Non-unique MERGE sources in Gold
`dim_student` was built from every Silver row of the day, so a student enrolled in two courses produced two source rows for the same key. On first load both were inserted (duplicate dimension rows). On later loads Delta raises *multiple source rows matched*. The same applied to `dim_course`.

**Fix:** deduplicate on the business key before each MERGE (`Student_ID`, `Course_ID`, and `(Student_ID, Course_ID)` for the fact).

Test: `test_dimensions_are_unique_on_business_key`.

## Recommended next steps

| Area | Recommendation |
|---|---|
| Modelling | `Grade_Level` is a student attribute but sits in `dim_course`; move it to `dim_student` or a bridge table |
| Business rules | `Performance_Score` weights sum to 0.5, so the score tops out at 50. Confirm the intended weights with the business, or normalise to 100 |
| Naming | `Course_Completion_Rate` holds a category, not a rate; rename to `Completion_Timeliness` |
| Slowly changing dimensions | Dimensions are type 1 (overwrite). Use type 2 if history of student attributes matters |
| Reuse | Package `src/lms_pipeline` as a wheel and attach it to a Fabric Environment so notebooks import the tested functions instead of duplicating them |
| Data quality | Add row count and null rate checks, or Materialized Lake View constraints, between layers and fail the pipeline on breach |
| Orchestration | Add failure alerts from the pipeline (Teams or email activity) |
