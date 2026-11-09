package com.asecurityguru.jiratestgen.ai.model;

import java.util.Locale;

/** Presentation format expected for the steps of each test case. */
public enum TestFormat {

    STANDARD("imperative steps"),
    GHERKIN("Given/When/Then steps");

    private final String description;

    TestFormat(String description) {
        this.description = description;
    }

    public String description() {
        return description;
    }

    public static TestFormat from(String value) {
        return value == null ? STANDARD : TestFormat.valueOf(value.trim().toUpperCase(Locale.ROOT));
    }
}
