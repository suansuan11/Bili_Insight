// BiliLoginController.java (修正版)

package com.ecut.bili_insight.controller;

import com.ecut.bili_insight.service.impl.PythonExecutorService;
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

    // 使用final关键字，并推荐通过构造函数注入
    private final PythonExecutorService pythonExecutorService;
    private final ObjectMapper objectMapper;

    // 【核心修改①】: 使用构造函数进行依赖注入
    // Spring会自动找到所需的Bean并传入
    @Autowired
    public BiliLoginController(PythonExecutorService pythonExecutorService, ObjectMapper objectMapper) {
        this.pythonExecutorService = pythonExecutorService;
        this.objectMapper = objectMapper;
    }

    // 【核心修改②】: 删除了所有写在类声明区的业务逻辑代码。
    // 业务逻辑必须在方法内部，由HTTP请求等事件触发。

    /**
     * API端点①: 生成二维码
     * 这个接口负责调用生成二维码的Python脚本
     */
    @GetMapping("/qrcode/generate")
    public ResponseEntity<String> generateQrCode() {
        try {
            // 业务逻辑在这里，由 /generate 的GET请求触发
            String scriptOutput = pythonExecutorService.executeScript("login/qr_generate.py");
            return ResponseEntity.ok(scriptOutput);
        } catch (Exception e) {
            e.printStackTrace(); // 在后端打印详细错误，方便调试
            return ResponseEntity.status(500)
                    .body("{\"status\": \"error\", \"message\": \"执行二维码生成脚本失败: " + e.getMessage() + "\"}");
        }
    }

    /**
     * API端点②: 轮询扫码状态
     * 这个接口负责调用查询状态的Python脚本
     */
    @GetMapping("/qrcode/poll")
    public ResponseEntity<String> pollQrCodeStatus(@RequestParam("key") String key) {
        try {
            String scriptOutput = pythonExecutorService.executeScript("login/qr_poll.py", "--key", key);

            // 检查并处理登录成功后的业务逻辑
            JsonNode jsonNode = objectMapper.readTree(scriptOutput);
            if (jsonNode.has("status") && "success".equals(jsonNode.get("status").asText())) {
                String sessdata = jsonNode.get("cookies").get("SESSDATA").asText();
                // 将 sessdata 与当前登录的用户绑定，并加密存储到你的数据库中
                System.out.println("成功获取到SESSDATA: " + sessdata + "，准备存入数据库...");
            }

            return ResponseEntity.ok(scriptOutput);
        } catch (Exception e) {
            e.printStackTrace();
            return ResponseEntity.status(500)
                    .body("{\"status\": \"error\", \"message\": \"执行状态轮询脚本失败: " + e.getMessage() + "\"}");
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
    @GetMapping("/danmaku")
    public ResponseEntity<String> scrapeDanmaku(@RequestParam String bvid, @RequestParam String sessdata) {
        try {
            String result = pythonExecutorService.executeScript(
                    "danmaku_scraper.py",
                    "--bvid", bvid,
                    "--sessdata", sessdata);
            return ResponseEntity.ok("弹幕爬取任务已成功执行，请检查 'data' 文件夹下的产出文件。脚本输出: " + result);
        } catch (Exception e) {
            e.printStackTrace();
            return ResponseEntity.status(500).body("执行弹幕爬取脚本时出错: " + e.getMessage());
        }
    }
}