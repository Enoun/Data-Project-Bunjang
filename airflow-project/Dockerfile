FROM apache/airflow:2.10.3

USER root
ARG AIRFLOW_UID=501

# airflow 그룹과 사용자 ID 조건부 변경
RUN groupmod -g 0 airflow || echo "Group airflow already set to GID 0" && \
    usermod -u 501 -g 0 airflow || echo "User airflow already set"

# 필요한 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    python3-pip \
    wget \
    curl \
    unzip \
    Hadoop-client \
    && apt-get clean



USER airflow

RUN pip install --no-cache-dir selenium pyspark pandas schedule
