package com.asecurityguru.jiratestgen.error;

import org.springframework.http.HttpStatus;

/** Raised when the local model cannot be reached or fails to answer. */
public class AiUnavailableException extends ApiException {

    public AiUnavailableException(String message, Throwable cause) {
        super(HttpStatus.SERVICE_UNAVAILABLE, "AI_UNAVAILABLE", message, cause);
    }
}
