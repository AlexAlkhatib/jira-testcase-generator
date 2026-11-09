package com.asecurityguru.jiratestgen.error;

import org.springframework.http.HttpStatus;

/** Raised when Jira does not know the requested issue key. */
public class JiraStoryNotFoundException extends ApiException {

    public JiraStoryNotFoundException(String storyKey) {
        super(HttpStatus.NOT_FOUND, "STORY_NOT_FOUND",
                "No Jira issue found for key '%s'. Check the key and the project permissions."
                        .formatted(storyKey));
    }
}
