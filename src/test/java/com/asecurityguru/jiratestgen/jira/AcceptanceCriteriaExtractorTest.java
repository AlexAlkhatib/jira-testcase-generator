package com.asecurityguru.jiratestgen.jira;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

class AcceptanceCriteriaExtractorTest {

    private final AcceptanceCriteriaExtractor extractor = new AcceptanceCriteriaExtractor();

    @Test
    @DisplayName("an 'Acceptance Criteria' section is isolated from the description")
    void extractsSection() {
        String description = """
                As a registered user I want to log in so that I can access my dashboard.

                Acceptance Criteria
                - Valid credentials open the dashboard
                - Invalid password shows an error

                Notes
                - Use the test account
                """;

        String criteria = extractor.extract(description, "Login");

        assertThat(criteria)
                .contains("Valid credentials open the dashboard")
                .contains("Invalid password shows an error")
                .doesNotContain("Notes")
                .doesNotContain("As a registered user");
    }

    @Test
    @DisplayName("French headings and inline labels are supported")
    void extractsFrenchSection() {
        String description = """
                En tant qu'utilisateur, je veux réinitialiser mon mot de passe.

                Critères d'acceptation :
                1. Un email valide envoie un lien
                2. Un email inconnu affiche une erreur générique

                Détails techniques
                - endpoint /reset
                """;

        String criteria = extractor.extract(description, "Réinitialisation");

        assertThat(criteria)
                .contains("Un email valide envoie un lien")
                .contains("Un email inconnu affiche une erreur générique")
                .doesNotContain("endpoint");
    }

    @Test
    @DisplayName("without a section the whole description is used")
    void fallsBackToDescription() {
        String description = "The user can upload a PDF of up to 10 MB.";

        assertThat(extractor.extract(description, "Upload")).isEqualTo(description);
    }

    @Test
    @DisplayName("a blank description falls back to the summary")
    void fallsBackToSummary() {
        assertThat(extractor.extract("", "Login story")).isEqualTo("Login story");
        assertThat(extractor.extract(null, "Login story")).isEqualTo("Login story");
    }

    @Test
    @DisplayName("an empty section does not swallow the description")
    void emptySectionIsIgnored() {
        String description = """
                Acceptance Criteria
                Not really documented yet.
                """;

        assertThat(extractor.extract(description, "Story")).contains("Not really documented yet.");
    }

    @Test
    @DisplayName("inline acceptance criteria are extracted")
    void extractsInline() {
        String description = """
                The user can filter the list.
                AC: filtering by status and assignee updates the results.
                """;

        assertThat(extractor.extract(description, "Filter"))
                .isEqualTo("filtering by status and assignee updates the results.");
    }
}
