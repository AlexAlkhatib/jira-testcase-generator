package com.asecurityguru.jiratestgen.jira;

import java.util.List;
import java.util.Locale;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import org.springframework.stereotype.Component;
import org.springframework.util.StringUtils;

/**
 * Isolates the acceptance criteria from a free-text Jira description.
 *
 * <p>Three strategies are applied in order:</p>
 * <ol>
 *   <li>a labelled section ("Acceptance Criteria", "Critères d'acceptation", "AC"...) until the
 *       next known heading;</li>
 *   <li>an inline label ("Acceptance criteria: the user ...");</li>
 *   <li>the whole description, which is the only reasonable input when the team does not use
 *       a dedicated section.</li>
 * </ol>
 */
@Component
public class AcceptanceCriteriaExtractor {

    private static final List<String> SECTION_HEADINGS = List.of(
            "acceptance criteria", "acceptance criterias", "criteria", "criteres d'acceptation",
            "critères d'acceptation", "criteres d acceptation", "criteres dacceptation",
            "ac", "definition of done", "dod");

    private static final List<String> STOP_HEADINGS = List.of(
            "definition of done", "dod", "notes", "note", "technical details", "détails techniques",
            "details techniques", "out of scope", "hors périmètre", "hors perimetre", "design",
            "links", "liens", "attachments", "pièces jointes", "pieces jointes", "screenshots",
            "captures d'écran", "captures d ecran", "context", "contexte", "description",
            "business value", "valeur métier", "questions", "risks", "risques", "dependencies",
            "dépendances", "dependances", "implementation notes", "test plan", "plan de test");

    private static final Pattern HEADING = Pattern.compile("^\\s*#{0,6}\\s*(?<label>[^:\\n]{2,60}?)\\s*:?\\s*$");
    private static final Pattern INLINE = Pattern.compile(
            "(?i)^\\s*(?:acceptance criteria|acceptance criterias|critères? d'acceptation|"
                    + "criteres? d['’]acceptation|ac)\\s*[:\\-–]\\s*(?<value>.+)$");

    /**
     * @param description plain-text description, may be blank
     * @param summary     issue title, used as last resort
     * @return the best acceptance criteria available, never blank when a summary exists
     */
    public String extract(String description, String summary) {
        String text = description == null ? "" : description.replace("\r\n", "\n").trim();
        if (text.isBlank()) {
            return summary == null ? "" : summary.trim();
        }

        String[] lines = text.split("\n", -1);
        int sectionStart = -1;
        String inlineValue = null;

        for (int i = 0; i < lines.length; i++) {
            String line = lines[i].trim();
            if (line.isBlank()) {
                continue;
            }
            Matcher inline = INLINE.matcher(line);
            if (inline.matches()) {
                inlineValue = inline.group("value").trim();
                sectionStart = i;
                break;
            }
            Matcher heading = HEADING.matcher(line);
            if (heading.matches() && isSectionHeading(heading.group("label"))) {
                sectionStart = i;
                break;
            }
        }

        if (sectionStart < 0) {
            return text;
        }

        StringBuilder criteria = new StringBuilder();
        if (StringUtils.hasText(inlineValue)) {
            criteria.append(inlineValue).append('\n');
        }
        for (int i = sectionStart + 1; i < lines.length; i++) {
            String line = lines[i];
            String trimmed = line.trim();
            Matcher heading = HEADING.matcher(trimmed);
            if (!trimmed.isBlank() && heading.matches() && isStopHeading(heading.group("label"))) {
                break;
            }
            criteria.append(line).append('\n');
        }

        String result = criteria.toString().trim();
        // A heading with no content is not an acceptance criteria section: keep the full text.
        return result.isBlank() ? text : result;
    }

    private boolean isSectionHeading(String label) {
        String normalised = label.toLowerCase(Locale.ROOT).replace("’", "'").trim();
        return SECTION_HEADINGS.stream().anyMatch(h -> normalised.equals(h) || normalised.startsWith(h + " "));
    }

    private boolean isStopHeading(String label) {
        String normalised = label.toLowerCase(Locale.ROOT).replace("’", "'").trim();
        return STOP_HEADINGS.stream().anyMatch(normalised::equals);
    }
}
