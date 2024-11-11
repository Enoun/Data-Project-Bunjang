from pyspark.sql import SparkSession
from pyspark.sql.functions import *
import os
import pandas as pd
import subprocess
from datetime import datetime

# SparkSession 생성
spark = SparkSession.builder \
    .appName("ETL Project") \
    .config("spark.some.config.option", "some-value") \
    .getOrCreate()

hdfs_path = "hdfs://localhost:9000/user/dataPipeline/collectedData/mans_category1.csv"

df = spark.read.csv(hdfs_path, header=True, inferSchema=True)

df = df.withColumnRenamed("수집된 시간", "collected_time") \
       .withColumnRenamed("상품명", "product_name") \
       .withColumnRenamed("가격", "price") \
       .withColumnRenamed("시간", "time") \
       .withColumnRenamed("지역 정보", "location_info")
df = df.withColumn("collected_time", date_format("collected_time", "yyyy-MM-dd"))
df = df.withColumn("price", regexp_replace("price", ",", "").cast("int"))
df = df.dropDuplicates() # 중복제거

# 광고 제거(AD), 구매글 필터링
df_filtered = df.filter(df["time"] != "AD")
df_filtered = df.filter(~df["product_name"].isin("구합니다", "구함"))
df_filtered = df_filtered.drop("time")

df_filtered.show(5)
df_filtered.printSchema()

current_date = datetime.now().strftime('%Y%m%d')

# 전처리된 데이터프레임을 HDFS에 저장
output_path = f"hdfs://localhost:9000/user/dataPipeline/processedData/processedData_{current_date}.csv"

# 데이터 저장 append는 새로 추가 overwrite는 덮어쓰기
df_filtered.write.csv(output_path, mode="append", header=True)

# SUCCESS 파일 제거
subprocess.run(["hdfs", "dfs", "-rm", "/user/dataPipeline/processedData/_SUCCESS"])

spark.stop()