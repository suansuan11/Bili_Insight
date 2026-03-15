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

    private final RestTemplate restTemplate;
    private final ObjectMapper objectMapper;

    public PythonApiClient(RestTemplate restTemplate, ObjectMapper objectMapper) {
        this.restTemplate = restTemplate;
        this.objectMapper = objectMapper;
    }

    /**
     * 提交视频分析任务到Python服务
     * @param bvid 视频BVID
     * @param taskId Java端任务ID
     * @return 是否提交成功
     */
    public boolean submitAnalysisTask(String bvid, Long taskId) {
        String url = pythonServiceUrl + "/api/analyze/video";

        try {
            // 构建请求体
            Map<String, Object> requestBody = new HashMap<>();
            requestBody.put("bvid", bvid);
            requestBody.put("task_id", taskId);

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);

            HttpEntity<Map<String, Object>> request = new HttpEntity<>(requestBody, headers);

            // 发送POST请求
            logger.info("Submitting analysis task to Python service: bvid={}, taskId={}", bvid, taskId);
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

    /**
     * 查询Python服务的任务进度
     * @param taskId 任务ID
     * @return 进度信息的JSON字符串
     */
    public String getTaskProgress(Long taskId) {
        String url = pythonServiceUrl + "/api/analyze/progress/" + taskId;

        try {
            logger.debug("Querying task progress from Python service: taskId={}", taskId);
            ResponseEntity<String> response = restTemplate.getForEntity(url, String.class);

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
            ResponseEntity<String> response = restTemplate.getForEntity(url, String.class);
            boolean isHealthy = response.getStatusCode() == HttpStatus.OK;
            logger.info("Python service health check: {}", isHealthy ? "OK" : "FAILED");
            return isHealthy;

        } catch (Exception e) {
            logger.error("Python service health check failed: {}", e.getMessage());
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
     * 获取B站登录二维码
     * @return 包含二维码信息的JSON字符串
     */
    public String getLoginQrCode() {
        String url = pythonServiceUrl + "/api/login/qrcode";
        try {
            ResponseEntity<String> response = restTemplate.getForEntity(url, String.class);
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
        String url = pythonServiceUrl + "/api/login/status?key=" + key;
        try {
            ResponseEntity<String> response = restTemplate.getForEntity(url, String.class);
            return response.getBody();
        } catch (Exception e) {
            logger.error("Error polling login status from Python service: {}", e.getMessage(), e);
            throw new RuntimeException("Failed to poll login status", e);
        }
    }
}
