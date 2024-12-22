import os
import warnings
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, explode, expr, lit, sum, unix_timestamp

###################################################################################################
# Download winutils https://github.com/cdarlint/winutils/raw/master/hadoop-3.3.5/bin/winutils.exe #
# Copy exe into C:\hadoop\bin                                                                     #
####################################################################################################
warnings.simplefilter(action='ignore', category=FutureWarning)
os.environ['HADOOP_HOME'] = "C:\\hadoop"
connection_string = "mongodb+srv://minh150555:BjYWmSxUg9Ier4pk@devconnector.xamuv.mongodb.net/"

# Create a SparkSession
spark = SparkSession.builder.appName("SystemAnalysis") \
    .config("spark.mongodb.read.connection.uri", connection_string) \
    .config("spark.mongodb.write.connection.uri", connection_string) \
    .config('spark.jars.packages', 'org.mongodb.spark:mongo-spark-connector_2.12:10.4.0') \
    .getOrCreate()

# # Stream from Kafka
# df = spark.readStream.format("kafka")\
#     .option("kafka.bootstrap.servers", "localhost:9092")\
#     .option("subscribe", "test")\
#     .option("startingOffsets", "earliest")\
#     .load()

json_file_path = "data.json"
df = spark.read.json(json_file_path, multiLine=True)

exploded_df = df.select(
    explode(col("physical_disks.disk_list")).alias("disk"))
total_disk_size_df = exploded_df.select(
    sum(col("disk.size")).alias("total_disk_size"))
total_disk_size = total_disk_size_df.collect()[0]["total_disk_size"]


# Select required fields from the DataFrame
selected_fields_df = df.select(
    # Assume that "computer_name" is unique
    df.basic_info.computer_name.alias("bi_computer_name"),
    df.basic_info.serial_number.alias("bi_serial_number"),
    df.basic_info.boot_time.alias("bi_boot_time"),
    df.cpu.uptime.alias("cpu_uptime"),
    df.cpu.processes.alias("cpu_processes"),
    df.cpu.ultilization.alias("cpu_ultilization"),
    df.ram.total.alias("ram_total"),
    df.ram.used.alias("ram_used"),
    df.battery.percent.alias("battery_percent"),
    lit(total_disk_size).alias("total_disk_size"),
    df.physical_disks.total_memory_used.alias("disk_total_used")
)

selected_fields_df = selected_fields_df.withColumn(
    "uptime_seconds",
    expr("""
        split(cpu_uptime, ':')[0] * 86400 + -- Days to seconds
        split(cpu_uptime, ':')[1] * 3600 +  -- Hours to seconds
        split(cpu_uptime, ':')[2] * 60 +    -- Minutes to seconds
        split(cpu_uptime, ':')[3]           -- Remaining seconds
    """).cast("int")
)

selected_fields_df = selected_fields_df.withColumn(
    "timestamp",
    (unix_timestamp(col("bi_boot_time")) + col("uptime_seconds")).cast("timestamp")
)

selected_fields_df.show(truncate=False, vertical=True)

# Write DataFrame to MongoDB
selected_fields_df.write \
    .format("mongodb") \
    .mode("append") \
    .option("database", "big_data") \
    .option("collection", "spark") \
    .save()


# Stop the Spark session
spark.stop()
