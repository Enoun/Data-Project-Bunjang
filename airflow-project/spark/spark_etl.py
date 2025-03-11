from pyspark.sql import SparkSession
from pyspark.sql.functions import col, explode, to_timestamp, lit
from datetime import datetime, timedelta
import subprocess
import pytz
import os

# Spark 세션 생성
spark = SparkSession.builder \
    .appName("BrandFiltering") \
    .getOrCreate()


def get_kst_now():
    kst_tz = pytz.timezone("Asia/Seoul")
    return datetime.now(kst_tz).strftime("%Y-%m-%d %H:%M:%S")


def get_filtered_files(hdfs_base_path, selected_brands):
    """
    HDFS 상의 디렉터리에서 특정 브랜드 이름이 들어간 파일만 선택
    예:  stussy_products.json, supreme_products.json 등이 있다고 가정
    """
    result = subprocess.run(
        ["hdfs", "dfs", "-ls", hdfs_base_path],
        capture_output=True, text=True
    )
    files = result.stdout.splitlines()

    filtered_files = []
    for line in files:
        tokens = line.split()
        if len(tokens) < 8:
            continue
        file_path = tokens[-1]
        for brand in selected_brands:
            # 예: "stussy_products.json" substring 확인
            if f"{brand}_products.json" in file_path:
                filtered_files.append(file_path)
    return filtered_files

def filter_and_save_json(hdfs_input_dir, local_output_dir, selected_brands):
    spark = SparkSession.builder \
        .appName("FilterAndSaveJson") \
        .getOrCreate()

    # 최근 7일 전 시각
    seven_days_ago = datetime.now() - timedelta(days=7)

    # 1) 원하는 브랜드들 파일 목록
    brand_files = get_filtered_files(hdfs_input_dir, selected_brands)
    print("브랜드 파일 목록:", brand_files)

    if not brand_files:
        print("해당 브랜드의 JSON 파일이 없습니다.")
        spark.stop()
        return

    # 2) HDFS의 JSON을 불러오고, 수집 시각 필터 적용
    #    한 번에 여러 파일 로드 가능
    df = spark.read.option("multiline", "true").json(brand_files)

    # (선택) brand explode
    if "brands" in df.columns:
        df = df.withColumn("brand", explode(col("brands")))

    # collected_timestamp → Timestamp 변환 (있다고 가정)
    if "collected_timestamp" in df.columns:
        df = df.withColumn(
            "collected_ts",
            to_timestamp(col("collected_timestamp"), "yyyy-MM-dd HH:mm:ss")
        )
        # 7일 필터
        # spark에서 datetime -> string 비교는 불안정하니 timestamp 변환이 안전
        # lit(seven_days_ago_str) 형태보다 lit() + timestamp가 더 안전
        # 다만 spark>=3.0부터 timestampLiteral 가능
        df = df.filter(col("collected_ts") >= lit(seven_days_ago.strftime("%Y-%m-%d %H:%M:%S")))
    else:
        print("collected_timestamp 컬럼이 없어, 최근 7일 필터 미적용.")

    # (선택) 필요한 컬럼들만
    # 여기서는 전체 JSON 유지하려면 그대로
    # df_filtered = df.select("pid", "brand", "name", "price_updates", "collected_timestamp", ...)

    # 3) Spark DataFrame → Python list[dict] 변환
    #    3-1) df.toJSON() -> 각 row를 JSON 문자열로
    #    3-2) collect() -> driver로 가져와 Python list
    #    3-3) json.loads() -> 실제 dict
    #    (데이터 양이 아주 많다면 collect()에 주의)
    json_rows = df.toJSON().collect()  # row 수가 매우 클 경우, OutOfMemory 가능

    python_dicts = [json.loads(row) for row in json_rows]
    print(f"가져온 레코드 수: {len(python_dicts)}")

    # 4) 로컬 디렉터리에 저장
    os.makedirs(local_output_dir, exist_ok=True)

    # (예) 하나의 JSON 파일로 통합
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"filtered_{'_'.join(selected_brands)}_{timestamp_str}.json"
    output_filepath = os.path.join(local_output_dir, output_filename)

    with open(output_filepath, "w", encoding="utf-8") as f:
        json.dump(python_dicts, f, ensure_ascii=False, indent=4)

    print(f"★ 로컬에 JSON 저장 완료: {output_filepath}")

    spark.stop()

if __name__ == "__main__":
    # HDFS 디렉터리
    hdfs_input_dir = "hdfs://namenode:9000/user/bunjang/output"
    # 로컬 저장 디렉터리
    local_output_dir = "/opt/airflow"

    # 원하는 브랜드
    selected_brands = ["supreme", "stussy"]

    filter_and_save_json(hdfs_input_dir, local_output_dir, selected_brands)