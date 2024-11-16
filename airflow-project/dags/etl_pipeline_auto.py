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
}

venv_activated = "/Users/data-project/data-pipeline-project/.venv/bin/activate"

# DAG 정의
with DAG(
    'data_pipeline_etl',
    default_args = default_args,
    description = 'An ETL pipeline with HDFS and Spark',
    schedule_interval = "0 7, 15, 23 * * *", #매일 7시, 15시, 23시
    start_date = days_ago(1),
    catchup = False,
) as dag:
    
    # 1. 데이터 수집
    collect_data = BashOperator(
        task_id = 'collect_data',
        bash_command = f'source {venv_activated} && python /Users/data-project/data-pipeline-project/product_data_scraper.py',
    )

    # HDFS에 업로드
    upload_to_hdfs = BashOperator(
        task_id = 'upload_to_hdfs',
        python_callable = 'python /Users/data-project/data-pipeline-project/upload-to-hdfs/upload_to_hdfs.py'
    )

    # 3. spark 전처리 작업
    spark_processing = BashOperator(
        task_id = 'spark_processing',
        bash_command = 'python //Users/data-project/data-pipeline-project/etl-saprk/etl_pipeline.py'
    )

    # 작업 순서 정의
    collect_data >> upload_to_hdfs >> spark_processing