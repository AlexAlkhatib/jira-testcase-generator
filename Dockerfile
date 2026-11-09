# syntax=docker/dockerfile:1
# ---------- Build ----------
FROM gradle:8.8-jdk17 AS build
WORKDIR /home/gradle/project
COPY --chown=gradle:gradle settings.gradle build.gradle gradle.properties ./
COPY --chown=gradle:gradle gradle ./gradle
COPY --chown=gradle:gradle src ./src
RUN gradle bootJar --no-daemon --console=plain -x test

# ---------- Runtime ----------
FROM eclipse-temurin:17-jre-alpine
LABEL org.opencontainers.image.title="jira-test-case-generator" \
      org.opencontainers.image.description="Generate structured Jira test cases with a local Ollama model" \
      org.opencontainers.image.licenses="MIT"

RUN addgroup -S app && adduser -S app -G app
WORKDIR /app
COPY --from=build /home/gradle/project/build/libs/jira-test-case-generator.jar /app/app.jar

USER app
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
  CMD wget -qO- http://127.0.0.1:8080/actuator/health | grep -q '"status":"UP"' || exit 1

ENTRYPOINT ["java", "-XX:MaxRAMPercentage=75", "-XX:+UseG1GC", "-jar", "/app/app.jar"]
