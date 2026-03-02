// com.ecut.bili_insight.service.impl.PopularVideosServiceImpl.java
package com.ecut.bili_insight.service.impl;

import com.ecut.bili_insight.entity.VideoInfo;
import com.ecut.bili_insight.mapper.PopularVideoMapper;
import com.ecut.bili_insight.service.IPopularVideosService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.util.List;
import java.util.Map;

@Service
public class PopularVideosServiceImpl implements IPopularVideosService {

    private static final Logger logger = LoggerFactory.getLogger(PopularVideosServiceImpl.class);

    private final PopularVideoMapper popularVideoMapper;
    private final RestTemplate restTemplate;

    @Value("${python.service.url:http://localhost:8001}")
    private String pythonServiceUrl;

    public PopularVideosServiceImpl(
            PopularVideoMapper popularVideoMapper,
            RestTemplate restTemplate) {
        this.popularVideoMapper = popularVideoMapper;
        this.restTemplate = restTemplate;
    }

    /**
     * 异步触发热门视频爬取（调用Python API后台任务）
     * 不会阻塞启动，Python服务会在后台执行
     */
    @Override
    public void refreshAndSavePopularVideos() throws Exception {
        triggerPopularFetch();
    }

    @Override
    public void triggerPopularFetch() {
        logger.info("触发Python服务异步爬取热门视频...");

        try {
            String url = pythonServiceUrl + "/api/popular/fetch?pages=5&workers=10";
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);

            HttpEntity<Void> request = new HttpEntity<>(headers);
            ResponseEntity<String> response = restTemplate.postForEntity(url, request, String.class);

            if (response.getStatusCode() == HttpStatus.OK) {
                logger.info("热门视频爬取任务已提交到Python服务（后台执行）");
            } else {
                logger.warn("Python服务返回非200状态: {}", response.getStatusCode());
            }
        } catch (Exception e) {
            logger.error("调用Python服务失败（不影响启动）: {}", e.getMessage());
            throw new RuntimeException("调用Python热门抓取服务失败", e);
        }
    }


    @Override
    public Map<String, Object> getPopularFetchStatus() {
        logger.debug("查询Python热门视频抓取状态");
        try {
            String url = pythonServiceUrl + "/api/popular/fetch/status";
            ResponseEntity<Map> response = restTemplate.getForEntity(url, Map.class);
            if (response.getStatusCode() == HttpStatus.OK && response.getBody() != null) {
                return response.getBody();
            }
            throw new RuntimeException("Python服务返回异常状态: " + response.getStatusCode());
        } catch (Exception e) {
            logger.error("查询Python热门抓取状态失败: {}", e.getMessage());
            throw new RuntimeException("查询热门抓取状态失败", e);
        }
    }

    @Override
    public List<VideoInfo> getCurrentPopularVideos() {
        logger.info("从数据库查询当前热门视频列表");
        return popularVideoMapper.findAll();
    }
}