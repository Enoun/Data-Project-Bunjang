from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from datetime import datetime, timedelta
from pytz import timezone
import json
import sys
import os
import threading

sys.path.append('/opt/airflow/modules')
from bunjang_crawler import collect_and_filter_data, merge_results

KST = timezone('Asia/Seoul')

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
    'execution_timeout': timedelta(minutes=60),
}

with DAG(
        'trigger_dag',
        default_args=default_args,
        description='번개장터의 브랜드별 데이터를 Elasticsearch에 수집 및 필터링하는 DAG',
        start_date=datetime(2024, 11, 27, 12, 0),
        schedule_interval='30 10,22 * * *',
        # schedule_interval="@once",
        catchup=False,
        max_active_runs=1,
) as trigger_dag:
    
    def crawl_and_filter(brand, **kwargs):
        # 출력 파일 경로를 생성합니다. 예: /opt/airflow/output/nike_products.json
        output_file = f"/opt/airflow/output/{brand[0]}_products.json"
        collect_and_filter_data([brand[0]], output_file)
    
    # 브랜드 목록 파일 불러오기 (예: {"nike": "나이키", "adidas": "아디다스", ...})
    with open("/opt/airflow/data/brands_test.json", "r", encoding="utf-8") as f:
        brands = json.load(f)
    
    # 각 브랜드에 대해 동적으로 태스크 생성
    for brand in brands.items():
        crawl_task = PythonOperator(
            task_id=f"crawl_and_filter_{brand[0]}",
            python_callable=crawl_and_filter,
            op_kwargs={"brand": brand},
            dag=trigger_dag,
        )
    
        trigger_merge_task = TriggerDagRunOperator(
            task_id=f"trigger_merge_{brand[0]}",
            trigger_dag_id="merge_dag",  # 병합 DAG의 dag_id
            conf={"brand": brand[0]},
            dag=trigger_dag,
        )
    
        crawl_task >> trigger_merge_task

# 병합 작업에서 동시성을 제어하기 위한 Lock
merge_lock = threading.Lock()

with DAG(
    dag_id='merge_dag',
    default_args=default_args,
    description='번개장터의 브랜드별 수집 데이터를 병합하는 DAG',
    schedule_interval=None,
) as merge_dag:

    def merge_results_task(**kwargs):
        # TriggerDagRunOperator로부터 전달된 conf에서 브랜드 정보 획득
        brand = kwargs['dag_run'].conf.get('brand', 'default_brand')
        input_dir = "/opt/airflow/output"
        output_file = f"/opt/airflow/output/{brand}_merged_products.json"
        merge_results(input_dir, output_file, merge_lock, brand)

    merge_task = PythonOperator(
        task_id='merge_results',
        python_callable=merge_results_task,
        provide_context=True,
        dag=merge_dag,
    )