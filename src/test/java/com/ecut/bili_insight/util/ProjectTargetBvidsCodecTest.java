package com.ecut.bili_insight.util;

import org.junit.jupiter.api.Test;

import java.util.Arrays;
import java.util.Collections;

import static org.junit.jupiter.api.Assertions.assertEquals;

class ProjectTargetBvidsCodecTest {

    @Test
    void normalizeForStorageShouldConvertTextareaInputToJsonArray() {
        String normalized = ProjectTargetBvidsCodec.normalizeForStorage("BV1abc\nBV2def\n\nBV1abc");

        assertEquals("[\"BV1abc\",\"BV2def\"]", normalized);
    }

    @Test
    void parseShouldReadStoredJsonArray() {
        assertEquals(
                Arrays.asList("BV1abc", "BV2def"),
                ProjectTargetBvidsCodec.parse("[\"BV1abc\", \"BV2def\"]")
        );
    }

    @Test
    void parseShouldSupportLegacyCommaAndNewlineSeparatedValues() {
        assertEquals(
                Arrays.asList("BV1abc", "BV2def", "BV3ghi"),
                ProjectTargetBvidsCodec.parse("BV1abc,BV2def\nBV3ghi")
        );
    }

    @Test
    void normalizeForStorageShouldReturnEmptyJsonArrayForBlankInput() {
        assertEquals("[]", ProjectTargetBvidsCodec.normalizeForStorage("  "));
        assertEquals(Collections.emptyList(), ProjectTargetBvidsCodec.parse("  "));
    }
}
