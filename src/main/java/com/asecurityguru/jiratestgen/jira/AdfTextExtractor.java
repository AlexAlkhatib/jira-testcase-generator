package com.asecurityguru.jiratestgen.jira;

import java.util.Set;
import java.util.regex.Pattern;

import org.springframework.stereotype.Component;

import com.fasterxml.jackson.databind.JsonNode;

/**
 * Converts a Jira description to plain text.
 *
 * <p>Jira Cloud (REST v3) returns an Atlassian Document Format tree while Jira Server
 * (REST v2) usually returns a plain string. Both shapes are supported, so the same code
 * works against Cloud and Data Center instances.</p>
 */
@Component
public class AdfTextExtractor {

    private static final Pattern BLANK_LINES = Pattern.compile("\\n{3,}");
    private static final Set<String> BLOCK_NODES = Set.of(
            "paragraph", "heading", "blockquote", "panel", "tableRow",
            "bulletList", "orderedList", "listItem", "codeBlock", "rule", "mediaGroup");

    public String toPlainText(JsonNode node) {
        if (node == null || node.isMissingNode() || node.isNull()) {
            return "";
        }
        StringBuilder out = new StringBuilder();
        append(node, out, 0);
        String text = out.toString()
                .replace('\u00a0', ' ')
                .replaceAll("[ \\t]+\\n", "\n")
                .replaceAll("\\n{3,}", "\n\n")
                .trim();
        return BLANK_LINES.matcher(text).replaceAll("\n\n");
    }

    private void append(JsonNode node, StringBuilder out, int depth) {
        if (node == null || node.isNull() || depth > 40) {
            return;
        }
        if (node.isArray()) {
            for (JsonNode child : node) {
                append(child, out, depth + 1);
            }
            return;
        }
        if (node.isTextual()) {
            out.append(node.asText());
            return;
        }
        if (!node.isObject()) {
            return;
        }

        String type = node.path("type").asText("");
        switch (type) {
            case "text" -> out.append(node.path("text").asText(""));
            case "hardBreak" -> out.append('\n');
            case "listItem" -> {
                out.append("- ");
                appendChildren(node, out, depth);
                out.append('\n');
            }
            case "mediaSingle", "media" -> out.append("[image]\n");
            default -> {
                if (BLOCK_NODES.contains(type)) {
                    appendChildren(node, out, depth);
                    out.append("\n\n");
                } else {
                    appendChildren(node, out, depth);
                }
            }
        }
    }

    private void appendChildren(JsonNode node, StringBuilder out, int depth) {
        for (JsonNode child : node.path("content")) {
            append(child, out, depth + 1);
        }
    }

    /** Utility used by tests and callers that already hold a plain string. */
    public String toPlainText(String text) {
        return text == null ? "" : text.trim();
    }
}
