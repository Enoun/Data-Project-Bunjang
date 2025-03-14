from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta
from elasticsearch import Elasticsearch
import json
import sys

sys.path.append('/opt/airflow/modules')
from bunjang_crawler import update_products, save_to_json

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 11, 27, 12, 0),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
}

dag = DAG(
    'merge_release',
    default_args=default_args,
    description='Bunjang crawler merge DAG',
    schedule_interval=None,
    max_active_runs=1,
)

def merge_results_task(**kwargs):
    brand = kwargs['dag_run'].conf.get('brand', 'default_brand')
    today = datetime.now().strftime("%Y%m%d")
    input_file = f"/opt/airflow/output/{brand}_update_{today}.json"
    print(f"Starting merge task for brand: {brand}")
    print(f"Input file: {input_file}")

    with open(input_file, "r", encoding="utf-8") as file:
        update_data = json.load(file)
    print(f"Loaded {len(update_data)} records from {input_file}")

    es = Elasticsearch(['http://elasticsearch:9200'])

    for product in update_data:
        result = es.search(index='bunjang_products', body={'query': {'match': {'pid': product['pid']}}})

        if result['hits']['total']['value'] > 0:
            existing_product = result['hits']['hits'][0]['_source']
            brands = set(existing_product['brands'])
            brands.update(product['brands'])
            price_updates = existing_product['price_updates']
            new_price_updates = [
                {
                    'price': int(next(iter(item.values()))),
                    'updated_at': datetime.fromtimestamp(int(next(iter(item.keys()))))
                }
                for item in product['price_updates']
            ]
            for update in new_price_updates:
                if update not in price_updates:
                    price_updates.append(update)
            status = product['status'] if product['status'] != existing_product['status'] else existing_product['status']

            doc = {
                'brands': list(brands),
                'name': product['name'],
                'price_updates': price_updates,
                'product_image': product['product_image'],
                'status': status,
                'category_id_1': product['category_id'][:3],
                'category_id_2': product['category_id'][:6],
                'category_id_3': product['category_id']
            }
            es.update(index='bunjang_products', id=result['hits']['hits'][0]['_id'], body={'doc': doc})
            print(f"업데이트: pid: {product['pid']}")
        else:
            doc = {
                'pid': product['pid'],
                'brands': product['brands'],
                'name': product['name'],
                'price_updates': [
                    {
                        'price': int(next(iter(item.values()))),
                        'updated_at': datetime.fromtimestamp(int(next(iter(item.keys()))))
                    }
                    for item in product['price_updates']
                ],
                'product_image': product['product_image'],
                'status': product['status'],
                'category_id_1': product['category_id'][:3],
                'category_id_2': product['category_id'][:6],
                'category_id_3': product['category_id']
            }
            es.index(index='bunjang_products', body=doc)
            print(f"제품추가: pid: {product['pid']}")

    print(f"Merge task 완료: {brand}")

merge_task = PythonOperator(
    task_id='merge_results',
    python_callable=merge_results_task,
    provide_context=True,
    dag=dag,
    pool='merge_pool',
)
