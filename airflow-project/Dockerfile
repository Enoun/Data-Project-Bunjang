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

ENV HADOOP_VERSION=3.4.0
ENV HADOOP_HOME=/usr/local/hadoop
ENV HADOOP_CONF_DIR=$HADOOP_HOME/etc/hadoop
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-arm64
ENV PATH=$HADOOP_HOME/bin:$HADOOP_HOME/sbin:$PATH
ENV PATH=$JAVA_HOME/bin:$PATH

# Hadoop 설치
RUN wget https://dlcdn.apache.org/hadoop/common/hadoop-${HADOOP_VERSION}/hadoop-${HADOOP_VERSION}-aarch64.tar.gz && \
    tar -xvzf hadoop-${HADOOP_VERSION}-aarch64.tar.gz && \
    mv hadoop-${HADOOP_VERSION} $HADOOP_HOME && \
    rm hadoop-${HADOOP_VERSION}-aarch64.tar.gz

RUN mkdir -p /usr/local/hadoop/logs && \
    chown -R airflow:root /usr/local/hadoop/logs

# 기본 설정
RUN echo '<configuration><property><name>fs.defaultFS</name><value>hdfs://namenode:9000</value></property></configuration>' > $HADOOP_CONF_DIR/core-site.xml && \
    echo '<configuration><property><name>dfs.replication</name><value>1</value></property></configuration>' > $HADOOP_CONF_DIR/hdfs-site.xml && \
    echo "export JAVA_HOME=$JAVA_HOME" > $HADOOP_CONF_DIR/hadoop-env.sh



USER airflow
RUN pip install --no-cache-dir selenium pyspark pandas schedule