from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago

# DAG 기본 설정
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
}

# DAG 정의
with DAG(
    'hdfs_test_dag',
    default_args=default_args,
    description='Test HDFS Connection',
    schedule_interval=None,
    start_date=days_ago(1),
    catchup=False,
) as dag:

    # 1. HDFS에 디렉터리 생성
    create_hdfs_dir = BashOperator(
        task_id='create_hdfs_dir',
        bash_command='/usr/local/hadoop/bin/hdfs dfs -mkdir -p /airflow/test_dir && /usr/local/hadoop/bin/hdfs dfs -ls /airflow/test_dir',
        env={
            'HADOOP_USER_NAME': 'airflow',
        }
    )

    # 2. 로컬 파일 업로드 테스트
    upload_to_hdfs = BashOperator(
        task_id='upload_to_hdfs',
        bash_command='echo "This is a test file" > /tmp/test_file && hdfs dfs -put /tmp/test_file /user/test_dir'
    )

    # 작업 순서 정의
    create_hdfs_dir >> upload_to_hdfs