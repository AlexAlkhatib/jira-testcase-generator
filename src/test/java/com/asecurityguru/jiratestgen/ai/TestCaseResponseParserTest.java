package com.asecurityguru.jiratestgen.ai;

import static org.assertj.core.api.Assertions.assertThat;

import java.util.List;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import com.asecurityguru.jiratestgen.ai.model.TestCase;
import com.fasterxml.jackson.databind.ObjectMapper;

class TestCaseResponseParserTest {

    private final TestCaseResponseParser parser = new TestCaseResponseParser(new ObjectMapper());

    @Test
    @DisplayName("a markdown-fenced JSON answer is parsed")
    void parsesFencedJson() {
        String raw = """
                Here are your test cases:
                ```json
                {"testCases": [
                  {"id": "TC-001", "title": "Login with valid credentials", "type": "Fonctionnel",
                   "priority": "Haute", "preconditions": ["A confirmed account"],
                   "steps": ["Open the login page", "Submit valid credentials"],
                   "testData": ["email = qa@example.com"], "expectedResult": "The dashboard is displayed"}
                ]}
                ```
                """;

        List<TestCase> cases = parser.parse(raw);

        assertThat(cases).hasSize(1);
        TestCase testCase = cases.get(0);
        assertThat(testCase.id()).isEqualTo("TC-001");
        assertThat(testCase.title()).isEqualTo("Login with valid credentials");
        assertThat(testCase.priority()).isEqualTo("Haute");
        assertThat(testCase.preconditions()).containsExactly("A confirmed account");
        assertThat(testCase.steps()).hasSize(2);
        assertThat(testCase.expectedResult()).isEqualTo("The dashboard is displayed");
    }

    @Test
    @DisplayName("a bare JSON array is accepted")
    void parsesBareArray() {
        String raw = """
                [{"title": "Negative login", "steps": ["Enter a wrong password"],
                  "expectedResult": "An error message is shown"}]
                """;

        List<TestCase> cases = parser.parse(raw);

        assertThat(cases).hasSize(1);
        assertThat(cases.get(0).id()).isEqualTo("TC-001");
        assertThat(cases.get(0).type()).isEqualTo("Fonctionnel");
        assertThat(cases.get(0).priority()).isEqualTo("Moyenne");
    }

    @Test
    @DisplayName("field aliases and numbered multi-line steps are supported")
    void supportsAliases() {
        String raw = """
                {"test_cases": [{"testCaseId": "TC-7", "description": "Boundary upload",
                  "steps": "1. Upload a 10 MB file\\n2. Upload a 10.1 MB file",
                  "expected_result": "The first succeeds, the second is rejected"}]}
                """;

        List<TestCase> cases = parser.parse(raw);

        assertThat(cases).hasSize(1);
        assertThat(cases.get(0).id()).isEqualTo("TC-7");
        assertThat(cases.get(0).title()).isEqualTo("Boundary upload");
        assertThat(cases.get(0).steps()).containsExactly("Upload a 10 MB file", "Upload a 10.1 MB file");
        assertThat(cases.get(0).expectedResult()).isEqualTo("The first succeeds, the second is rejected");
    }

    @Test
    @DisplayName("non-JSON answers produce an empty list instead of an exception")
    void returnsEmptyForNonJson() {
        assertThat(parser.parse("I cannot help with that request.")).isEmpty();
        assertThat(parser.parse("")).isEmpty();
        assertThat(parser.parse(null)).isEmpty();
        assertThat(parser.parse("{\"testCases\": []}")).isEmpty();
    }

    @Test
    @DisplayName("a JSON object surrounded by prose is still extracted")
    void extractsEmbeddedJson() {
        String raw = "Sure. {\"testCases\": [{\"title\": \"Smoke\", \"steps\": [\"Open the app\"]}]} Hope it helps!";

        assertThat(parser.parse(raw)).hasSize(1);
        assertThat(parser.parse(raw).get(0).title()).isEqualTo("Smoke");
    }

    @Test
    @DisplayName("invalid entries are skipped without losing valid ones")
    void skipsInvalidEntries() {
        String raw = """
                {"testCases": [{"id": "TC-1", "steps": ["Do something"]}, {"foo": "bar"}]}
                """;

        assertThat(parser.parse(raw)).hasSize(1);
    }
}
