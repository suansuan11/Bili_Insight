package com.ecut.bili_insight.service;

import org.springframework.stereotype.Service;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

@Service
public class RateLimitService {
    private final Map<String, LoginAttempt> attempts = new ConcurrentHashMap<>();
    private static final int MAX_ATTEMPTS = 5;
    private static final long LOCK_TIME_MS = 15 * 60 * 1000; // 15分钟

    public boolean isBlocked(String identifier) {
        LoginAttempt attempt = attempts.get(identifier);
        if (attempt == null) return false;

        if (System.currentTimeMillis() - attempt.lastAttempt > LOCK_TIME_MS) {
            attempts.remove(identifier);
            return false;
        }
        return attempt.count >= MAX_ATTEMPTS;
    }

    public void recordFailure(String identifier) {
        attempts.compute(identifier, (k, v) -> {
            if (v == null) return new LoginAttempt(1, System.currentTimeMillis());
            return new LoginAttempt(v.count + 1, System.currentTimeMillis());
        });
    }

    public void resetAttempts(String identifier) {
        attempts.remove(identifier);
    }

    private static class LoginAttempt {
        int count;
        long lastAttempt;
        LoginAttempt(int count, long lastAttempt) {
            this.count = count;
            this.lastAttempt = lastAttempt;
        }
    }
}
