package com.ecut.bili_insight.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;

import java.util.HashMap;
import java.util.Map;

/**
 * Python分析服务HTTP客户端
 * 负责调用Python FastAPI服务的所有接口
 */
@Component
public class PythonApiClient {

    private static final Logger logger = LoggerFactory.getLogger(PythonApiClient.class);

    @Value("${python.service.url:http://localhost:8001}")
    private String pythonServiceUrl;

    @Value("${python.service.api-key:}")
    private String apiKey;

    public String getPythonServiceUrl() {
        return pythonServiceUrl;
    }

    private final RestTemplate restTemplate;
    private final ObjectMapper objectMapper;

    public PythonApiClient(RestTemplate restTemplate, ObjectMapper objectMapper) {
        this.restTemplate = restTemplate;
        this.objectMapper = objectMapper;
    }

    private HttpHeaders createHeaders() {
        HttpHeaders headers = new HttpHeaders();
        if (apiKey != null && !apiKey.isEmpty()) {
            headers.set("X-API-Key", apiKey);
        }
        return headers;
    }

    /**
     * 提交视频分析任务到Python服务
     * @param bvid      视频BVID
     * @param taskId    Java端任务ID
     * @param sessdata  当前用户的B站SESSDATA（可为null，则Python使用游客模式）
     * @param biliJct   当前用户绑定的 bili_jct
     * @param buvid3    当前用户绑定的 buvid3
     * @param maxComments 最大评论获取数量（默认20000）
     * @return 是否提交成功
     */
    public boolean submitAnalysisTask(String bvid, String taskId, String sessdata, String biliJct, String buvid3, String cookieJson, Integer maxComments) {
        String url = pythonServiceUrl + "/api/analysis/video";

        try {
            Map<String, Object> requestBody = new HashMap<>();
            requestBody.put("bvid", bvid);
            requestBody.put("task_id", taskId);
            requestBody.put("max_comments", maxComments != null ? maxComments : 20000);
            if (sessdata != null && !sessdata.trim().isEmpty()) {
                requestBody.put("sessdata", sessdata);
            }
            if (biliJct != null && !biliJct.trim().isEmpty()) {
                requestBody.put("bili_jct", biliJct);
            }
            if (buvid3 != null && !buvid3.trim().isEmpty()) {
                requestBody.put("buvid3", buvid3);
            }
            if (cookieJson != null && !cookieJson.trim().isEmpty()) {
                requestBody.put("cookie_json", cookieJson);
            }

            HttpHeaders headers = createHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            HttpEntity<Map<String, Object>> request = new HttpEntity<>(requestBody, headers);

            logger.info("Submitting analysis task: bvid={}, taskId={}, maxComments={}, hasCredential={}", 
                bvid, taskId, maxComments, sessdata != null);
            ResponseEntity<String> response = restTemplate.postForEntity(url, request, String.class);

            if (response.getStatusCode() == HttpStatus.OK) {
                logger.info("Analysis task submitted successfully: {}", response.getBody());
                return true;
            } else {
                logger.error("Failed to submit analysis task, status: {}", response.getStatusCode());
                return false;
            }

        } catch (Exception e) {
            logger.error("Error calling Python service: {}", e.getMessage(), e);
            return false;
        }
    }
    
    /** 兼容旧调用：不传maxComments */
    public boolean submitAnalysisTask(String bvid, String taskId, String sessdata, String biliJct, String buvid3, String cookieJson) {
        return submitAnalysisTask(bvid, taskId, sessdata, biliJct, buvid3, cookieJson, 2000);
    }

