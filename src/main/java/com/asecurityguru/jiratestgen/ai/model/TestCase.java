package com.asecurityguru.jiratestgen.ai.model;

import java.util.List;

/**
 * A single functional test case produced by the model.
 *
 * @param id             stable identifier, e.g. {@code TC-001}
 * @param title          short intent of the test
 * @param type           Functional, Negative, Boundary, Security...
 * @param priority       High / Medium / Low (localised)
 * @param preconditions  state required before the test
 * @param steps          ordered actions (imperative or Gherkin)
 * @param testData       concrete values to use
 * @param expectedResult observable outcome
 */
public record TestCase(
        String id,
        String title,
        String type,
        String priority,
        List<String> preconditions,
        List<String> steps,
        List<String> testData,
        String expectedResult) {

    public TestCase {
        preconditions = preconditions == null ? List.of() : List.copyOf(preconditions);
        steps = steps == null ? List.of() : List.copyOf(steps);
        testData = testData == null ? List.of() : List.copyOf(testData);
    }
}
