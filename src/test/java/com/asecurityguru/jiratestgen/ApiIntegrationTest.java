package com.asecurityguru.jiratestgen;

import static org.assertj.core.api.Assertions.assertThat;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.List;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.ai.chat.messages.AssistantMessage;
import org.springframework.ai.chat.model.ChatModel;
import org.springframework.ai.chat.model.ChatResponse;
import org.springframework.ai.chat.model.Generation;
import org.springframework.ai.chat.prompt.Prompt;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.context.TestConfiguration;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Primary;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

import okhttp3.mockwebserver.Dispatcher;
import okhttp3.mockwebserver.MockResponse;
import okhttp3.mockwebserver.MockWebServer;
import okhttp3.mockwebserver.RecordedRequest;

/**
 * Full-stack test: HTTP layer -> service -> Jira REST client (stubbed) -> Spring AI ChatClient
 * (fake model) -> JSON contract. No Ollama instance and no Jira tenant are required.
 */
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT, properties = {
        "spring.ai.ollama.chat.options.model=mistral-test",
        "app.jira.email=qa@example.com",
        "app.jira.api-token=test-token",
        "app.jira.api-version=3",
        "app.generation.max-test-cases=20",
        "app.generation.default-test-cases=8",
        "management.endpoints.web.exposure.include=health"
})
class ApiIntegrationTest {

    private static final String MODEL_ANSWER = """
            {"testCases": [
              {"id": "TC-001", "title": "Connexion avec des identifiants valides", "type": "Fonctionnel",
               "priority": "Haute", "preconditions": ["Compte confirmé"],
               "steps": ["Ouvrir la page de connexion", "Saisir un email et un mot de passe valides"],
               "testData": ["email = qa@example.com"], "expectedResult": "Le tableau de bord est affiché"},
              {"id": "TC-002", "title": "Connexion avec un mot de passe invalide", "type": "Négatif",
               "priority": "Haute", "preconditions": ["Compte confirmé"],
               "steps": ["Saisir un mot de passe erroné"], "testData": [],
               "expectedResult": "Un message d'erreur générique est affiché"},
              {"id": "TC-003", "title": "Champ email vide", "type": "Limite",
               "priority": "Moyenne", "preconditions": [], "steps": ["Valider le formulaire vide"],
               "testData": [], "expectedResult": "Les champs obligatoires sont signalés"}
            ]}
            """;

    private static final MockWebServer JIRA = new MockWebServer();

    static {
        try {
            JIRA.start();
            JIRA.setDispatcher(new Dispatcher() {
                @Override
                public MockResponse dispatch(RecordedRequest request) {
                    String path = request.getPath() == null ? "" : request.getPath();
                    if (path.contains("/issue/KAN-404")) {
                        return new MockResponse().setResponseCode(404)
                                .setHeader("Content-Type", "application/json")
                                .setBody("{\"errorMessages\":[\"Issue does not exist\"]}");
                    }
                    if (path.contains("/issue/KAN-3")) {
                        return new MockResponse().setResponseCode(200)
                                .setHeader("Content-Type", "application/json")
                                .setBody("""
                                        {
                                          "key": "KAN-3",
                                          "fields": {
                                            "summary": "Connexion utilisateur",
                                            "issuetype": {"name": "Story"},
                                            "status": {"name": "To Do"},
                                            "description": {
                                              "type": "doc", "version": 1,
                                              "content": [
                                                {"type": "heading", "attrs": {"level": 2},
                                                 "content": [{"type": "text", "text": "Critères d'acceptation"}]},
                                                {"type": "bulletList", "content": [
                                                  {"type": "listItem", "content": [{"type": "paragraph",
                                                    "content": [{"type": "text", "text": "Un email et un mot de passe valides connectent l'utilisateur"}]}]},
                                                  {"type": "listItem", "content": [{"type": "paragraph",
                                                    "content": [{"type": "text", "text": "Un mot de passe invalide affiche une erreur"}]}]}
                                                ]}
                                              ]
                                            }
                                          }
                                        }
                                        """);
                    }
                    return new MockResponse().setResponseCode(500);
                }
            });
        } catch (IOException e) {
            throw new UncheckedIOException(e);
        }
    }

    @DynamicPropertySource
    static void jiraProperties(DynamicPropertyRegistry registry) {
        registry.add("app.jira.base-url", () -> JIRA.url("/").toString());
    }

    @TestConfiguration
    static class FakeAiConfiguration {
        @Bean
        @Primary
        ChatModel chatModel() {
            return new ChatModel() {
                @Override
                public ChatResponse call(Prompt prompt) {
                    return new ChatResponse(List.of(new Generation(new AssistantMessage(MODEL_ANSWER))));
                }
            };
        }
    }

    @Autowired
    private TestRestTemplate rest;

    @Autowired
    private ObjectMapper objectMapper;

