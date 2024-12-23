FROM apache/airflow:2.10.3

USER root/Users/data-project/data-pipeline-project/airflow-project/airflow/Dockerfile

# Airflow 그룹과 사용자 ID 변경
ARG AIRFLOW_UID=501
RUN groupmod -g 0 airflow || echo "Group airflow already set to GID 0" && \
    usermod -u 501 -g 0 airflow || echo "User airflow already set"

# 추가 패키지 설치
RUN apt-get update && apt-get install -y \
    python3-pip \
    wget \
    curl \
    unzip \
    default-jdk \
    && apt-get clean

# Python 라이브러리 설치
USER airflow
RUN pip install --no-cache-dir selenium pyspark pandas schedule