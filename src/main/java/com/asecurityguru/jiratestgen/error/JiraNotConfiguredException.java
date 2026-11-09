package com.asecurityguru.jiratestgen.error;

/** Raised when the Jira credentials are missing from the environment. */
public class JiraNotConfiguredException extends ApiException {

    public JiraNotConfiguredException() {
        super(org.springframework.http.HttpStatus.SERVICE_UNAVAILABLE, "JIRA_NOT_CONFIGURED",
                "Jira is not configured. Set JIRA_BASE_URL, JIRA_EMAIL and JIRA_API_TOKEN "
                        + "(see .env.example / README).");
    }
}
