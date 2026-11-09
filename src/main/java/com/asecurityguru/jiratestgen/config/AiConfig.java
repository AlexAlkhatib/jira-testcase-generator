package com.asecurityguru.jiratestgen.config;

import org.springframework.ai.chat.client.ChatClient;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * Builds the shared {@link ChatClient}. Model, temperature and context size are configured
 * through standard Spring AI properties ({@code spring.ai.ollama.chat.options.*}).
 */
@Configuration
public class AiConfig {

    @Bean
    ChatClient chatClient(ChatClient.Builder builder) {
        return builder.build();
    }
}
