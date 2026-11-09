package com.asecurityguru.jiratestgen.ai.model;

/** Requested generation settings, already validated by the service layer. */
public record GenerationOptions(TestLanguage language, TestFormat format, int maxTestCases) {
}
