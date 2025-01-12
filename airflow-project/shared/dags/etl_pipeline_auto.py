from sndhdr import test_hcom

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago
from datetime import timedelta, datetime
from pytz import timezone

from hdfs_test import upload_to_hdfs

# 기본 설정
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
    'execution_timeout': timedelta(minutes=20),
}

# DAG 정의
with DAG(
        dag_id = 'data_pipeline_etl',
        default_args=default_args,
        description='An ETL pipeline with HDFS and Spark',
        # schedule_interval="@once",  # 한 번만 실행 (테스트 용)
        # start_date=days_ago(1),
        # schedule_interval='30 10,22 * * *',
        start_date=datetime(2024, 12, 6, tzinfo=timezone('Asia/Seoul')),
        catchup=False,
        max_active_runs=1,
) as dag:
    # 1. 데이터 수집
    # collect_data = BashOperator(
    #     task_id='collect_data',
    #     bash_command='python /opt/airflow/data-pipeline-project/product_data_scraper.py',
    #     execution_timeout=timedelta(minutes=60)
    # )

    # debug_task = BashOperator(
    #     task_id='debug_task',
    #     bash_command='''
    #     echo "=== User Info ===";
    #     id;
    #     echo "=== Current Directory ===";
    #     pwd;
    #     echo "=== File List ===";
    #     ls -la /opt/airflow/data-pipeline-project;
    #     echo "=== Environment Variables ===";
    #     env;
    #     '''
    # )

    # HDFS에 업로드
    # upload_to_hdfs = BashOperator(
    #     task_id='upload_to_hdfs',
    #     bash_command='python /opt/airflow/data-pipeline-project/upload-to-hdfs/upload_to_hdfs.py',
    # )

    debug_task = BashOperator(
        task_id='debug_task',
        bash_command="""
        echo "PATH: $PATH";
        echo "HADOOP_HOME: $HADOOP_HOME";
        echo "HADOOP_CONF_DIR: $HADOOP_CONF_DIR";
        ls -ld $HADOOP_CONF_DIR;
        ls -l /usr/local/hadoop/etc/hadoop/core-site.xml;
        ls -l $HADOOP_CONF_DIR/core-site.xml;
        hdfs dfs -ls /
        """,
        env={
            'PATH': '/usr/local/hadoop/bin:/usr/local/hadoop/sbin:/bin:/usr/bin',
            'HADOOP_HOME': '/usr/local/hadoop',
            'HADOOP_CONF_DIR': '/usr/local/hadoop/etc/hadoop',
            'HADOOP_USER_NAME': 'airflow'
        },
    )

    update_core_site = BashOperator(
        task_id='update_core_site',
        bash_command="""
            echo '
            <configuration>
                <property>
                    <name>fs.defaultFS</name>
                    <value>hdfs://namenode:9000</value>
                </property>
                <property>
                    <name>fs.webhdfs.impl</name>
                    <value>org.apache.hadoop.hdfs.web.WebHdfsFileSystem</value>
                </property>
            </configuration>
            ' > $HADOOP_CONF_DIR/core-site.xml
        """,
        env={
            'HADOOP_CONF_DIR': '/usr/local/hadoop/etc/hadoop',
        },
    )

    # debug_task = BashOperator(
    #     task_id='debug_task',
    #     bash_command='hdfs dfs -ls /',
    #     env={
    #         'HADOOP_CONF_DIR': '/usr/local/hadoop/etc/hadoop',
    #         'HADOOP_USER_NAME': 'hdfs',  # airflow 사용자로 실행
    #     },
    # )

    # # 3. Spark 전처리 작업
    # spark_processing = BashOperator(
    #     task_id='spark_processing',
    #     bash_command='spark-submit --master local /opt/airflow/data-pipeline-project/etl-spark/etl_pipeline.py',
    # )

    # collect_data >> upload_to_hdfs >> spark_processing
    # upload_to_hdfs >> spark_processing
    debug_task >> update_core_site