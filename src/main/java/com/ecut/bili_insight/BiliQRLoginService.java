package com.ecut.bili_insight;

import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import org.springframework.http.*;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

import java.util.Map;
import java.util.HashMap;

/**
 * B站扫码登录服务示例
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class BiliQRLoginService {

    private final RestTemplate restTemplate;

    private static final String PYTHON_API = "http://localhost:18001/api";

    /**
     * 1. 获取二维码信息
     * 前端调用此方法获取二维码URL和Key
     *
     * @return {qrcode_url: "...", qrcode_key: "..."}
     */
    public Map<String, String> getQRCode() {
        String url = PYTHON_API + "/login/qrcode";

        try {
            ResponseEntity<Map> response = restTemplate.getForEntity(url, Map.class);

            if (response.getStatusCode() == HttpStatus.OK) {
                Map<String, String> data = response.getBody();
                log.info("获取二维码成功");
                return data;
            }
        } catch (Exception e) {
            log.error("获取二维码失败", e);
        }
        return null;
    }

    /**
     * 2. 检查扫码状态
     * 前端轮询调用此方法（每2秒）
     *
     * @param qrcodeKey 二维码Key
     * @return {status: "pending|scanned|confirmed|expired", message: "...", sessdata: "..."}
     */
    public Map<String, Object> checkQRStatus(String qrcodeKey) {
        String url = PYTHON_API + "/login/status/" + qrcodeKey + "?auto_save=true";

        try {
            ResponseEntity<Map> response = restTemplate.getForEntity(url, Map.class);

            if (response.getStatusCode() == HttpStatus.OK) {
                Map<String, Object> data = response.getBody();
                String status = (String) data.get("status");

                log.info("扫码状态: {}", status);

                // 登录成功时的处理
                if ("confirmed".equals(status)) {
                    String sessdata = (String) data.get("sessdata");
                    log.info("用户登录成功，SESSDATA: {}...", sessdata.substring(0, 20));

                    // 可以保存到用户表
                    // userService.updateUserBiliCredential(userId, sessdata);
                }

                return data;
            }
        } catch (Exception e) {
            log.error("检查扫码状态失败", e);
        }
        return null;
    }

    /**
     * 完整的登录流程示例（WebSocket方式）
     * Controller中使用：
     */
    /*
    @Controller
    public class BiliLoginController {

        @Autowired
        private BiliQRLoginService qrLoginService;

        @MessageMapping("/bili/qrcode")
        @SendToUser("/queue/qrcode")
        public Map<String, String> getQRCode() {
            return qrLoginService.getQRCode();
        }

        @MessageMapping("/bili/poll")
        @SendToUser("/queue/status")
        public Map<String, Object> pollStatus(String qrcodeKey) {
            return qrLoginService.checkQRStatus(qrcodeKey);
        }
    }
    */
}
