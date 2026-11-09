package com.asecurityguru.jiratestgen.service;

import java.time.Instant;
import java.util.Locale;
import java.util.regex.Pattern;

import org.springframework.stereotype.Service;

import com.asecurityguru.jiratestgen.ai.TestCaseGenerationService;
import com.asecurityguru.jiratestgen.ai.model.GeneratedTestCases;
import com.asecurityguru.jiratestgen.ai.model.GenerationOptions;
import com.asecurityguru.jiratestgen.ai.model.TestFormat;
import com.asecurityguru.jiratestgen.ai.model.TestLanguage;
import com.asecurityguru.jiratestgen.config.GenerationProperties;
import com.asecurityguru.jiratestgen.error.InvalidRequestException;
import com.asecurityguru.jiratestgen.jira.JiraStory;
import com.asecurityguru.jiratestgen.jira.JiraStoryClient;
import com.asecurityguru.jiratestgen.web.dto.GenerationResponse;

/**
 * Application service: validate the request, read the story, generate the cases and map
 * everything to the public response.
 */
@Service
public class TestSuiteService {

    /** Jira keys are project key (letters/digits/underscore) + '-' + numeric id. */
    private static final Pattern STORY_KEY_PATTERN = Pattern.compile("^[A-Za-z][A-Za-z0-9_]*-[0-9]+$");

    private final JiraStoryClient jiraStoryClient;
    private final TestCaseGenerationService generationService;
    private final GenerationProperties properties;

    public TestSuiteService(JiraStoryClient jiraStoryClient,
                            TestCaseGenerationService generationService,
                            GenerationProperties properties) {
        this.jiraStoryClient = jiraStoryClient;
        this.generationService = generationService;
        this.properties = properties;
    }

    public GenerationResponse generate(String rawStoryKey, String rawLanguage, String rawFormat, Integer requestedCount) {
        String storyKey = normaliseStoryKey(rawStoryKey);
        TestLanguage language = parseLanguage(rawLanguage);
        TestFormat format = parseFormat(rawFormat);
        int count = resolveCount(requestedCount);

        JiraStory story = jiraStoryClient.fetch(storyKey);
        GeneratedTestCases generated = generationService.generate(
                story, new GenerationOptions(language, format, count));

        return new GenerationResponse(
                new GenerationResponse.Story(
                        story.key(),
                        story.summary(),
                        story.issueType(),
                        story.status(),
                        story.url(),
                        story.description(),
                        story.acceptanceCriteria(),
                        story.acceptanceCriteriaSource()),
                new GenerationResponse.Generation(
                        generated.model(),
                        language.name(),
                        format.name(),
                        Instant.now(),
                        generated.durationMs(),
                        generated.testCases().size()),
                generated.testCases(),
                generated.warnings());
    }

    String normaliseStoryKey(String rawStoryKey) {
        if (rawStoryKey == null || rawStoryKey.isBlank()) {
            throw new InvalidRequestException("Le paramètre 'storyKey' est obligatoire (exemple : KAN-3).");
        }
        String storyKey = rawStoryKey.trim().toUpperCase(Locale.ROOT);
        if (!STORY_KEY_PATTERN.matcher(storyKey).matches()) {
            throw new InvalidRequestException(
                    "Clé de story invalide : '" + rawStoryKey + "'. Format attendu : PROJET-123 (ex. KAN-3).");
        }
        return storyKey;
    }

    TestLanguage parseLanguage(String rawLanguage) {
        if (rawLanguage == null || rawLanguage.isBlank()) {
            return TestLanguage.FR;
        }
        try {
            return TestLanguage.from(rawLanguage);
        } catch (IllegalArgumentException e) {
            throw new InvalidRequestException("Langue inconnue : '" + rawLanguage + "'. Valeurs acceptées : FR, EN.");
        }
    }

    TestFormat parseFormat(String rawFormat) {
        if (rawFormat == null || rawFormat.isBlank()) {
            return TestFormat.STANDARD;
        }
        try {
            return TestFormat.from(rawFormat);
        } catch (IllegalArgumentException e) {
            throw new InvalidRequestException(
                    "Format inconnu : '" + rawFormat + "'. Valeurs acceptées : STANDARD, GHERKIN.");
        }
    }

    int resolveCount(Integer requestedCount) {
        if (requestedCount == null) {
            return properties.getDefaultTestCases();
        }
        if (requestedCount < 1 || requestedCount > properties.getMaxTestCases()) {
            throw new InvalidRequestException("'maxCases' doit être compris entre 1 et "
                    + properties.getMaxTestCases() + ".");
        }
        return requestedCount;
    }
}
