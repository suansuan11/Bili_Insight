package com.ecut.bili_insight.task;

import com.ecut.bili_insight.service.IPopularVideosService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Component;

/**
 * 应用启动初始化器
 *
 * 使用异步方式触发热门视频爬取，不会阻塞应用启动
 * 热门视频爬取任务会在Python服务后台执行
 */
@Component
public class StartupDataInitializer implements ApplicationRunner {

    private static final Logger logger = LoggerFactory.getLogger(StartupDataInitializer.class);
    private final IPopularVideosService popularVideosService;

    public StartupDataInitializer(IPopularVideosService popularVideosService) {
        this.popularVideosService = popularVideosService;
    }

    @Override
    @Async
    public void run(ApplicationArguments args) {
        logger.info("应用已启动，异步触发热门视频数据初始化任务...");
        try {
            // 调用Python API触发后台爬取，不会阻塞启动
            popularVideosService.refreshAndSavePopularVideos();
            logger.info("热门视频数据初始化任务已提交（后台执行）");
        } catch (Exception e) {
            logger.error("触发热门视频数据初始化失败（不影响应用启动）", e);
        }
    }
}