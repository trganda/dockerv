FROM openjdk:8u302-jdk

WORKDIR /opt

RUN apt-get update \
    && apt-get install wget -y

RUN wget --no-check-certificate -O hbase-2.4.8-bin.tar.gz https://dlcdn.apache.org/hbase/stable/hbase-2.4.8-bin.tar.gz

RUN tar -zxvf hbase-2.4.8-bin.tar.gz \
    && cd hbase-2.4.8 \
    && export JAVA_HOME=/usr/local/openjdk-8

ADD scripts/entrypointsh /opt/entrypointsh

# Exposing 16010 hbase web tools and 2181 Zookeeper port
EXPOSE 16010 2181

# HBase is configured to store data in /data/hbase, vol-mount it to persist your data.
VOLUME ["/data/hbase"]

# 
CMD [ "entrypointsh" ]