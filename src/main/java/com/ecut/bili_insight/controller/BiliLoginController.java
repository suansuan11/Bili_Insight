package com.ecut.bili_insight.controller;

import com.ecut.bili_insight.mapper.UserMapper;
import com.ecut.bili_insight.service.PythonApiClient;
import com.ecut.bili_insight.util.JwtUtil;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;

import javax.servlet.http.HttpServletRequest;

/**
 * B站扫码登录控制器
 * 负责转发二维码生成/轮询请求到 Python 服务，
 * 并在扫码成功后将 B站凭证持久化到当前用户的数据库记录。
 */
@RestController
@RequestMapping("/insight/login")
public class BiliLoginController {

    private static final Logger logger = LoggerFactory.getLogger(BiliLoginController.class);

    @Autowired
    private PythonApiClient pythonApiClient;

    @Autowired
    private ObjectMapper objectMapper;

    @Autowired
    private JwtUtil jwtUtil;

    @Autowired
    private UserMapper userMapper;

    // ── 从请求头的 Bearer token 里提取 userId ────────────────────────────
    private Long extractUserId(HttpServletRequest request) {
        String authHeader = request.getHeader("Authorization");
        if (authHeader != null && authHeader.startsWith("Bearer ")) {
            try {
                return jwtUtil.extractUserId(authHeader.substring(7));
            } catch (Exception e) {
                logger.warn("Failed to extract userId from token: {}", e.getMessage());
            }
        }
        return null;
    }

    /**
     * 生成 B站登录二维码
     * GET /insight/login/qrcode/generate
     */
    @GetMapping("/qrcode/generate")
    public ResponseEntity<String> generateQrCode() {
        try {
            String result = pythonApiClient.getLoginQrCode();
            return ResponseEntity.ok(result);
        } catch (Exception e) {
            logger.error("Failed to generate QR code: {}", e.getMessage());
            return ResponseEntity.status(500)
                    .body("{\"error\":\"获取二维码失败: " + e.getMessage() + "\"}");
        }
    }

    /**
     * 轮询扫码状态
     * GET /insight/login/qrcode/poll?key={key}
     *
     * Python 服务返回格式（status=confirmed 时）：
     * { "status": "confirmed", "message": "...", "sessdata": "...", "bili_jct": "...", "buvid3": "..." }
     *
     * 登录成功后将凭证写入当前用户的数据库记录。
     */
    @GetMapping("/qrcode/poll")
    public ResponseEntity<String> pollQrCodeStatus(@RequestParam("key") String key,
                                                   HttpServletRequest request) {
        try {
            String raw = pythonApiClient.pollLoginStatus(key);
            JsonNode json = objectMapper.readTree(raw);

            String status = json.has("status") ? json.get("status").asText() : "";

            if ("confirmed".equals(status)) {
                String sessdata = json.has("sessdata") ? json.get("sessdata").asText(null) : null;
                String biliJct  = json.has("bili_jct")  ? json.get("bili_jct").asText(null)  : null;
                String buvid3   = json.has("buvid3")    ? json.get("buvid3").asText(null)    : null;

                Long userId = extractUserId(request);
                if (userId != null && sessdata != null) {
                    int updated = userMapper.updateBiliCredential(userId, sessdata, biliJct, buvid3);
                    if (updated > 0) {
                        logger.info("B站凭证已绑定到用户 userId={}", userId);
                    } else {
                        logger.warn("updateBiliCredential 未更新任何行，userId={}", userId);
                    }
                } else {
                    logger.warn("B站登录成功但无法保存凭证: userId={}, sessdata存在={}", userId, sessdata != null);
                }
            }

            return ResponseEntity.ok(raw);
        } catch (Exception e) {
            logger.error("Failed to poll QR code status: {}", e.getMessage());
            return ResponseEntity.status(500)
                    .body("{\"status\":\"error\",\"message\":\"状态轮询失败: " + e.getMessage() + "\"}");
        }
    }

