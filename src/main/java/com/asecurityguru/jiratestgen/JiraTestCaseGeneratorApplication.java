package com.asecurityguru.jiratestgen;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.ConfigurationPropertiesScan;

/**
 * Entry point of the Jira Test Case Generator.
 *
 * <p>The application exposes a REST API and a small web UI that turn a Jira user story
 * (description + acceptance criteria) into structured functional test cases thanks to a
 * local Ollama model. No credential is ever required at build time: Jira is configured
 * through environment variables only.</p>
 */
@SpringBootApplication
@ConfigurationPropertiesScan
public class JiraTestCaseGeneratorApplication {

    public static void main(String[] args) {
        SpringApplication.run(JiraTestCaseGeneratorApplication.class, args);
    }
}
