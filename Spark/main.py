from pyspark.sql import SparkSession
from pyspark.sql.functions import col, explode, expr, lit, sum, unix_timestamp


# Create a SparkSession
spark = SparkSession.builder.appName("SystemAnalysis").getOrCreate()

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

# # Average CPU Utilization
# avg_cpu_util = selected_fields_df.groupBy("ComputerName").agg({"CPUUtilization": "avg"})
# # RAM Usage Summary
# ram_usage = selected_fields_df.groupBy("ComputerName").agg({"TotalRAM": "max", "UsedRAM": "max", "RAMPercentage": "max"})
# # Disk Usage and Partition Analysis
# disk_usage = selected_fields_df.select("ComputerName", "DiskList.size", "TotalDiskMemoryUsed").groupBy("ComputerName").sum("size")

# Stop the Spark session
spark.stop()
