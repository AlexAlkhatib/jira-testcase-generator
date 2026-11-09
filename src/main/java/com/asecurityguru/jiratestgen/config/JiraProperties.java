package com.asecurityguru.jiratestgen.config;

import java.time.Duration;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.util.StringUtils;

/**
 * Jira connection settings, bound from {@code app.jira.*} (environment variables in
 * production). Credentials are never committed and never validated at startup so that
 * the application can boot and report its configuration state through
 * {@code GET /api/v1/config}.
 */
@ConfigurationProperties(prefix = "app.jira")
public class JiraProperties {

    /** Jira base URL, e.g. {@code https://my-domain.atlassian.net}. */
    private String baseUrl = "";

    /** Atlassian account email used for HTTP Basic authentication. */
    private String email = "";

    /** Atlassian API token (create one at id.atlassian.com/manage-profile/security/api-tokens). */
    private String apiToken = "";

    /** Jira REST API version: 3 (Cloud, default) or 2 (Server/Data Center). */
    private String apiVersion = "3";

    /** Optional custom field id holding the acceptance criteria, e.g. {@code customfield_10045}. */
    private String acceptanceCriteriaField = "";

    /** Connect and read timeout for Jira calls. */
    private Duration timeout = Duration.ofSeconds(15);

    public boolean isConfigured() {
        return StringUtils.hasText(baseUrl)
                && StringUtils.hasText(email)
                && StringUtils.hasText(apiToken);
    }

    public String getBaseUrl() {
        return baseUrl;
    }

    public void setBaseUrl(String baseUrl) {
        this.baseUrl = baseUrl;
    }

    public String getEmail() {
        return email;
    }

    public void setEmail(String email) {
        this.email = email;
    }

    public String getApiToken() {
        return apiToken;
    }

    public void setApiToken(String apiToken) {
        this.apiToken = apiToken;
    }

    public String getApiVersion() {
        return StringUtils.hasText(apiVersion) ? apiVersion : "3";
    }

    public void setApiVersion(String apiVersion) {
        this.apiVersion = apiVersion;
    }

    public String getAcceptanceCriteriaField() {
        return acceptanceCriteriaField;
    }

    public void setAcceptanceCriteriaField(String acceptanceCriteriaField) {
        this.acceptanceCriteriaField = acceptanceCriteriaField;
    }

    public Duration getTimeout() {
        return timeout;
    }

    public void setTimeout(Duration timeout) {
        this.timeout = timeout;
    }

    /** Never expose the token through {@code toString()} (it ends up in logs). */
    @Override
    public String toString() {
        return "JiraProperties{baseUrl='" + baseUrl + "', email='" + email
                + "', apiToken='" + (StringUtils.hasText(apiToken) ? "****" : "") + "'}";
    }
}
