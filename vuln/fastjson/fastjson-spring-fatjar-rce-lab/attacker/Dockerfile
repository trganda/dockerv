FROM eclipse-temurin:8-jdk

WORKDIR /opt
ADD https://repo1.maven.org/maven2/org/ow2/asm/asm/9.6/asm-9.6.jar /opt/asm.jar
COPY Gen.java AttackerServer.java /opt/
RUN javac -XDignore.symbol.file -cp /opt/asm.jar -d /opt /opt/Gen.java /opt/AttackerServer.java
COPY entrypoint.sh /opt/entrypoint.sh
RUN chmod +x /opt/entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["/opt/entrypoint.sh"]
