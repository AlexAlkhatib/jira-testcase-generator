package com.asecurityguru.jiratestgen.error;

import org.springframework.http.HttpStatus;

/** Raised when Jira rejects the credentials (401/403). */
public class JiraAuthenticationException extends ApiException {

    public JiraAuthenticationException(String detail) {
        super(HttpStatus.BAD_GATEWAY, "JIRA_AUTH_FAILED",
                "Jira rejected the configured credentials: " + detail);
    }
}
