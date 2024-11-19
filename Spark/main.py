from pyspark.sql import SparkSession
from pyspark.sql.functions import col, explode


# Create a SparkSession
spark = SparkSession.builder.appName("SystemAnalysis").getOrCreate()

# Stream from Kafka
df = spark.readStream.format("kafka")\
    .option("kafka.bootstrap.servers", "192.168.1.100:9092")\
    .option("subscribe", "test")\
    .option("startingOffsets", "earliest")\
    .load()

# json_file_path = "./Kafka/Producer/data.json"
# df = spark.read.json(json_file_path, multiLine=True)

# # Select required fields from the DataFrame
# # boot_time
# selected_fields_df = df.select(
#     df.basic_info.computer_name.alias("computer_name"),
#     df.basic_info.serial_number.alias("serial_number"),
#     df.basic_info.OS.alias("os"),
#     df.basic_info.system_model.alias("system_model"),
#     df.basic_info.system_type.alias("system_type"),
# )

# selected_fields_df.show(truncate=False)

# # Stop the Spark session
# spark.stop()
