package com.ecut.bili_insight.service;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

import static org.junit.jupiter.api.Assertions.*;

@SpringBootTest
class RateLimitServiceTest {

    @Autowired
    private RateLimitService rateLimitService;

    @Test
    void testLoginRateLimit() {
        String identifier = "test_user_" + System.currentTimeMillis();

        // 前5次失败不应被阻止
        for (int i = 0; i < 5; i++) {
            assertFalse(rateLimitService.isBlocked(identifier), "第" + (i + 1) + "次不应被阻止");
            rateLimitService.recordFailure(identifier);
        }

        // 第6次应该被阻止
        assertTrue(rateLimitService.isBlocked(identifier), "第6次应该被阻止");

        // 重置后应该可以访问
        rateLimitService.resetAttempts(identifier);
        assertFalse(rateLimitService.isBlocked(identifier), "重置后应该可以访问");
    }
}
