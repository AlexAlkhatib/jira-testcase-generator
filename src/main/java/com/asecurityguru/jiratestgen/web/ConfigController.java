package com.asecurityguru.jiratestgen.web;

import java.util.Arrays;
import java.util.List;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.util.StringUtils;

import com.asecurityguru.jiratestgen.ai.model.TestFormat;
import com.asecurityguru.jiratestgen.ai.model.TestLanguage;
import com.asecurityguru.jiratestgen.config.GenerationProperties;
import com.asecurityguru.jiratestgen.config.JiraProperties;
import com.asecurityguru.jiratestgen.jira.JiraRestClient;
import com.asecurityguru.jiratestgen.web.dto.PublicConfigResponse;

/** Exposes the non-sensitive runtime configuration used by the web UI. */
@RestController
@RequestMapping("/api/v1")
public class ConfigController {

    private final JiraProperties jiraProperties;
    private final GenerationProperties generationProperties;
    private final String version;
    private final String model;

    public ConfigController(JiraProperties jiraProperties,
                            GenerationProperties generationProperties,
                            @Value("${app.version:2.0.0}") String version,
                            @Value("${spring.ai.ollama.chat.options.model:mistral}") String model) {
        this.jiraProperties = jiraProperties;
        this.generationProperties = generationProperties;
        this.version = version;
        this.model = model;
    }

    @GetMapping("/config")
    public PublicConfigResponse config() {
        return new PublicConfigResponse(
                "Jira Test Case Generator",
                version,
                jiraProperties.isConfigured(),
                jiraProperties.isConfigured() ? JiraRestClient.normaliseBaseUrl(jiraProperties.getBaseUrl()) : "",
                jiraProperties.getApiVersion(),
                StringUtils.hasText(jiraProperties.getAcceptanceCriteriaField()),
                model,
                generationProperties.getDefaultTestCases(),
                generationProperties.getMaxTestCases(),
                Arrays.stream(TestLanguage.values()).map(Enum::name).toList(),
                Arrays.stream(TestFormat.values()).map(Enum::name).toList());
    }
}
