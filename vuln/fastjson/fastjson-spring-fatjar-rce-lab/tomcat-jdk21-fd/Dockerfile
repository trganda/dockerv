FROM maven:3.9.9-amazoncorretto-21 AS build
WORKDIR /src
COPY pom.xml ./
COPY src ./src
RUN mvn -q -DskipTests package

FROM amazoncorretto:21
WORKDIR /app
COPY --from=build /src/target/app.jar /app/app.jar
EXPOSE 8080 6005
ENTRYPOINT ["java", "-jar", "/app/app.jar"]
