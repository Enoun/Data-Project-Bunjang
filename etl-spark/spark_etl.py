from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from datetime import datetime, timedelta
import re
import os
import pandas as pd
import subprocess

# SparkSession 생성
spark = SparkSession.builder \
    .appName("ETL Project") \
    .config("spark.some.config.option", "some-value") \
    .getOrCreate()

# 오늘 날짜와 7일 전 날짜
end_date = datetime.now()
start_date = end_date - timedelta(days=7)
date_format_str = "%Y%m%d"

# HDFS에서 최근 7일치 파일 목록을 가져오는 함수
def get_recent_files(hdfs_base_path, start_date, end_date):
    result = subprocess.run(["hdfs", "dfs", "-ls", hdfs_base_path], capture_output=True, text=True)
    files = result.stdout.splitlines()
    recent_files = []
    date_pattern = re.compile(r"(\d{8})")  # YYYYMMDD 날짜 패턴 [다시 보기]

    for file_info in files:
        match = date_pattern.search(file_info)
        if match:
            file_date_str = match.group(1)
            file_date = datetime.strptime(file_date_str, date_format_str)
            if start_date <= file_date <= end_date:
                file_path = file_info.split()[-1]
                recent_files.append(file_path)

    return recent_files


# 데이터 수집, 전처리 및 저장을 진행하는 함수
def process_and_save_data(category_name, hdfs_base_path):
    # 최근 7일치 파일 목록 가져오기
    recent_files = get_recent_files(hdfs_base_path, start_date, end_date)
    print("7일치 목록 가져오기 성공")

    if recent_files:
        df = spark.read.csv(recent_files, header=True, inferSchema=True)
        df = df.withColumnRenamed("수집된 시간", "collected_time") \
            .withColumnRenamed("상품명", "product_name") \
            .withColumnRenamed("가격", "price") \
            .withColumnRenamed("시간", "time") \
            .withColumnRenamed("지역 정보", "location_info") \
            .withColumn("collected_time", to_date("collected_time", "yyyy-MM-dd")) \
            .withColumn("price", regexp_replace("price", ",", "").cast("int")) \
            .dropDuplicates()

        df_filtered = df.filter(df["time"] != "AD")
        df_filtered = df_filtered.filter(~df["product_name"].rlike("구합니다|구함|원합니다|원함|삽니다|삼|사요|구매"))
        df_filtered = df_filtered.drop("time")

        # 저장 경로 설정 및 저장
        output_path = f"hdfs://localhost:9000/user/dataPipeline/processedData/{category_name}_processed_{end_date.strftime('%Y%m%d')}.csv"
        df_filtered.write.csv(output_path, mode="overwrite", header=True)
        print(f"{output_path}에 저장완료")

        local_file_path = os.path.join(local_output_dir, f"{category_name}_processed_{end_date.strftime('%Y%m%d')}.csv")
        df_filtered.toPandas().to_csv(local_file_path, mode="W", header=True, encoding="utf-8-sig", index=False)
        print(f"{category_name} 데이터 전처리 및 저장 완료{local_file_path}")

# 로컬 파일 저장 경로 (shared 폴더)
local_output_dir = "/shared/processedData"
os.makedirs(local_output_dir, exist_ok=True)

# 남성 및 여성 데이터 각각 처리
process_and_save_data("mans", "hdfs://localhost:9000/user/dataPipeline/collectedData/mans_category/")
print("성공-MAN")
process_and_save_data("woman", "hdfs://localhost:9000/user/dataPipeline/collectedData/woman_category/")
print("성공-WOMAN")

# SUCCESS 파일 제거
subprocess.run(["hdfs", "dfs", "-rm", "-f", "/user/dataPipeline/processedData/_SUCCESS"])

spark.stop()