    /**
     * 获取当前 B站登录状态（检查当前用户 DB 里是否有凭证）
     * GET /insight/login/qrcode/poll?key=check  ← 前端 SettingsView 用这个来检查初始状态
     */
    @GetMapping("/status/check")
    public ResponseEntity<String> checkBiliLoginStatus(HttpServletRequest request) {
        Long userId = extractUserId(request);
        if (userId == null) {
            return ResponseEntity.ok("{\"is_login\":false}");
        }
        try {
            com.ecut.bili_insight.entity.User user = userMapper.findById(userId);
            boolean hasCredential = user != null
                    && user.getBiliSessdata() != null
                    && !user.getBiliSessdata().isEmpty();
            // 转发给 Python 验证 sessdata 有效性，同时返回用户信息
            if (hasCredential) {
                String currentUserInfo = pythonApiClient.pollLoginStatus("check");
                return ResponseEntity.ok(currentUserInfo);
            }
            return ResponseEntity.ok("{\"is_login\":false}");
        } catch (Exception e) {
            return ResponseEntity.ok("{\"is_login\":false}");
        }
    }

    /**
     * 获取B站当前登录用户信息
     * Java 直接从 DB 读取 sessdata，调用 B站 API，不依赖 Python 内存状态
     * GET /insight/login/current_user
     */
    @GetMapping("/current_user")
    public ResponseEntity<String> getCurrentBiliUser(HttpServletRequest request) {
        Long userId = extractUserId(request);
        if (userId == null) {
            return ResponseEntity.ok("{\"is_login\":false}");
        }
        try {
            com.ecut.bili_insight.entity.User user = userMapper.findById(userId);
            if (user == null || user.getBiliSessdata() == null || user.getBiliSessdata().isEmpty()) {
                return ResponseEntity.ok("{\"is_login\":false}");
            }

            // 用 DB 里的 sessdata 直接请求 B站导航接口
            RestTemplate rt = new RestTemplate();
            org.springframework.http.HttpHeaders headers = new org.springframework.http.HttpHeaders();
            headers.set("Cookie", "SESSDATA=" + user.getBiliSessdata()
                    + (user.getBiliJct() != null ? "; bili_jct=" + user.getBiliJct() : "")
                    + (user.getBiliBuvid3() != null ? "; buvid3=" + user.getBiliBuvid3() : ""));
            headers.set("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36");
            headers.set("Referer", "https://www.bilibili.com");

            org.springframework.http.HttpEntity<Void> entity = new org.springframework.http.HttpEntity<>(headers);
            ResponseEntity<String> biliResp = rt.exchange(
                    "https://api.bilibili.com/x/web-interface/nav",
                    org.springframework.http.HttpMethod.GET,
                    entity,
                    String.class
            );

            JsonNode root = objectMapper.readTree(biliResp.getBody());
            if (root.path("code").asInt() == 0 && root.path("data").path("isLogin").asBoolean(false)) {
                JsonNode data = root.path("data");
                java.util.Map<String, Object> result = new java.util.HashMap<>();
                result.put("is_login", true);
                result.put("mid", data.path("mid").asLong());
                result.put("uname", data.path("uname").asText());
                result.put("face", data.path("face").asText());
                result.put("level_info", objectMapper.convertValue(data.path("level_info"), java.util.Map.class));
                result.put("vip_label", objectMapper.convertValue(data.path("vip_label"), java.util.Map.class));
                return ResponseEntity.ok(objectMapper.writeValueAsString(result));
            } else {
                return ResponseEntity.ok("{\"is_login\":false}");
            }
        } catch (Exception e) {
            logger.error("Failed to get bili user info: {}", e.getMessage());
            return ResponseEntity.ok("{\"is_login\":false}");
        }
    }

    /**
     * 图片代理（二维码图片跨域代理）
     * GET /insight/login/qrcode/image-proxy?url=...
     */
    @GetMapping("/qrcode/image-proxy")
    public ResponseEntity<byte[]> getQrCodeImage(@RequestParam("url") String url) {
        try {
            RestTemplate restTemplate = new RestTemplate();
            byte[] imageBytes = restTemplate.getForObject(url, byte[].class);
            return ResponseEntity.ok().contentType(MediaType.IMAGE_PNG).body(imageBytes);
        } catch (Exception e) {
            logger.error("Image proxy failed: {}", e.getMessage());
            return ResponseEntity.status(500).build();
        }
    }
}
