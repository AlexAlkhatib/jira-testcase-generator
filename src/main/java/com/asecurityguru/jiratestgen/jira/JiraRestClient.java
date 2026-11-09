package com.asecurityguru.jiratestgen.jira;

import java.time.Duration;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Component;
import org.springframework.util.StringUtils;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientResponseException;

import com.asecurityguru.jiratestgen.config.JiraProperties;
import com.asecurityguru.jiratestgen.error.JiraAuthenticationException;
import com.asecurityguru.jiratestgen.error.JiraNotConfiguredException;
import com.asecurityguru.jiratestgen.error.JiraStoryNotFoundException;
import com.asecurityguru.jiratestgen.error.JiraUnavailableException;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

/**
 * Jira Cloud / Data Center REST client built on Spring's {@link RestClient}.
 *
 * <p>Deliberately lighter than the official Jira Java client: only one endpoint is needed,
 * timeouts are explicit, and Cloud (v3 / ADF) and Server (v2 / plain text) payloads are both
 * supported.</p>
 */
@Component
public class JiraRestClient implements JiraStoryClient {

    private static final Logger log = LoggerFactory.getLogger(JiraRestClient.class);
    private static final String BASE_FIELDS = "summary,description,issuetype,status";

    private final JiraProperties properties;
    private final AdfTextExtractor adfTextExtractor;
    private final AcceptanceCriteriaExtractor acceptanceCriteriaExtractor;
    private final ObjectMapper objectMapper;
    private final RestClient restClient;

    public JiraRestClient(JiraProperties properties,
                          AdfTextExtractor adfTextExtractor,
                          AcceptanceCriteriaExtractor acceptanceCriteriaExtractor,
                          ObjectMapper objectMapper) {
        this.properties = properties;
        this.adfTextExtractor = adfTextExtractor;
        this.acceptanceCriteriaExtractor = acceptanceCriteriaExtractor;
        this.objectMapper = objectMapper;
        this.restClient = properties.isConfigured() ? buildClient(properties) : null;
        if (this.restClient == null) {
            log.warn("Jira is not configured: /api/v1/test-cases will answer 503 until "
                    + "JIRA_BASE_URL, JIRA_EMAIL and JIRA_API_TOKEN are provided.");
        }
    }

    @Override
    public JiraStory fetch(String storyKey) {
        if (restClient == null) {
            throw new JiraNotConfiguredException();
        }

        String fields = BASE_FIELDS;
        if (StringUtils.hasText(properties.getAcceptanceCriteriaField())) {
            fields = fields + "," + properties.getAcceptanceCriteriaField().trim();
        }
        String apiVersion = properties.getApiVersion();
        String requestedFields = fields;

        String body;
        try {
            body = restClient.get()
                    .uri(uriBuilder -> uriBuilder
                            .path("/rest/api/{version}/issue/{key}")
                            .queryParam("fields", requestedFields)
                            .build(apiVersion, storyKey))
                    .retrieve()
                    .body(String.class);
        } catch (RestClientResponseException e) {
            int status = e.getStatusCode().value();
            log.warn("Jira answered HTTP {} for issue {}", status, storyKey);
            if (status == 404) {
                throw new JiraStoryNotFoundException(storyKey);
            }
            if (status == 401 || status == 403) {
                throw new JiraAuthenticationException("HTTP " + status + " (token expired or scope missing)");
            }
            throw new JiraUnavailableException("Jira answered HTTP " + status + " for issue " + storyKey, e);
        } catch (ResourceAccessException e) {
            throw new JiraUnavailableException(
                    "Jira cannot be reached at " + normaliseBaseUrl(properties.getBaseUrl())
                            + " (timeout or network error)", e);
        }

        return mapStory(storyKey, body);
    }

    JiraStory mapStory(String storyKey, String body) {
        JsonNode root;
        try {
            root = objectMapper.readTree(body);
        } catch (JsonProcessingException e) {
            throw new JiraUnavailableException("Jira returned a malformed JSON payload for issue " + storyKey, e);
        }
        JsonNode fields = root.path("fields");
        if (fields.isMissingNode() || !fields.isObject()) {
            throw new JiraUnavailableException("Jira response does not contain the expected 'fields' object");
        }

        String summary = fields.path("summary").asText("").trim();
        String issueType = fields.path("issuetype").path("name").asText("Issue");
        String status = fields.path("status").path("name").asText("Unknown");
        String description = adfTextExtractor.toPlainText(fields.get("description"));

        String customField = properties.getAcceptanceCriteriaField();
        String customCriteria = StringUtils.hasText(customField)
                ? adfTextExtractor.toPlainText(fields.get(customField.trim()))
                : "";

        String acceptanceCriteria;
        String source;
        if (StringUtils.hasText(customCriteria)) {
            acceptanceCriteria = customCriteria;
            source = "custom-field:" + customField.trim();
        } else {
            acceptanceCriteria = acceptanceCriteriaExtractor.extract(description, summary);
            source = acceptanceCriteria.equals(description.trim()) ? "description" : "description-section";
        }

        return new JiraStory(
                storyKey,
                summary,
                issueType,
                status,
                description,
                acceptanceCriteria,
                source,
                normaliseBaseUrl(properties.getBaseUrl()) + "/browse/" + storyKey);
    }

    static RestClient buildClient(JiraProperties properties) {
        Duration timeout = properties.getTimeout() == null ? Duration.ofSeconds(15) : properties.getTimeout();
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout((int) Math.min(Integer.MAX_VALUE, timeout.toMillis()));
        factory.setReadTimeout((int) Math.min(Integer.MAX_VALUE, timeout.toMillis()));

        return RestClient.builder()
                .baseUrl(normaliseBaseUrl(properties.getBaseUrl()))
                .requestFactory(factory)
                .defaultHeaders(headers -> {
                    headers.setBasicAuth(properties.getEmail(), properties.getApiToken());
                    headers.setAccept(java.util.List.of(MediaType.APPLICATION_JSON));
                    headers.set(HttpHeaders.USER_AGENT, "jira-test-case-generator/2.0");
                })
                .build();
    }

    /**
     * Accepts either {@code https://instance.atlassian.net} or the legacy
     * {@code https://instance.atlassian.net/rest/api/3} form and returns the bare instance URL.
     */
    public static String normaliseBaseUrl(String raw) {
        if (!StringUtils.hasText(raw)) {
            return "";
        }
        String url = raw.trim();
        while (url.endsWith("/")) {
            url = url.substring(0, url.length() - 1);
        }
        return url.replaceAll("(?i)/rest/api/(?:2|3|latest)$", "");
    }
}
