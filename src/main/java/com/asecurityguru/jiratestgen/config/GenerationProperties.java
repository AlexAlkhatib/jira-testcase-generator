package com.asecurityguru.jiratestgen.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

/**
 * Limits and defaults for the test case generation pipeline.
 */
@ConfigurationProperties(prefix = "app.generation")
public class GenerationProperties {

    /** Maximum number of characters of story context sent to the model (prompt-injection and cost guard). */
    private int maxStoryCharacters = 8000;

    /** Hard upper bound on generated test cases (protects the model and the API). */
    private int maxTestCases = 20;

    /** Default number of test cases when the caller does not specify one. */
    private int defaultTestCases = 8;

    public int getMaxStoryCharacters() {
        return maxStoryCharacters;
    }

    public void setMaxStoryCharacters(int maxStoryCharacters) {
        this.maxStoryCharacters = maxStoryCharacters;
    }

    public int getMaxTestCases() {
        return maxTestCases;
    }

    public void setMaxTestCases(int maxTestCases) {
        this.maxTestCases = maxTestCases;
    }

    public int getDefaultTestCases() {
        return defaultTestCases;
    }

    public void setDefaultTestCases(int defaultTestCases) {
        this.defaultTestCases = defaultTestCases;
    }
}
