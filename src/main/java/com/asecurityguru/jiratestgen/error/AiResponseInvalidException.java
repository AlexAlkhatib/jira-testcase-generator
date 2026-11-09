package com.asecurityguru.jiratestgen.error;

import org.springframework.http.HttpStatus;

/** Raised when the model answered but not with a usable test case structure. */
public class AiResponseInvalidException extends ApiException {

    public AiResponseInvalidException(String message, String rawPreview) {
        super(HttpStatus.BAD_GATEWAY, "AI_RESPONSE_INVALID",
                message + (rawPreview == null || rawPreview.isBlank()
                        ? ""
                        : " Model output started with: " + rawPreview));
    }
}
