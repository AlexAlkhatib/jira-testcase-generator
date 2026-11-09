package com.asecurityguru.jiratestgen.ai;

import java.util.ArrayList;
import java.util.List;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.ai.chat.client.ChatClient;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

import com.asecurityguru.jiratestgen.ai.model.GeneratedTestCases;
import com.asecurityguru.jiratestgen.ai.model.GenerationOptions;
import com.asecurityguru.jiratestgen.ai.model.TestCase;
import com.asecurityguru.jiratestgen.config.GenerationProperties;
import com.asecurityguru.jiratestgen.error.AiResponseInvalidException;
import com.asecurityguru.jiratestgen.error.AiUnavailableException;
import com.asecurityguru.jiratestgen.jira.JiraStory;

/**
 * Orchestrates one generation: prompt, model call, parsing, truncation and auditing data.
 */
@Service
public class TestCaseGenerationService {

    private static final Logger log = LoggerFactory.getLogger(TestCaseGenerationService.class);

    private final ChatClient chatClient;
    private final PromptFactory promptFactory;
    private final TestCaseResponseParser parser;
    private final GenerationProperties properties;
    private final String model;

    public TestCaseGenerationService(ChatClient chatClient,
                                     PromptFactory promptFactory,
                                     TestCaseResponseParser parser,
                                     GenerationProperties properties,
                                     @Value("${spring.ai.ollama.chat.options.model:mistral}") String model) {
        this.chatClient = chatClient;
        this.promptFactory = promptFactory;
        this.parser = parser;
        this.properties = properties;
        this.model = model;
    }

    public GeneratedTestCases generate(JiraStory story, GenerationOptions options) {
        int maxCases = Math.max(1, Math.min(options.maxTestCases(), properties.getMaxTestCases()));
        GenerationOptions effective = new GenerationOptions(options.language(), options.format(), maxCases);
        PromptFactory.Prompt prompt = promptFactory.build(story, effective);

        List<String> warnings = new ArrayList<>();
        if (!StringUtils.hasText(story.acceptanceCriteria())) {
            warnings.add("Aucun critère d'acceptation n'a été trouvé dans la story : le modèle s'appuie sur la description.");
        }
        if (story.description() != null && story.description().length() > properties.getMaxStoryCharacters()) {
            warnings.add("La description dépassait " + properties.getMaxStoryCharacters()
                    + " caractères : elle a été tronquée avant l'envoi au modèle.");
        }

        long start = System.nanoTime();
        String raw;
        try {
            raw = chatClient.prompt()
                    .system(prompt.system())
                    .user(prompt.user())
                    .call()
                    .content();
        } catch (Exception e) {
            log.error("The local AI model failed to answer for story {}", story.key(), e);
            throw new AiUnavailableException(
                    "Le modèle local n'a pas répondu. Vérifiez qu'Ollama est démarré et que le modèle '"
                            + model + "' est téléchargé (ollama pull " + model + ").", e);
        }
        long durationMs = (System.nanoTime() - start) / 1_000_000;

        List<TestCase> parsed = parser.parse(raw);
        if (parsed.isEmpty()) {
            throw new AiResponseInvalidException(
                    "Le modèle a répondu, mais sa sortie ne contient aucun cas de test JSON exploitable.",
                    parser.preview(raw));
        }

        List<TestCase> retained = parsed;
        if (parsed.size() > maxCases) {
            retained = parsed.subList(0, maxCases);
            warnings.add("Le modèle a produit " + parsed.size() + " cas ; les " + maxCases
                    + " premiers sont retournés (limite configurée).");
        }

        log.info("Story {}: {} test case(s) generated with model {} in {} ms",
                story.key(), retained.size(), model, durationMs);
        return new GeneratedTestCases(List.copyOf(retained), model, durationMs, List.copyOf(warnings),
                raw == null ? "" : raw);
    }
}
