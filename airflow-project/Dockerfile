FROM apache/airflow:2.10.3

USER root
ARG AIRFLOW_UID=501

# airflow 그룹과 사용자 ID 조건부 변경
RUN groupmod -g 0 airflow || echo "Group airflow already set to GID 0" && \
    usermod -u 501 -g 0 airflow || echo "User airflow already set"

RUN apt-get update && apt-get install -y \
    python3-pip \
    wget \
    curl \
    unzip \
    default-jdk \
    && apt-get clean

ENV DEBIAN_FRONTEND=noninteractive
ENV HADOOP_HOME=/usr/local/hadoop
ENV HADOOP_CONF_DIR=$HADOOP_HOME/etc/hadoop
ENV PATH=$HADOOP_HOME/bin:$PATH

USER airflow

RUN pip install --no-cache-dir selenium pyspark pandas schedule
