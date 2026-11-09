package com.asecurityguru.jiratestgen.jira;

/** Fetches a Jira issue and maps it to the domain model. */
public interface JiraStoryClient {

    /**
     * @param storyKey already validated and normalised issue key
     * @return the story data used to build the AI prompt
     */
    JiraStory fetch(String storyKey);
}
