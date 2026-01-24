// com.ecut.bili_insight.controller.PopularVideosController.java
package com.ecut.bili_insight.controller;

import com.ecut.bili_insight.constant.Result;
import com.ecut.bili_insight.constant.ResultCode;
import com.ecut.bili_insight.entity.VideoInfo;
import com.ecut.bili_insight.service.IPopularVideosService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/insight/popular-videos")
public class PopularVideosController {

    private static final Logger logger = LoggerFactory.getLogger(PopularVideosController.class);

    private final IPopularVideosService popularVideosService;

    @Autowired
    public PopularVideosController(IPopularVideosService popularVideosService) {
        this.popularVideosService = popularVideosService;
    }

    /**
     * 获取当前存储在数据库中的热门视频列表
     * @return 热门视频列表
     */
    @GetMapping
    public Result<List<VideoInfo>> getPopularVideos() {
        logger.info("收到获取热门视频列表的API请求...");
        try {
            List<VideoInfo> videoList = popularVideosService.getCurrentPopularVideos();
            return Result.success(videoList);
        } catch (Exception e) {
            logger.error("获取热门视频列表失败", e);

            // ===== 【核心修改】 =====
            // 不再直接传入字符串，而是使用我们定义好的枚举和自定义消息
            // 您也可以只使用 Result.failed(ResultCode.FAILED)，它会返回"操作失败"的默认消息
            return Result.failed(ResultCode.FAILED, "获取热门视频列表时发生服务器内部错误");
        }
    }
}
