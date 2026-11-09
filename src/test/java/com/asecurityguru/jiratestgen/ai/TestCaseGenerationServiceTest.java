package com.asecurityguru.jiratestgen.ai;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import java.util.List;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.ai.chat.messages.AssistantMessage;
import org.springframework.ai.chat.model.ChatModel;
import org.springframework.ai.chat.model.ChatResponse;
import org.springframework.ai.chat.model.Generation;
import org.springframework.ai.chat.prompt.Prompt;
import org.springframework.ai.chat.client.ChatClient;

import com.asecurityguru.jiratestgen.ai.model.GeneratedTestCases;
import com.asecurityguru.jiratestgen.ai.model.GenerationOptions;
import com.asecurityguru.jiratestgen.ai.model.TestFormat;
import com.asecurityguru.jiratestgen.ai.model.TestLanguage;
import com.asecurityguru.jiratestgen.config.GenerationProperties;
import com.asecurityguru.jiratestgen.error.AiResponseInvalidException;
import com.asecurityguru.jiratestgen.error.AiUnavailableException;
import com.asecurityguru.jiratestgen.jira.JiraStory;

class TestCaseGenerationServiceTest {

    private static final String THREE_CASES = """
            {"testCases": [
              {"id": "TC-001", "title": "Nominal", "steps": ["step one"], "expectedResult": "ok"},
              {"id": "TC-002", "title": "Negative", "steps": ["step two"], "expectedResult": "error"},
              {"id": "TC-003", "title": "Boundary", "steps": ["step three"], "expectedResult": "limit"}
            ]}
            """;

    private GenerationProperties properties;
    private JiraStory story;

    @BeforeEach
    void setUp() {
        properties = new GenerationProperties();
        properties.setMaxTestCases(20);
        properties.setMaxStoryCharacters(8000);
        story = new JiraStory("KAN-3", "Login", "Story", "To Do",
                "As a user I want to log in.", "Valid credentials work.", "description",
                "https://acme.atlassian.net/browse/KAN-3");
    }

    private TestCaseGenerationService service(ChatModel chatModel) {
        return new TestCaseGenerationService(
                ChatClient.builder(chatModel).build(),
                new PromptFactory(properties),
                new TestCaseResponseParser(new com.fasterxml.jackson.databind.ObjectMapper()),
                properties,
                "mistral-test");
    }

    private ChatModel answering(String content) {
        return new ChatModel() {
            @Override
            public ChatResponse call(Prompt prompt) {
                return new ChatResponse(List.of(new Generation(new AssistantMessage(content))));
            }
        };
    }

    private GenerationOptions options(int max) {
        return new GenerationOptions(TestLanguage.FR, TestFormat.STANDARD, max);
    }

    @Test
    @DisplayName("a valid model answer is parsed into test cases")
    void generatesTestCases() {
        GeneratedTestCases result = service(answering(THREE_CASES)).generate(story, options(8));

        assertThat(result.testCases()).hasSize(3);
        assertThat(result.model()).isEqualTo("mistral-test");
        assertThat(result.warnings()).isEmpty();
        assertThat(result.rawResponse()).contains("TC-001");
    }

    @Test
    @DisplayName("extra cases are truncated to the requested limit with a warning")
    void truncatesToRequestedCount() {
        GeneratedTestCases result = service(answering(THREE_CASES)).generate(story, options(2));

        assertThat(result.testCases()).hasSize(2);
        assertThat(result.warnings()).anyMatch(w -> w.contains("limite"));
    }

    @Test
    @DisplayName("the configured maximum is enforced even if the caller asks for more")
    void enforcesGlobalMaximum() {
        properties.setMaxTestCases(10);

        GeneratedTestCases result = service(answering(THREE_CASES)).generate(story, options(99));

        assertThat(result.testCases()).hasSize(3);
    }

    @Test
    @DisplayName("a non-JSON answer becomes AI_RESPONSE_INVALID")
    void rejectsInvalidAnswer() {
        assertThatThrownBy(() -> service(answering("I am sorry, I cannot do that.")).generate(story, options(5)))
                .isInstanceOf(AiResponseInvalidException.class)
                .hasMessageContaining("aucun cas de test JSON");
    }

    @Test
    @DisplayName("a model failure becomes AI_UNAVAILABLE with a remediation hint")
    void mapsModelFailure() {
        ChatModel failing = new ChatModel() {
            @Override
            public ChatResponse call(Prompt prompt) {
                throw new IllegalStateException("connection refused");
            }
        };

        assertThatThrownBy(() -> service(failing).generate(story, options(5)))
                .isInstanceOf(AiUnavailableException.class)
                .hasMessageContaining("Ollama");
    }

    @Test
    @DisplayName("a missing acceptance criteria section produces a non-blocking warning")
    void warnsWhenCriteriaMissing() {
        JiraStory withoutCriteria = new JiraStory("KAN-9", "Title", "Story", "To Do",
                "", "", "description", "https://acme.atlassian.net/browse/KAN-9");

        GeneratedTestCases result = service(answering(THREE_CASES)).generate(withoutCriteria, options(5));

        assertThat(result.warnings()).anyMatch(w -> w.contains("critère"));
    }
}
