package com.asecurityguru.jiratestgen.error;

import org.springframework.http.HttpStatus;

/** Raised when a query parameter is missing or out of its allowed range. */
public class InvalidRequestException extends ApiException {

    public InvalidRequestException(String message) {
        super(HttpStatus.BAD_REQUEST, "VALIDATION_ERROR", message);
    }
}
