FROM apache/airflow:2.10.3

USER root

# Airflow 그룹과 사용자 ID 변경
ARG AIRFLOW_UID=501
RUN groupmod -g 0 airflow || echo "Group airflow already set to GID 0" && \
   usermod -u 501 -g 0 airflow || echo "User airflow already set"

# 추가 패키지 설치
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    unzip \
    default-jdk \
    python3-pip \
    && apt-get clean

# Hadoop 설치
ENV HADOOP_VERSION=3.4.0
ENV HADOOP_HOME=/usr/local/hadoop
ENV HADOOP_CONF_DIR=$HADOOP_HOME/etc/hadoop
# Spark 설치
ENV SPARK_VERSION=3.5.4
ENV SPARK_HOME=/usr/local/spark
ENV JAVA_HOME=/usr/lib/jvm/default-java
ENV HDFS_SECONDARYNAMENODE_USER=root
ENV PATH="${HADOOP_HOME}/bin:${HADOOP_HOME}/sbin:${SPARK_HOME}/bin:${SPARK_HOME}/sbin:$JAVA_HOME/bin:/home/airflow/.local/bin:${PATH}"

RUN wget https://dlcdn.apache.org/hadoop/common/hadoop-${HADOOP_VERSION}/hadoop-${HADOOP_VERSION}-aarch64.tar.gz && \
    tar -xvzf hadoop-${HADOOP_VERSION}-aarch64.tar.gz && \
    mv hadoop-${HADOOP_VERSION} $HADOOP_HOME && \
    rm hadoop-${HADOOP_VERSION}-aarch64.tar.gz

RUN wget https://dlcdn.apache.org/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-hadoop3.tgz && \
    tar -xvzf spark-${SPARK_VERSION}-bin-hadoop3.tgz && \
    mv spark-${SPARK_VERSION}-bin-hadoop3 $SPARK_HOME && \
    rm spark-${SPARK_VERSION}-bin-hadoop3.tgz

# Hadoop 환경 변수 설정
RUN echo "export JAVA_HOME=/usr/lib/jvm/default-java" >> $HADOOP_HOME/etc/hadoop/hadoop-env.sh

# Spark의 로그를 관리하는 log4j 설정
RUN echo "log4j.rootCategory=INFO, console" > $HADOOP_CONF_DIR/log4j.properties

# core-site.xml 추가
COPY ./core-site.xml $HADOOP_CONF_DIR/core-site.xml
RUN chown airflow:root $HADOOP_CONF_DIR/core-site.xml && \
    chmod 664 $HADOOP_CONF_DIR/core-site.xml

RUN pip install --no-cache-dir pandas pyspark
# Python 라이브러리 설치
USER airflow
RUN pip install --no-cache-dir selenium schedule