package com.asecurityguru.jiratestgen.jira;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

class AdfTextExtractorTest {

    private final ObjectMapper objectMapper = new ObjectMapper();
    private final AdfTextExtractor extractor = new AdfTextExtractor();

    @Test
    @DisplayName("plain string descriptions (Jira Server v2) are returned as-is")
    void handlesPlainText() {
        assertThat(extractor.toPlainText("As a user\nI want to log in")).isEqualTo("As a user\nI want to log in");
    }

    @Test
    @DisplayName("null and missing nodes produce an empty string")
    void handlesNull() {
        assertThat(extractor.toPlainText((JsonNode) null)).isEmpty();
        assertThat(extractor.toPlainText((String) null)).isEmpty();
    }

    @Test
    @DisplayName("Atlassian Document Format paragraphs, headings and bullets are flattened")
    void handlesAdf() throws Exception {
        JsonNode doc = objectMapper.readTree("""
                {
                  "type": "doc",
                  "version": 1,
                  "content": [
                    {"type": "heading", "attrs": {"level": 3}, "content": [{"type": "text", "text": "Acceptance Criteria"}]},
                    {"type": "paragraph", "content": [{"type": "text", "text": "The user can log in."}, {"type": "hardBreak"}, {"type": "text", "text": "An error is shown otherwise."}]},
                    {"type": "bulletList", "content": [
                      {"type": "listItem", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Email is valid"}]}]},
                      {"type": "listItem", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Password is valid"}]}]}
                    ]}
                  ]
                }
                """);

        String text = extractor.toPlainText(doc);

        assertThat(text)
                .contains("Acceptance Criteria")
                .contains("The user can log in.")
                .contains("An error is shown otherwise.")
                .contains("- Email is valid")
                .contains("- Password is valid");
    }

    @Test
    @DisplayName("unknown nodes are traversed instead of dropped")
    void traversesUnknownNodes() throws Exception {
        JsonNode node = objectMapper.readTree("""
                {"type": "panel", "content": [
                  {"type": "paragraph", "content": [{"type": "text", "text": "Inside a panel"}]}
                ]}
                """);

        assertThat(extractor.toPlainText(node)).contains("Inside a panel");
    }
}
