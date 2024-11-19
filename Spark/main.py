from pyspark.sql import SparkSession
from pyspark.sql.functions import col, explode


spark = SparkSession.builder.appName("SystemAnalysis").getOrCreate()

data_path = "./Kafka/Producer/data.json"
df = spark.read.json(data_path, multiLine=True)

flattened_df = df.select(
    col("basic_info.computer_name").alias("ComputerName"),
    col("basic_info.OS").alias("OS"),
    col("cpu.name").alias("CPUName"),
    col("cpu.cores").alias("CPUCores"),
    col("cpu.ultilization").alias("CPUUtilization"),
    explode("gpu").alias("gpu_info"),
    col("network.ip").alias("IP"),
    col("network.mac").alias("MAC"),
    col("ram.total").alias("TotalRAM"),
    col("ram.used").alias("UsedRAM"),
    col("ram.percentage").alias("RAMPercentage"),
    explode("ram.details").alias("RAMDetails"),
    col("battery.percent").alias("BatteryPercent"),
    explode("physical_disks.disk_list").alias("DiskList"),
    col("physical_disks.total_memory_used").alias("TotalDiskMemoryUsed")
)

flattened_df.show(vertical=True)
flattened_df.printSchema()

# Average CPU Utilization
avg_cpu_util = flattened_df.groupBy("ComputerName").agg({"CPUUtilization": "avg"})