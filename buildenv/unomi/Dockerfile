FROM openjdk:8u312-jdk

WORKDIR /opt

ENV JAVA_VERSION=8u312
ENV UNOMI_HOME=/opt/apache-unomi-1.5.0
ENV KARAF_OPTS=-Dunomi.autoStart=true

RUN apt-get update \
    && apt-get install wget -y
RUN wget --no-check-certificate -O unomi-1.5.0-bin.tar.gz https://archive.apache.org/dist/unomi/1.5.0/unomi-1.5.0-bin.tar.gz
RUN tar -zxvf unomi-1.5.0-bin.tar.gz

ADD scripts/entrypoint.sh /opt

EXPOSE 9443
EXPOSE 8181
EXPOSE 5005

CMD [ "/bin/bash", "/opt/entrypoint.sh" ]