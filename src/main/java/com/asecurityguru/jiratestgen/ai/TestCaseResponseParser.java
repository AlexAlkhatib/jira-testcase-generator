package com.asecurityguru.jiratestgen.ai;

import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;

import org.springframework.stereotype.Component;
import org.springframework.util.StringUtils;

import com.asecurityguru.jiratestgen.ai.model.TestCase;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

/**
 * Parses the model answer into {@link TestCase} objects.
 *
 * <p>Local models are not always compliant: they may wrap JSON in a markdown fence, return a
 * bare array, rename a field, or append a sentence. The parser is intentionally lenient and
 * never throws on a partially valid payload; callers decide what to do with an empty result.</p>
 */
@Component
public class TestCaseResponseParser {

    private final ObjectMapper objectMapper;

    public TestCaseResponseParser(ObjectMapper objectMapper) {
        this.objectMapper = objectMapper;
    }

    public List<TestCase> parse(String rawResponse) {
        if (!StringUtils.hasText(rawResponse)) {
            return List.of();
        }
        String json = extractJson(rawResponse);
        if (!StringUtils.hasText(json)) {
            return List.of();
        }

        JsonNode root;
        try {
            root = objectMapper.readTree(json);
        } catch (JsonProcessingException e) {
            return List.of();
        }

        JsonNode array = findArray(root);
        if (array == null) {
            return List.of();
        }

        List<TestCase> cases = new ArrayList<>();
        int index = 1;
        for (JsonNode node : array) {
            TestCase testCase = mapCase(node, index);
            if (testCase != null) {
                cases.add(testCase);
                index++;
            }
        }
        return cases;
    }

    private JsonNode findArray(JsonNode root) {
        if (root == null) {
            return null;
        }
        if (root.isArray()) {
            return root;
        }
        for (String field : List.of("testCases", "test_cases", "cases", "tests", "results")) {
            JsonNode candidate = root.get(field);
            if (candidate != null && candidate.isArray()) {
                return candidate;
            }
        }
        // Some models nest everything under "data" or a single test case object.
        for (String field : List.of("data", "result", "output")) {
            JsonNode candidate = root.get(field);
            if (candidate != null) {
                JsonNode nested = findArray(candidate);
                if (nested != null) {
                    return nested;
                }
            }
        }
        return root.has("title") || root.has("steps") ? objectMapper.createArrayNode().add(root) : null;
    }

    private TestCase mapCase(JsonNode node, int index) {
        if (node == null || !node.isObject()) {
            return null;
        }

        String title = firstText(node, "title", "name", "description", "summary", "testCaseDescription");
        List<String> steps = textList(node, "steps", "testSteps", "test_steps", "actions");
        if (title == null && steps.isEmpty()) {
            return null;
        }
        if (title == null) {
            title = "Test case " + index;
        }

        String id = firstText(node, "id", "testCaseId", "test_case_id", "key");
        if (!StringUtils.hasText(id)) {
            id = String.format("TC-%03d", index);
        }

        return new TestCase(
                id.trim(),
                title.trim(),
                defaultValue(firstText(node, "type", "category", "testType"), "Fonctionnel"),
                defaultValue(firstText(node, "priority", "severity"), "Moyenne"),
                textList(node, "preconditions", "preConditions", "pre_conditions", "prerequisites"),
                steps,
                textList(node, "testData", "test_data", "data", "inputs"),
                defaultValue(firstText(node, "expectedResult", "expected_result", "expected", "expectedOutcome"),
                        ""));
    }

    private String firstText(JsonNode node, String... fields) {
        for (String field : fields) {
            JsonNode value = node.get(field);
            if (value != null && value.isValueNode() && StringUtils.hasText(value.asText())) {
                return value.asText();
            }
        }
        return null;
    }

    private List<String> textList(JsonNode node, String... fields) {
        for (String field : fields) {
            JsonNode value = node.get(field);
            if (value == null) {
                continue;
            }
            if (value.isArray()) {
                List<String> items = new ArrayList<>();
                Iterator<JsonNode> it = value.elements();
                while (it.hasNext()) {
                    JsonNode item = it.next();
                    if (item.isValueNode()) {
                        addIfMeaningful(items, item.asText());
                    } else if (item.isObject()) {
                        String text = firstText(item, "step", "action", "description", "value", "text");
                        addIfMeaningful(items, text);
                    }
                }
                if (!items.isEmpty()) {
                    return items;
                }
            }
            if (value.isTextual()) {
                List<String> items = new ArrayList<>();
                for (String line : value.asText().split("\\r?\\n")) {
                    addIfMeaningful(items, line);
                }
                if (!items.isEmpty()) {
                    return items;
                }
            }
        }
        return List.of();
    }

    private void addIfMeaningful(List<String> target, String raw) {
        if (!StringUtils.hasText(raw)) {
            return;
        }
        String cleaned = raw.trim().replaceFirst("^(?:\\d+[.)]|[-*•])\\s*", "").trim();
        if (!cleaned.isEmpty()) {
            target.add(cleaned);
        }
    }

    private String defaultValue(String value, String fallback) {
        return StringUtils.hasText(value) ? value.trim() : fallback;
    }

    /** Extracts the first JSON object/array from a possibly fenced or chatty answer. */
    String extractJson(String raw) {
        String text = raw.trim();
        int fence = text.indexOf("```");
        if (fence >= 0) {
            int firstLineEnd = text.indexOf('\n', fence);
            int closing = text.indexOf("```", fence + 3);
            if (firstLineEnd > 0 && closing > firstLineEnd) {
                String fenced = text.substring(firstLineEnd + 1, closing).trim();
                if (fenced.startsWith("{") || fenced.startsWith("[")) {
                    text = fenced;
                }
            }
        }

        int startObject = text.indexOf('{');
        int startArray = text.indexOf('[');
        int start;
        if (startObject < 0) {
            start = startArray;
        } else if (startArray < 0) {
            start = startObject;
        } else {
            start = Math.min(startObject, startArray);
        }
        if (start < 0) {
            return "";
        }

        char open = text.charAt(start);
        char close = open == '{' ? '}' : ']';
        int end = text.lastIndexOf(close);
        if (end <= start) {
            return "";
        }
        return text.substring(start, end + 1);
    }

    /** Small helper used by the UI: a safe preview of an unusable answer. */
    public String preview(String rawResponse) {
        if (rawResponse == null) {
            return "";
        }
        String compact = rawResponse.replaceAll("\\s+", " ").trim();
        return compact.length() <= 140 ? compact : compact.substring(0, 140) + "...";
    }
}
