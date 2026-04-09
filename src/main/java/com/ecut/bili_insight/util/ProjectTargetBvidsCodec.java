package com.ecut.bili_insight.util;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashSet;
import java.util.List;

public final class ProjectTargetBvidsCodec {

    private static final ObjectMapper OBJECT_MAPPER = new ObjectMapper();

    private ProjectTargetBvidsCodec() {
    }

    public static List<String> parse(String rawValue) {
        if (rawValue == null || rawValue.trim().isEmpty()) {
            return Collections.emptyList();
        }

        String trimmed = rawValue.trim();
        if (trimmed.startsWith("[")) {
            try {
                return sanitize(OBJECT_MAPPER.readValue(trimmed, new TypeReference<List<String>>() {
                }));
            } catch (Exception ignored) {
                // 回退到兼容旧格式解析
            }
        }

        String[] parts = trimmed.split("[\\r\\n,，]+");
        List<String> values = new ArrayList<>();
        Collections.addAll(values, parts);
        return sanitize(values);
    }

    public static String normalizeForStorage(String rawValue) {
        try {
            return OBJECT_MAPPER.writeValueAsString(parse(rawValue));
        } catch (Exception e) {
            throw new IllegalArgumentException("无法序列化 targetBvids", e);
        }
    }

    private static List<String> sanitize(List<String> rawValues) {
        LinkedHashSet<String> deduped = new LinkedHashSet<>();
        if (rawValues != null) {
            for (String value : rawValues) {
                if (value == null) {
                    continue;
                }
                String trimmed = value.trim();
                if (!trimmed.isEmpty()) {
                    deduped.add(trimmed);
                }
            }
        }
        return new ArrayList<>(deduped);
    }
}
