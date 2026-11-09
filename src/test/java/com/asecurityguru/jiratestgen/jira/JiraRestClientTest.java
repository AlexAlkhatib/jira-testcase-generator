package com.asecurityguru.jiratestgen.jira;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.Base64;

import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import com.asecurityguru.jiratestgen.config.JiraProperties;
import com.asecurityguru.jiratestgen.error.JiraAuthenticationException;
import com.asecurityguru.jiratestgen.error.JiraNotConfiguredException;
import com.asecurityguru.jiratestgen.error.JiraStoryNotFoundException;
import com.asecurityguru.jiratestgen.error.JiraUnavailableException;
import com.fasterxml.jackson.databind.ObjectMapper;

import okhttp3.mockwebserver.MockResponse;
import okhttp3.mockwebserver.MockWebServer;
import okhttp3.mockwebserver.RecordedRequest;

class JiraRestClientTest {

    private MockWebServer server;
    private JiraProperties properties;

    @BeforeEach
    void setUp() throws IOException {
        server = new MockWebServer();
        server.start();
        properties = new JiraProperties();
        properties.setBaseUrl(server.url("/").toString());
        properties.setEmail("qa@example.com");
        properties.setApiToken("secret-token");
        properties.setTimeout(Duration.ofSeconds(5));
    }

    @AfterEach
    void tearDown() throws IOException {
        server.shutdown();
    }

    private JiraRestClient client() {
        return new JiraRestClient(properties, new AdfTextExtractor(), new AcceptanceCriteriaExtractor(),
                new ObjectMapper());
    }

    @Test
    @DisplayName("a Jira Cloud payload is mapped, ADF is flattened and Basic auth is sent")
    void fetchesAndMapsStory() throws Exception {
        server.enqueue(jsonResponse("""
                {
                  "key": "KAN-3",
                  "fields": {
                    "summary": "User can log in",
                    "issuetype": {"name": "Story"},
                    "status": {"name": "In Progress"},
                    "description": {
                      "type": "doc", "version": 1,
                      "content": [
                        {"type": "heading", "attrs": {"level": 2}, "content": [{"type": "text", "text": "Acceptance Criteria"}]},
                        {"type": "bulletList", "content": [
                          {"type": "listItem", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Valid credentials open the dashboard"}]}]},
                          {"type": "listItem", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Invalid password displays an error"}]}]}
                        ]}
                      ]
                    }
                  }
                }
                """));

        JiraStory story = client().fetch("KAN-3");

        assertThat(story.key()).isEqualTo("KAN-3");
        assertThat(story.summary()).isEqualTo("User can log in");
        assertThat(story.issueType()).isEqualTo("Story");
        assertThat(story.status()).isEqualTo("In Progress");
        assertThat(story.acceptanceCriteria()).contains("Valid credentials open the dashboard");
        assertThat(story.acceptanceCriteriaSource()).isEqualTo("description-section");
        assertThat(story.url()).endsWith("/browse/KAN-3");

        RecordedRequest request = server.takeRequest();
        assertThat(request.getPath()).startsWith("/rest/api/3/issue/KAN-3");
        assertThat(request.getPath()).contains("fields=").contains("summary").contains("description");
        String expectedAuth = "Basic " + Base64.getEncoder()
                .encodeToString("qa@example.com:secret-token".getBytes(StandardCharsets.UTF_8));
        assertThat(request.getHeader("Authorization")).isEqualTo(expectedAuth);
    }

    @Test
    @DisplayName("a configured acceptance-criteria custom field takes precedence")
    void usesCustomAcceptanceCriteriaField() {
        properties.setAcceptanceCriteriaField("customfield_10042");
        server.enqueue(jsonResponse("""
                {
                  "key": "KAN-4",
                  "fields": {
                    "summary": "Password reset",
                    "issuetype": {"name": "Story"},
                    "status": {"name": "To Do"},
                    "description": "A long description without a dedicated section.",
                    "customfield_10042": "Given a registered email, when I reset, then a link is sent."
                  }
                }
                """));

        JiraStory story = client().fetch("KAN-4");

        assertThat(story.acceptanceCriteria()).isEqualTo("Given a registered email, when I reset, then a link is sent.");
        assertThat(story.acceptanceCriteriaSource()).isEqualTo("custom-field:customfield_10042");
        assertThat(story.description()).isEqualTo("A long description without a dedicated section.");
    }

    @Test
    @DisplayName("issue 404 becomes a typed STORY_NOT_FOUND error")
    void mapsNotFound() {
        server.enqueue(new MockResponse().setResponseCode(404)
                .setHeader("Content-Type", "application/json")
                .setBody("{\"errorMessages\":[\"Issue does not exist\"]}"));

        assertThatThrownBy(() -> client().fetch("KAN-404"))
                .isInstanceOf(JiraStoryNotFoundException.class)
                .hasMessageContaining("KAN-404");
    }

    @Test
    @DisplayName("401 becomes JIRA_AUTH_FAILED instead of a generic crash")
    void mapsAuthenticationFailure() {
        server.enqueue(new MockResponse().setResponseCode(401));

        assertThatThrownBy(() -> client().fetch("KAN-3"))
                .isInstanceOf(JiraAuthenticationException.class);
    }

    @Test
    @DisplayName("a 500 becomes JIRA_UNAVAILABLE")
    void mapsServerError() {
        server.enqueue(new MockResponse().setResponseCode(500));

        assertThatThrownBy(() -> client().fetch("KAN-3"))
                .isInstanceOf(JiraUnavailableException.class)
                .hasMessageContaining("HTTP 500");
    }

    @Test
    @DisplayName("missing credentials fail fast with a clear 503, not at startup")
    void reportsMissingConfiguration() {
        properties.setApiToken("");

        assertThatThrownBy(() -> client().fetch("KAN-3"))
                .isInstanceOf(JiraNotConfiguredException.class);
    }

    @Test
    @DisplayName("legacy base URLs ending with /rest/api/3 are normalised")
    void normalisesLegacyBaseUrl() {
        assertThat(JiraRestClient.normaliseBaseUrl("https://acme.atlassian.net/rest/api/3/"))
                .isEqualTo("https://acme.atlassian.net");
        assertThat(JiraRestClient.normaliseBaseUrl("https://acme.atlassian.net/"))
                .isEqualTo("https://acme.atlassian.net");
    }

    private MockResponse jsonResponse(String body) {
        return new MockResponse()
                .setResponseCode(200)
                .setHeader("Content-Type", "application/json")
                .setBody(body);
    }
}