    /**
     * 提交前探测评论接口可用性，识别 B站 412 风控。
     */
    public Map<String, Object> probeCommentAccess(String bvid, String sessdata, String biliJct, String buvid3, String cookieJson) {
        String url = pythonServiceUrl + "/api/analysis/probe-comment";
        try {
            Map<String, Object> requestBody = new HashMap<>();
            requestBody.put("bvid", bvid);
            if (sessdata != null && !sessdata.trim().isEmpty()) {
                requestBody.put("sessdata", sessdata);
            }
            if (biliJct != null && !biliJct.trim().isEmpty()) {
                requestBody.put("bili_jct", biliJct);
            }
            if (buvid3 != null && !buvid3.trim().isEmpty()) {
                requestBody.put("buvid3", buvid3);
            }
            if (cookieJson != null && !cookieJson.trim().isEmpty()) {
                requestBody.put("cookie_json", cookieJson);
            }

            HttpHeaders headers = createHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            HttpEntity<Map<String, Object>> request = new HttpEntity<>(requestBody, headers);
            ResponseEntity<String> response = restTemplate.exchange(url, HttpMethod.POST, request, String.class);

            if (response.getStatusCode() != HttpStatus.OK || response.getBody() == null) {
                throw new IllegalStateException("评论接口探测返回异常");
            }

            JsonNode root = objectMapper.readTree(response.getBody());
            Map<String, Object> result = new HashMap<>();
            result.put("available", root.path("available").asBoolean(false));
            result.put("riskControlled", root.path("risk_controlled").asBoolean(false));
            result.put("message", root.path("message").asText(""));
            result.put("sampleCount", root.path("sample_count").asInt(0));
            return result;
        } catch (Exception e) {
            logger.warn("Comment access probe failed for {}: {}", bvid, e.getMessage());
            Map<String, Object> result = new HashMap<>();
            result.put("available", false);
            result.put("riskControlled", false);
            result.put("message", "评论接口探测失败: " + e.getMessage());
            result.put("error", true);
            return result;
        }
    }
    
    /** 兼容旧调用：不传sessdata（用于系统自动触发的监控任务） */
    public boolean submitAnalysisTask(String bvid, String taskId) {
        return submitAnalysisTask(bvid, taskId, null, null, null, null);
    }

    /**
     * 查询Python服务的任务进度
     * @param taskId 任务ID
     * @return 进度信息的JSON字符串
     */
    public String getTaskProgress(String taskId) {
        String url = pythonServiceUrl + "/api/analysis/status/" + taskId;

        try {
            logger.debug("Querying task progress from Python service: taskId={}", taskId);
            HttpEntity<Void> request = new HttpEntity<>(createHeaders());
            ResponseEntity<String> response = restTemplate.exchange(url, HttpMethod.GET, request, String.class);

            if (response.getStatusCode() == HttpStatus.OK) {
                return response.getBody();
            } else {
                logger.warn("Failed to get task progress, status: {}", response.getStatusCode());
                return null;
            }

        } catch (Exception e) {
            logger.error("Error querying task progress: {}", e.getMessage());
            return null;
        }
    }

    /**
     * 测试Python服务健康状态
     * @return 服务是否可用
     */
    public boolean checkHealth() {
        String url = pythonServiceUrl + "/";

        try {
            HttpEntity<Void> request = new HttpEntity<>(createHeaders());
            ResponseEntity<String> response = restTemplate.exchange(url, HttpMethod.GET, request, String.class);
            boolean isHealthy = response.getStatusCode() == HttpStatus.OK;
            logger.debug("Python service health check: {}", isHealthy ? "OK" : "FAILED");
            return isHealthy;

        } catch (Exception e) {
            // 不记录错误日志，让调用方决定如何处理（启动时连接失败是正常的）
            logger.debug("Python service health check failed: {}", e.getMessage());
            return false;
        }
    }

    /**
     * 解析进度JSON
     * @param progressJson 进度JSON字符串
     * @return 进度百分比(0-100)
     */
    public Integer parseProgress(String progressJson) {
        try {
            JsonNode node = objectMapper.readTree(progressJson);
            return node.has("progress") ? node.get("progress").asInt() : 0;
        } catch (Exception e) {
            logger.error("Failed to parse progress JSON: {}", e.getMessage());
            return 0;
        }
    }

