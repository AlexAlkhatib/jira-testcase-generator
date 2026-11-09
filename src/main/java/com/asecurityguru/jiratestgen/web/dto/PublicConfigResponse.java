package com.asecurityguru.jiratestgen.web.dto;

import java.util.List;

/**
 * Safe, secret-free view of the runtime configuration, consumed by the web UI to display
 * a setup banner and the available options.
 */
public record PublicConfigResponse(
        String application,
        String version,
        boolean jiraConfigured,
        String jiraBaseUrl,
        String jiraApiVersion,
        boolean acceptanceCriteriaFieldConfigured,
        String model,
        int defaultTestCases,
        int maxTestCases,
        List<String> languages,
        List<String> formats) {
}
