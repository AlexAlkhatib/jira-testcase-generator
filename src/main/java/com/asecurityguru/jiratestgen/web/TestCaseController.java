package com.asecurityguru.jiratestgen.web;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.asecurityguru.jiratestgen.service.TestSuiteService;
import com.asecurityguru.jiratestgen.web.dto.GenerationResponse;

/**
 * Public API.
 *
 * <p>{@code /api/v1/jira-story} is kept as a backwards-compatible alias of
 * {@code /api/v1/test-cases} for existing clients.</p>
 */
@RestController
@RequestMapping("/api/v1")
public class TestCaseController {

    private final TestSuiteService testSuiteService;

    public TestCaseController(TestSuiteService testSuiteService) {
        this.testSuiteService = testSuiteService;
    }

    @GetMapping({"/test-cases", "/jira-story"})
    public GenerationResponse generate(
            @RequestParam(required = false) String storyKey,
            @RequestParam(required = false) String language,
            @RequestParam(required = false) String format,
            @RequestParam(required = false) Integer maxCases) {
        return testSuiteService.generate(storyKey, language, format, maxCases);
    }
}
