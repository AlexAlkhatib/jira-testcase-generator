package com.asecurityguru.jiratestgen.jira;

/**
 * Immutable view of the Jira data needed to generate test cases.
 *
 * @param key                issue key, e.g. {@code KAN-3}
 * @param summary            issue title
 * @param issueType          issue type name (Story, Bug, Task...)
 * @param status             workflow status name
 * @param description        full description flattened to plain text
 * @param acceptanceCriteria extracted acceptance criteria (description section or custom field)
 * @param acceptanceCriteriaSource how the criteria were obtained, for observability
 * @param url                browsable issue URL
 */
public record JiraStory(
        String key,
        String summary,
        String issueType,
        String status,
        String description,
        String acceptanceCriteria,
        String acceptanceCriteriaSource,
        String url) {
}
