from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
from datetime import timedelta
import os

# 기본 설정
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# DAG 정의
with DAG(
    'data_pipeline_etl',
    default_args = default_args,
    description = 'An ETL pipeline with HDFS and Spark',
    schedule_interval = timedelta(hours=8),
    start_date = days_ago(1),
    catchup = False,
) as dag:
    
    # 1. 데이터 수집
    collect_data = BashOperator(
        task_id = 'collect_data',
        bash_command = 'python /Users/data-project/data-pipeline-project/product_data_scraper.py',
    )

    # HDFS에 업로드
    def upload_to_hdfs():
        os.system("hdfs dfs -put /local.data/path.csv /user/dataPipeline/collectedData")

    upload_data = PythonOperator(
        task_id = 'upload_to_hdfs',
        python_callable = upload_to_hdfs,
    )

    # 3. spark 전처리 작업
    spark_processing = BashOperator(
        task_id = 'spark_processing',
        bash_command = 'spark-submit --master local /Users/data-project/data-pipeline-project/etl-saprk/etl_pipeline.py',
    )

    # 작업 순서 정의
    collect_data >> upload_data >> spark_processing