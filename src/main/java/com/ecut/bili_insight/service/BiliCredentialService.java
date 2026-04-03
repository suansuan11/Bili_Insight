package com.ecut.bili_insight.service;

import com.ecut.bili_insight.entity.User;
import com.ecut.bili_insight.mapper.UserMapper;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

@Service
public class BiliCredentialService {

    private static final Logger logger = LoggerFactory.getLogger(BiliCredentialService.class);
    private static final String NAV_API = "https://api.bilibili.com/x/web-interface/nav";
    private static final String USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36";

    private final UserMapper userMapper;
    private final RestTemplate restTemplate;
    private final ObjectMapper objectMapper;

    public BiliCredentialService(UserMapper userMapper, RestTemplate restTemplate, ObjectMapper objectMapper) {
        this.userMapper = userMapper;
        this.restTemplate = restTemplate;
        this.objectMapper = objectMapper;
    }

    public User findUserById(Long userId) {
        if (userId == null) {
            return null;
        }
        return userMapper.findById(userId);
    }

    public boolean hasBoundCredential(User user) {
        return user != null
                && user.getBiliSessdata() != null
                && !user.getBiliSessdata().trim().isEmpty();
    }

    public CredentialStatus checkCredential(Long userId) {
        return checkCredential(findUserById(userId));
    }

    public CredentialStatus checkCredential(User user) {
        CredentialStatus status = new CredentialStatus(user);

        if (!hasBoundCredential(user)) {
            return status;
        }

        status.setHasCredential(true);

        try {
            HttpHeaders headers = new HttpHeaders();
            headers.set("Cookie", buildCookie(user));
            headers.set("User-Agent", USER_AGENT);
            headers.set("Referer", "https://www.bilibili.com");

            HttpEntity<Void> entity = new HttpEntity<>(headers);
            ResponseEntity<String> response = restTemplate.exchange(
                    NAV_API,
                    HttpMethod.GET,
                    entity,
                    String.class
            );

            JsonNode root = objectMapper.readTree(response.getBody());
            boolean isLogin = root.path("code").asInt() == 0
                    && root.path("data").path("isLogin").asBoolean(false);

            if (isLogin) {
                status.setValid(true);
            } else {
                status.setExpired(true);
            }
        } catch (Exception e) {
            status.setError(true);
            status.setErrorMessage(e.getMessage());
            logger.warn("验证 B站凭证失败, userId={}: {}", user != null ? user.getId() : null, e.getMessage());
        }

        return status;
    }

    private String buildCookie(User user) {
        StringBuilder cookie = new StringBuilder("SESSDATA=").append(user.getBiliSessdata());
        if (user.getBiliJct() != null && !user.getBiliJct().trim().isEmpty()) {
            cookie.append("; bili_jct=").append(user.getBiliJct());
        }
        if (user.getBiliBuvid3() != null && !user.getBiliBuvid3().trim().isEmpty()) {
            cookie.append("; buvid3=").append(user.getBiliBuvid3());
        }
        return cookie.toString();
    }

    public static class CredentialStatus {
        private final User user;
        private boolean hasCredential;
        private boolean valid;
        private boolean expired;
        private boolean error;
        private String errorMessage;

        public CredentialStatus(User user) {
            this.user = user;
        }

        public User getUser() {
            return user;
        }

        public boolean hasCredential() {
            return hasCredential;
        }

        public void setHasCredential(boolean hasCredential) {
            this.hasCredential = hasCredential;
        }

        public boolean isValid() {
            return valid;
        }

        public void setValid(boolean valid) {
            this.valid = valid;
        }

        public boolean isExpired() {
            return expired;
        }

        public void setExpired(boolean expired) {
            this.expired = expired;
        }

        public boolean isError() {
            return error;
        }

        public void setError(boolean error) {
            this.error = error;
        }

        public String getErrorMessage() {
            return errorMessage;
        }

        public void setErrorMessage(String errorMessage) {
            this.errorMessage = errorMessage;
        }
    }
}
