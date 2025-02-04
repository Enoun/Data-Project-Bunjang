# Data-Project-Bunjang
Non AWS server Project

이 스크립트는 PySpark와 HDFS를 활용하여 데이터를 전처리하고, 처리된 데이터를 로컬 파일 및 HDFS에 저장합니다. 또한 너무 잦은 데이터 처리를 방지하기 위해 최근 7일치 데이터를 대상으로 작업하며, 중복 데이터를 제거하고 유효한 데이터를 필터링하여 최종 CSV 파일을 생성합니다.

• SparkSession 생성:
	Spark 클러스터와의 상호작용을 위한 SparkSession을 초기화합니다.

• 최근 7일치 데이터 필터링:
	HDFS에서 최근 7일 동안 저장된 파일만 필터링합니다.
	날짜 형식은 YYYYMMDD로 파싱하여 비교합니다.

• 데이터 전처리:
	데이터 컬럼 이름을 영어로 변경합니다.
	가격 데이터를 정수형으로 변환합니다.
	광고(“AD”) 및 특정 패턴(구합니다, 삽니다 등)을 포함한 상품명을 필터링합니다.
    중복 데이터를 제거하여 정리된 결과를 생성합니다.

• 저장:
	전처리된 데이터를 HDFS와 로컬 디렉터리에 저장합니다.
	HDFS 경로: /user/dataPipeline/processedData/{category}_processed_YYYYMMDD.csv
	로컬 경로: /Users/data-project/data-pipeline-project/airflow-project/shared/processedData

sd