// BiliLoginController.java (修正版)

package com.ecut.bili_insight.controller;

import com.ecut.bili_insight.service.PythonApiClient;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.client.RestTemplate;

@RestController
@RequestMapping("/insight/login") // 将路径统一到bili下
public class BiliLoginController {

    private final PythonApiClient pythonApiClient;
    private final ObjectMapper objectMapper;

    @Autowired
    public BiliLoginController(PythonApiClient pythonApiClient, ObjectMapper objectMapper) {
        this.pythonApiClient = pythonApiClient;
        this.objectMapper = objectMapper;
    }

    /**
     * API端点①: 生成二维码
     */
    @GetMapping("/qrcode/generate")
    public ResponseEntity<String> generateQrCode() {
        try {
            String scriptOutput = pythonApiClient.getLoginQrCode();
            return ResponseEntity.ok(scriptOutput);
        } catch (Exception e) {
            e.printStackTrace();
            return ResponseEntity.status(500)
                    .body("{\"status\": \"error\", \"message\": \"获取二维码失败: " + e.getMessage() + "\"}");
        }
    }

    /**
     * API端点②: 轮询扫码状态
     */
    @GetMapping("/qrcode/poll")
    public ResponseEntity<String> pollQrCodeStatus(@RequestParam("key") String key) {
        try {
            String scriptOutput = pythonApiClient.pollLoginStatus(key);

            // 检查并处理登录成功后的业务逻辑
            JsonNode jsonNode = objectMapper.readTree(scriptOutput);
            if (jsonNode.has("status") && "success".equals(jsonNode.get("status").asText())) {
                String sessdata = jsonNode.get("cookies").get("SESSDATA").asText();
                // 将 sessdata 与当前登录的用户绑定，并加密存储到数据库中
                System.out.println("成功获取到SESSDATA: " + sessdata + "，准备存入数据库...");
            }

            return ResponseEntity.ok(scriptOutput);
        } catch (Exception e) {
            e.printStackTrace();
            return ResponseEntity.status(500)
                    .body("{\"status\": \"error\", \"message\": \"状态轮询失败: " + e.getMessage() + "\"}");
        }
    }

    /**
     * API端点③: 图片代理接口
     * 这个接口负责代理从B站下载二维码图片
     */
    @GetMapping("/qrcode/image-proxy")
    public ResponseEntity<byte[]> getQrCodeImage(@RequestParam("url") String url) {
        try {
            RestTemplate restTemplate = new RestTemplate();
            byte[] imageBytes = restTemplate.getForObject(url, byte[].class);
            return ResponseEntity.ok().contentType(MediaType.IMAGE_PNG).body(imageBytes);
        } catch (Exception e) {
            e.printStackTrace();
            return ResponseEntity.status(500).build();
        }
    }

    // 如果您想测试弹幕爬取，也应该为它创建一个专门的API接口
    // 例如:
}