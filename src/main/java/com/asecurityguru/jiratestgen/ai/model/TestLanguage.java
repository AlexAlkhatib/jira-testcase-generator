package com.asecurityguru.jiratestgen.ai.model;

import java.util.Locale;

/** Output language of the generated test cases. */
public enum TestLanguage {

    FR("French", "français"),
    EN("English", "anglais");

    private final String englishName;
    private final String frenchName;

    TestLanguage(String englishName, String frenchName) {
        this.englishName = englishName;
        this.frenchName = frenchName;
    }

    public String instruction() {
        return this == FR
                ? "Write every human-readable value (title, steps, expected result, test data) in French."
                : "Write every human-readable value (title, steps, expected result, test data) in English.";
    }

    public String label() {
        return this == FR ? frenchName : englishName;
    }

    public static TestLanguage from(String value) {
        return value == null ? FR : TestLanguage.valueOf(value.trim().toUpperCase(Locale.ROOT));
    }
}
