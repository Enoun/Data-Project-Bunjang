FROM openjdk:11-jdk-slim

# Hadoop 환경 변수 설정
ENV HADOOP_VERSION=3.4.0
ENV HADOOP_HOME=/usr/local/hadoop
ENV HADOOP_CONF_DIR=$HADOOP_HOME/etc/hadoop
ENV JAVA_HOME=/usr/local/openjdk-11
ENV PATH=$HADOOP_HOME/bin:$HADOOP_HOME/sbin:$PATH

# 필수 패키지 설치
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    && apt-get clean

# Hadoop 공식 홈페이지를 통해 ARM64환경 하둡 설치
RUN wget https://dlcdn.apache.org/hadoop/common/hadoop-${HADOOP_VERSION}/hadoop-${HADOOP_VERSION}-aarch64.tar.gz && \
    tar -xvzf hadoop-${HADOOP_VERSION}-aarch64.tar.gz && \
    mv hadoop-${HADOOP_VERSION} $HADOOP_HOME && \
    rm hadoop-${HADOOP_VERSION}-aarch64.tar.gz

# 로그 디렉토리 생성
RUN mkdir -p /usr/local/hadoop/logs && \
    chown -R root:root /usr/local/hadoop/logs

# Hadoop 설정 복사
COPY core-site.xml $HADOOP_CONF_DIR/core-site.xml
COPY hdfs-site.xml $HADOOP_CONF_DIR/hdfs-site.xml
COPY hadoop-env.sh $HADOOP_CONF_DIR/hadoop-env.sh

CMD ["hdfs", "namenode"]