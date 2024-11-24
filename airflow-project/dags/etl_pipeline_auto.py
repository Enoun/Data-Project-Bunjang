from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago
from datetime import timedelta

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
        start_date=days_ago(1),
        catchup=False,
        max_active_runs=1,
) as dag:
    # 1. 데이터 수집
    collect_data = BashOperator(
        task_id='collect_data',
        bash_command='python /opt/airflow/data-pipeline-project/product_data_scraper.py',
        execution_timeout=timedelta(minutes=10)  # 실행 시간 제한을 10분으로 설정
    )

    # HDFS에 업로드
    upload_to_hdfs = BashOperator(
        task_id='upload_to_hdfs',
        bash_command='python /opt/airflow/data-pipeline-project/upload_to_hdfs.py',
    )

    # 3. Spark 전처리 작업
    spark_processing = BashOperator(
        task_id='spark_processing',
        bash_command='spark-submit --master local /opt/airflow/data-pipeline-project/etl_pipeline.py',
    )

    # 작업 순서 정의
    collect_data >> upload_to_hdfs >> spark_processing