    @Test
    @DisplayName("GET /api/v1/test-cases returns the structured contract end to end")
    void generatesTestCasesOverHttp() throws Exception {
        ResponseEntity<String> response = rest.getForEntity(
                "/api/v1/test-cases?storyKey=kan-3&language=fr&format=STANDARD&maxCases=8", String.class);

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
        JsonNode body = objectMapper.readTree(response.getBody());
        assertThat(body.at("/story/key").asText()).isEqualTo("KAN-3");
        assertThat(body.at("/story/summary").asText()).isEqualTo("Connexion utilisateur");
        assertThat(body.at("/story/acceptanceCriteria").asText())
                .contains("Un email et un mot de passe valides connectent l'utilisateur");
        assertThat(body.at("/generation/model").asText()).isEqualTo("mistral-test");
        assertThat(body.at("/generation/language").asText()).isEqualTo("FR");
        assertThat(body.at("/testCases")).hasSize(3);
        assertThat(body.at("/testCases/0/id").asText()).isEqualTo("TC-001");
        assertThat(body.at("/testCases/0/steps/1").asText()).contains("mot de passe");
        assertThat(body.at("/testCases/1/type").asText()).isEqualTo("Négatif");
    }

    @Test
    @DisplayName("maxCases truncates the answer and reports a warning")
    void respectsMaxCases() throws Exception {
        ResponseEntity<String> response = rest.getForEntity(
                "/api/v1/test-cases?storyKey=KAN-3&maxCases=2", String.class);

        JsonNode body = objectMapper.readTree(response.getBody());
        assertThat(body.at("/testCases")).hasSize(2);
        assertThat(body.at("/warnings/0").asText()).contains("limite");
    }

    @Test
    @DisplayName("the legacy /api/v1/jira-story endpoint still works")
    void legacyAliasStillWorks() {
        ResponseEntity<String> response = rest.getForEntity("/api/v1/jira-story?storyKey=KAN-3", String.class);

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(response.getBody()).contains("\"testCases\"");
    }

    @Test
    @DisplayName("an unknown story returns a 404 problem+json with a stable code")
    void unknownStoryReturns404() throws Exception {
        ResponseEntity<String> response = rest.getForEntity("/api/v1/test-cases?storyKey=KAN-404", String.class);

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.NOT_FOUND);
        assertThat(response.getHeaders().getContentType().toString()).contains("problem+json");
        JsonNode body = objectMapper.readTree(response.getBody());
        assertThat(body.at("/code").asText()).isEqualTo("STORY_NOT_FOUND");
        assertThat(body.at("/status").asInt()).isEqualTo(404);
    }

    @Test
    @DisplayName("an invalid key is rejected with 400 before any upstream call")
    void invalidKeyReturns400() throws Exception {
        ResponseEntity<String> response = rest.getForEntity("/api/v1/test-cases?storyKey=not-a-key", String.class);

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.BAD_REQUEST);
        JsonNode body = objectMapper.readTree(response.getBody());
        assertThat(body.at("/code").asText()).isEqualTo("VALIDATION_ERROR");
    }

    @Test
    @DisplayName("missing parameters and unknown enum values are rejected with 400")
    void validatesParameters() throws Exception {
        ResponseEntity<String> missing = rest.getForEntity("/api/v1/test-cases", String.class);
        assertThat(missing.getStatusCode()).isEqualTo(HttpStatus.BAD_REQUEST);
        assertThat(objectMapper.readTree(missing.getBody()).at("/code").asText()).isEqualTo("VALIDATION_ERROR");

        ResponseEntity<String> badLanguage = rest.getForEntity(
                "/api/v1/test-cases?storyKey=KAN-3&language=IT", String.class);
        assertThat(badLanguage.getStatusCode()).isEqualTo(HttpStatus.BAD_REQUEST);

        ResponseEntity<String> badCount = rest.getForEntity(
                "/api/v1/test-cases?storyKey=KAN-3&maxCases=99", String.class);
        assertThat(badCount.getStatusCode()).isEqualTo(HttpStatus.BAD_REQUEST);
    }

    @Test
    @DisplayName("/api/v1/config exposes the setup state without any secret")
    void configEndpointIsSafe() throws Exception {
        ResponseEntity<String> response = rest.getForEntity("/api/v1/config", String.class);

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
        JsonNode body = objectMapper.readTree(response.getBody());
        assertThat(body.at("/jiraConfigured").asBoolean()).isTrue();
        assertThat(body.at("/model").asText()).isEqualTo("mistral-test");
        assertThat(body.toString()).doesNotContain("test-token").doesNotContain("qa@example.com");
    }

    @Test
    @DisplayName("the health endpoint and the web UI are served")
    void servesHealthAndUi() {
        ResponseEntity<String> health = rest.getForEntity("/actuator/health", String.class);
        assertThat(health.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(health.getBody()).contains("UP");

        ResponseEntity<String> ui = rest.getForEntity("/", String.class);
        assertThat(ui.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(ui.getBody()).contains("Jira Test Case Generator").contains("/js/app.js");
    }
}
