package com.asecurityguru.jiratestgen.ai.model;

import java.util.List;

/**
 * Raw result of one generation call.
 *
 * @param testCases  parsed and truncated test cases
 * @param model      Ollama model name
 * @param durationMs end-to-end generation time
 * @param warnings   non-blocking information (truncation, missing acceptance criteria...)
 * @param rawResponse model output, kept for auditing and troubleshooting
 */
public record GeneratedTestCases(
        List<TestCase> testCases,
        String model,
        long durationMs,
        List<String> warnings,
        String rawResponse) {
}
