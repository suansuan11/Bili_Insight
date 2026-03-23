package com.ecut.bili_insight.util;

import java.util.regex.Pattern;

public class ValidationUtil {
    private static final Pattern BVID_PATTERN = Pattern.compile("^BV[a-zA-Z0-9]{10}$");
    private static final int MIN_PASSWORD_LENGTH = 6;

    public static boolean isValidBvid(String bvid) {
        return bvid != null && BVID_PATTERN.matcher(bvid).matches();
    }

    public static boolean isValidPassword(String password) {
        return password != null && password.length() >= MIN_PASSWORD_LENGTH;
    }

    public static String validateBvid(String bvid) {
        if (!isValidBvid(bvid)) {
            throw new IllegalArgumentException("无效的BVID格式");
        }
        return bvid;
    }
}
