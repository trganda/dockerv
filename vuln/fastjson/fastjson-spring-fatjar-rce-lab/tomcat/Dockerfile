FROM maven:3.8.8-eclipse-temurin-8 AS build
WORKDIR /src
COPY pom.xml ./
COPY src ./src
RUN mvn -q -DskipTests package

FROM eclipse-temurin:8-jdk
WORKDIR /app
COPY --from=build /src/target/app.jar /app/app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "/app/app.jar"]
