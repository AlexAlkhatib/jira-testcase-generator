package com.asecurityguru.jiratestgen.error;

import org.springframework.http.HttpStatus;

/** Raised when Jira cannot be reached or answers with an unusable payload. */
public class JiraUnavailableException extends ApiException {

    public JiraUnavailableException(String message, Throwable cause) {
        super(HttpStatus.BAD_GATEWAY, "JIRA_UNAVAILABLE", message, cause);
    }

    public JiraUnavailableException(String message) {
        super(HttpStatus.BAD_GATEWAY, "JIRA_UNAVAILABLE", message);
    }
}
