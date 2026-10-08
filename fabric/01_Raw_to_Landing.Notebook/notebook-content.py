# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {}
# META }

# MARKDOWN ********************

# ## 01 Raw to Landing

# PARAMETERS CELL ********************

today_file = 'file'#'LMS_09-01-2023.csv'
processed_date = '9999-09-09'#'2024-09-17'

source_account = 'fabric122'
source_container = 'fabricproject'
src_relative_path = 'raw'
destination_account  = 'fabric122'
destination_container = ''

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************


adls_path = 'abfss://%s@%s.dfs.core.windows.net/%s' % (source_container,source_account,src_relative_path)
print(adls_path)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

latest_path = f"{adls_path}/{today_file}"
print(latest_path)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

from pyspark.sql.functions import lit
df = spark.read.csv(path = latest_path,header=True,inferSchema=True)
if df.count()>1:
    print("The file has data")
    df_new = df.withColumn("processing_date",lit(processed_date))
    df_new.write.format('csv').option('header','true').partitionBy('processing_date').mode('append').save(f'abfss://{destination_container}@{destination_account}.dfs.core.windows.net/landing/')
    print("Data written to the landing zone successfully")
else:
    print("File contains only header")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
