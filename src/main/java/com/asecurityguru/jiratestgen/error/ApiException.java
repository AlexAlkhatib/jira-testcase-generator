package com.asecurityguru.jiratestgen.error;

import org.springframework.http.HttpStatus;

/**
 * Base class for every business error that must be rendered as an RFC 7807 problem
 * document. Carrying the HTTP status and a stable machine-readable code keeps the
 * controller free of error handling.
 */
public class ApiException extends RuntimeException {

    private final HttpStatus status;
    private final String code;

    public ApiException(HttpStatus status, String code, String message) {
        super(message);
        this.status = status;
        this.code = code;
    }

    public ApiException(HttpStatus status, String code, String message, Throwable cause) {
        super(message, cause);
        this.status = status;
        this.code = code;
    }

    public HttpStatus getStatus() {
        return status;
    }

    public String getCode() {
        return code;
    }
}
