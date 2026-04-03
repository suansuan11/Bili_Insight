package com.ecut.bili_insight.controller;

import com.ecut.bili_insight.constant.Result;
import com.ecut.bili_insight.constant.ResultCode;
import com.ecut.bili_insight.entity.User;
import com.ecut.bili_insight.entity.VideoInfo;
import com.ecut.bili_insight.mapper.UserMapper;
import com.ecut.bili_insight.service.BiliCredentialService;
import com.ecut.bili_insight.service.IPopularVideosService;
import com.ecut.bili_insight.service.PythonApiClient;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/insight/popular-videos")
public class PopularVideosController {

    private static final Logger logger = LoggerFactory.getLogger(PopularVideosController.class);

    private final IPopularVideosService popularVideosService;
    private final PythonApiClient pythonApiClient;
    private final UserMapper userMapper;
    private final BiliCredentialService biliCredentialService;

    @Autowired
    public PopularVideosController(IPopularVideosService popularVideosService,
                                   PythonApiClient pythonApiClient,
                                   UserMapper userMapper,
                                   BiliCredentialService biliCredentialService) {
        this.popularVideosService = popularVideosService;
        this.pythonApiClient = pythonApiClient;
        this.userMapper = userMapper;
        this.biliCredentialService = biliCredentialService;
    }

    private User getCurrentUser() {
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        if (auth == null || !auth.isAuthenticated()) {
            return null;
        }
        return userMapper.findByUsername(auth.getName());
    }

    /**
     * 获取当前存储在数据库中的热门视频列表
     */
    @GetMapping
    public Result<List<VideoInfo>> getPopularVideos() {
        logger.info("收到获取热门视频列表的API请求...");
        try {
            List<VideoInfo> videoList = popularVideosService.getCurrentPopularVideos();
            return Result.success(videoList);
        } catch (Exception e) {
            logger.error("获取热门视频列表失败", e);
            return Result.failed(ResultCode.FAILED, "获取热门视频列表时发生服务器内部错误");
        }
    }

    /**
     * 触发从B站抓取热门视频（代理到Python服务）
     */
    @PostMapping("/fetch")
    public ResponseEntity<String> fetchPopularVideos(@RequestParam(defaultValue = "3") int pages) {
        logger.info("触发抓取热门视频, pages={}", pages);
        try {
            User currentUser = getCurrentUser();
            BiliCredentialService.CredentialStatus credentialStatus = biliCredentialService.checkCredential(currentUser);
            if (credentialStatus.hasCredential() && credentialStatus.isExpired()) {
                return ResponseEntity.badRequest()
                        .body("{\"status\":\"error\",\"message\":\"B站凭证已过期，请前往设置页重新扫码绑定\"}");
            }

            String result = pythonApiClient.fetchPopularVideos(
                    pages,
                    currentUser != null ? currentUser.getBiliSessdata() : null,
                    currentUser != null ? currentUser.getBiliJct() : null,
                    currentUser != null ? currentUser.getBiliBuvid3() : null
            );
            return ResponseEntity.ok(result);
        } catch (Exception e) {
            logger.error("抓取热门视频失败", e);
            return ResponseEntity.status(500)
                    .body("{\"status\": \"error\", \"message\": \"" + e.getMessage() + "\"}");
        }
    }

    /**
     * 查询热门视频抓取状态（代理到Python服务）
     */
    @GetMapping("/fetch/status")
    public ResponseEntity<String> getFetchStatus() {
        try {
            String result = pythonApiClient.getPopularFetchStatus();
            return ResponseEntity.ok(result);
        } catch (Exception e) {
            return ResponseEntity.status(500)
                    .body("{\"status\": \"error\", \"message\": \"" + e.getMessage() + "\"}");
        }
    }
}
