FROM amazoncorretto:21

WORKDIR /opt
ADD https://repo1.maven.org/maven2/org/ow2/asm/asm/9.6/asm-9.6.jar /opt/asm.jar
COPY GenFd.java AttackerFdServer.java /opt/
RUN javac -cp /opt/asm.jar -d /opt /opt/GenFd.java /opt/AttackerFdServer.java
COPY entrypoint.sh /opt/entrypoint.sh
RUN chmod +x /opt/entrypoint.sh

EXPOSE 8001
ENTRYPOINT ["/opt/entrypoint.sh"]
