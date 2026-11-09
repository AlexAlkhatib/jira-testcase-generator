package com.asecurityguru.jiratestgen.ai;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import com.asecurityguru.jiratestgen.ai.model.GenerationOptions;
import com.asecurityguru.jiratestgen.ai.model.TestFormat;
import com.asecurityguru.jiratestgen.ai.model.TestLanguage;
import com.asecurityguru.jiratestgen.config.GenerationProperties;
import com.asecurityguru.jiratestgen.jira.JiraStory;

class PromptFactoryTest {

    private final GenerationProperties properties = new GenerationProperties();
    private final PromptFactory factory = new PromptFactory(properties);

    private JiraStory story(String criteria) {
        return new JiraStory("KAN-3", "User login", "Story", "To Do",
                "As a user I want to log in.", criteria, "description", "https://acme.atlassian.net/browse/KAN-3");
    }

    @Test
    @DisplayName("the prompt contains the story data, the count and the JSON contract")
    void buildsPrompt() {
        PromptFactory.Prompt prompt = factory.build(story("AC1: valid credentials work"),
                new GenerationOptions(TestLanguage.FR, TestFormat.STANDARD, 5));

        assertThat(prompt.user())
                .contains("KAN-3")
                .contains("User login")
                .contains("AC1: valid credentials work")
                .contains("Generate 5");
        assertThat(prompt.system())
                .contains("\"testCases\"")
                .contains("untrusted DATA")
                .contains("French")
                .contains("imperative");
    }

    @Test
    @DisplayName("Gherkin format and English output change the instructions")
    void supportsGherkinAndEnglish() {
        PromptFactory.Prompt prompt = factory.build(story("AC1"),
                new GenerationOptions(TestLanguage.EN, TestFormat.GHERKIN, 3));

        assertThat(prompt.system()).contains("Given, When or Then").contains("in English");
        assertThat(prompt.user()).contains("Gherkin");
    }

    @Test
    @DisplayName("long descriptions are truncated before being sent to the model")
    void truncatesLongDescriptions() {
        properties.setMaxStoryCharacters(50);
        String huge = "x".repeat(500);

        PromptFactory.Prompt prompt = factory.build(story(huge),
                new GenerationOptions(TestLanguage.FR, TestFormat.STANDARD, 4));

        assertThat(prompt.user()).contains("[... truncated ...]");
        assertThat(prompt.user().length()).isLessThan(huge.length() + 1500);
    }

    @Test
    @DisplayName("missing acceptance criteria are clearly announced to the model")
    void handlesMissingCriteria() {
        PromptFactory.Prompt prompt = factory.build(story(""),
                new GenerationOptions(TestLanguage.FR, TestFormat.STANDARD, 4));

        assertThat(prompt.user()).contains("(no acceptance criteria provided)");
    }
}
