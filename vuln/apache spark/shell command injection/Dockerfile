FROM openjdk:8u111-jdk

WORKDIR /opt

COPY ./spark-3.1.2-bin-hadoop2.7.tgz /opt/spark-3.1.2-bin-hadoop2.7.tgz

RUN apt-get update -y \
    || apt-get install netcat -y

RUN tar -xf /opt/spark-3.1.2-bin-hadoop2.7.tgz \
    && rm -rf spark-3.1.2-bin-hadoop2.7.tgz \
    && mv spark-3.1.2-bin-hadoop2.7 spark

ENV PATH /opt/spark/bin:$PATH

EXPOSE 4040

ENTRYPOINT [ "spark-shell" ]