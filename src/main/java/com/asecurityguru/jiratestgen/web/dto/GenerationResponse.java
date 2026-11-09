package com.asecurityguru.jiratestgen.web.dto;

import java.time.Instant;
import java.util.List;

import com.asecurityguru.jiratestgen.ai.model.TestCase;

/**
 * Public contract of {@code GET /api/v1/test-cases}.
 *
 * <p>A typed payload replaces the former free-text answer: clients can now display, export
 * and assert on the result instead of parsing a chat response.</p>
 */
public record GenerationResponse(
        Story story,
        Generation generation,
        List<TestCase> testCases,
        List<String> warnings) {

    public record Story(
            String key,
            String summary,
            String issueType,
            String status,
            String url,
            String description,
            String acceptanceCriteria,
            String acceptanceCriteriaSource) {
    }

    public record Generation(
            String model,
            String language,
            String format,
            Instant generatedAt,
            long durationMs,
            int testCaseCount) {
    }
}
