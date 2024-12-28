from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago
from datetime import timedelta, datetime
from pytz import timezone

# 기본 설정
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    'execution_timeout': timedelta(minutes=20),
}

# DAG 정의
with DAG(
        dag_id = 'data_pipeline_etl',
        default_args=default_args,
        description='An ETL pipeline with HDFS and Spark',
        schedule_interval="@once",  # 한 번만 실행
        # start_date=days_ago(1),
        # schedule_interval='0 13 * * *',  # UTC 기준으로 14시 = 한국 시간으로 23시
        start_date=datetime(2024, 12, 6, tzinfo=timezone('Asia/Seoul')),  # 한국 시간대
        catchup=False,
        max_active_runs=1,
) as dag:
    # 1. 데이터 수집
    # collect_data = BashOperator(
    #     task_id='collect_data',
    #     bash_command='python /opt/airflow/data-pipeline-project/product_data_scraper.py',
    #     execution_timeout=timedelta(minutes=60)
    # )

    # HDFS에 업로드
    upload_to_hdfs = BashOperator(
        task_id='upload_to_hdfs',
        bash_command='python /opt/airflow/data-pipeline-project/upload-to-hdfs/upload_to_hdfs.py',
    )

    # 3. Spark 전처리 작업
    spark_processing = BashOperator(
        task_id='spark_processing',
        bash_command='spark-submit --master local /opt/airflow/data-pipeline-project/etl-spark/etl_pipeline.py',
    )

    # 작업 순서 정의
    # collect_data >> upload_to_hdfs >> spark_processing
    upload_to_hdfs >> spark_processing