    /**
     * 解析当前步骤
     * @param progressJson 进度JSON字符串
     * @return 当前步骤描述
     */
    public String parseCurrentStep(String progressJson) {
        try {
            JsonNode node = objectMapper.readTree(progressJson);
            return node.has("current_step") ? node.get("current_step").asText() : "Unknown";
        } catch (Exception e) {
            logger.error("Failed to parse current step: {}", e.getMessage());
            return "Unknown";
        }
    }

    /**
     * 触发Python服务抓取热门视频
     * @param pages 抓取页数
     * @return 抓取结果JSON
     */
    public String fetchPopularVideos(int pages, String sessdata, String biliJct, String buvid3, String cookieJson) {
        String url = pythonServiceUrl + "/api/popular/fetch?pages=" + pages;
        try {
            Map<String, Object> requestBody = new HashMap<>();
            requestBody.put("pages", pages);
            if (sessdata != null && !sessdata.trim().isEmpty()) {
                requestBody.put("sessdata", sessdata);
            }
            if (biliJct != null && !biliJct.trim().isEmpty()) {
                requestBody.put("bili_jct", biliJct);
            }
            if (buvid3 != null && !buvid3.trim().isEmpty()) {
                requestBody.put("buvid3", buvid3);
            }
            if (cookieJson != null && !cookieJson.trim().isEmpty()) {
                requestBody.put("cookie_json", cookieJson);
            }

            HttpHeaders headers = createHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            HttpEntity<Map<String, Object>> request = new HttpEntity<>(requestBody, headers);
            ResponseEntity<String> response = restTemplate.exchange(url, HttpMethod.POST, request, String.class);
            return response.getBody();
        } catch (Exception e) {
            logger.error("Error fetching popular videos: {}", e.getMessage(), e);
            throw new RuntimeException("Failed to fetch popular videos", e);
        }
    }

    public String fetchPopularVideos(int pages) {
        return fetchPopularVideos(pages, null, null, null, null);
    }

    /**
     * 查询热门视频抓取状态
     * @return 抓取状态JSON
     */
    public String getPopularFetchStatus() {
        String url = pythonServiceUrl + "/api/popular/fetch/status";
        try {
            HttpEntity<Void> request = new HttpEntity<>(createHeaders());
            ResponseEntity<String> response = restTemplate.exchange(url, HttpMethod.GET, request, String.class);
            return response.getBody();
        } catch (Exception e) {
            logger.error("Error getting popular fetch status: {}", e.getMessage(), e);
            return "{\"status\": \"error\", \"message\": \"" + e.getMessage() + "\"}";
        }
    }

    /**
     * 获取B站登录二维码
     * @return 包含二维码信息的JSON字符串
     */
    public String getLoginQrCode() {
        String url = pythonServiceUrl + "/api/login/qrcode";
        try {
            HttpEntity<Void> request = new HttpEntity<>(createHeaders());
            ResponseEntity<String> response = restTemplate.exchange(url, HttpMethod.GET, request, String.class);
            return response.getBody();
        } catch (Exception e) {
            logger.error("Error getting login QR code from Python service: {}", e.getMessage(), e);
            throw new RuntimeException("Failed to get login QR code", e);
        }
    }

    /**
     * 轮询B站登录状态
     * @param key 二维码对应的key
     * @return 包含登录状态信息的JSON字符串
     */
    public String pollLoginStatus(String key) {
        String url = pythonServiceUrl + "/api/login/status/" + key;
        try {
            HttpEntity<Void> request = new HttpEntity<>(createHeaders());
            ResponseEntity<String> response = restTemplate.exchange(url, HttpMethod.GET, request, String.class);
            return response.getBody();
        } catch (Exception e) {
            logger.error("Error polling login status from Python service: {}", e.getMessage(), e);
            throw new RuntimeException("Failed to poll login status", e);
        }
    }
}
