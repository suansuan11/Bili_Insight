package com.ecut.bili_insight.controller;

import com.ecut.bili_insight.constant.Result;
import com.ecut.bili_insight.constant.ResultCode;
import com.ecut.bili_insight.entity.AnalysisTask;
import com.ecut.bili_insight.entity.User;
import com.ecut.bili_insight.entity.VideoComment;
import com.ecut.bili_insight.entity.VideoDanmaku;
import com.ecut.bili_insight.entity.SentimentTimeline;
import com.ecut.bili_insight.mapper.UserMapper;
import com.ecut.bili_insight.service.IAnalysisTaskService;
import com.ecut.bili_insight.service.BiliCredentialService;
import com.ecut.bili_insight.service.PythonApiClient;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 视频分析控制器
 * 提供视频复盘分析相关的API接口
 */
@RestController
@RequestMapping("/insight/analysis")
public class AnalysisController {

    private static final Logger logger = LoggerFactory.getLogger(AnalysisController.class);

    @Autowired
    private IAnalysisTaskService analysisTaskService;

    @Autowired
    private UserMapper userMapper;

    @Autowired
    private BiliCredentialService biliCredentialService;

    @Autowired
    private PythonApiClient pythonApiClient;

    /** 获取当前登录用户（含B站凭证） */
    private User getCurrentUser() {
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        if (auth == null || !auth.isAuthenticated()) return null;
        return userMapper.findByUsername(auth.getName());
    }

    private Long getCurrentUserId() {
        User user = getCurrentUser();
        return user != null ? user.getId() : null;
    }

    /**
     * 提交视频分析任务
     * 
     * @param bvid 视频BVID
     * @return 任务ID和状态
     */
    @PostMapping("/submit")
    public Result<Map<String, Object>> submitAnalysis(@RequestParam String bvid) {
        logger.info("Received analysis submission request for BVID: {}", bvid);

        try {
            User currentUser = getCurrentUser();
            if (currentUser == null) {
                return Result.failed(ResultCode.UNAUTHORIZED, "用户未登录");
            }

            // 参数校验
            if (bvid == null || bvid.trim().isEmpty()) {
                return Result.failed(ResultCode.FAILED, "BVID不能为空");
            }

            // BVID格式验证
            if (!bvid.matches("^BV[a-zA-Z0-9]{10}$")) {
                return Result.failed(ResultCode.FAILED, "BVID格式无效");
            }

            BiliCredentialService.CredentialStatus credentialStatus = biliCredentialService.checkCredential(currentUser);
            if (credentialStatus.hasCredential() && credentialStatus.isExpired()) {
                return Result.failed(ResultCode.FAILED, "B站凭证已过期，请前往设置页重新扫码绑定");
            }

            Map<String, Object> probeResult = pythonApiClient.probeCommentAccess(
                    bvid,
                    currentUser.getBiliSessdata(),
                    currentUser.getBiliJct(),
                    currentUser.getBiliBuvid3(),
                    currentUser.getBiliCookieJson()
            );
            boolean riskControlled = Boolean.TRUE.equals(probeResult.get("riskControlled"));
            if (riskControlled) {
                String probeMessage = String.valueOf(probeResult.getOrDefault(
                        "message",
                        "B站评论接口当前触发风控，请稍后重试或重新绑定更稳定的浏览器态账号"
                ));
                return Result.failed(ResultCode.FAILED, probeMessage);
            }

            // 提交任务，携带当前用户的B站凭证（若已绑定）
            String taskId = analysisTaskService.submitAnalysisTask(
                    bvid,
                    currentUser.getId(),
                    currentUser.getBiliSessdata(),
                    currentUser.getBiliJct(),
                    currentUser.getBiliBuvid3(),
                    currentUser.getBiliCookieJson()
            );

            Map<String, Object> response = new HashMap<>();
            response.put("task_id", taskId);
            response.put("status", "PENDING");
            response.put("message", "任务已提交,正在分析中");

            logger.info("Analysis task submitted successfully: taskId={}", taskId);
            return Result.success(response);

        } catch (Exception e) {
            logger.error("Failed to submit analysis task for BVID: {}", bvid, e);
            return Result.failed(ResultCode.FAILED, "提交分析任务失败: " + e.getMessage());
        }
    }

    /**
     * 查询任务状态
     * 
     * @param taskId 任务ID
     * @return 任务状态信息
     */
    @GetMapping("/status/{taskId}")
    public Result<AnalysisTask> getTaskStatus(@PathVariable String taskId) {
        logger.debug("Received status query for task ID: {}", taskId);

        try {
            AnalysisTask task = analysisTaskService.getTaskStatus(taskId);

            if (task == null) {
                return Result.failed(ResultCode.FAILED, "任务不存在");
            }

            return Result.success(task);

        } catch (Exception e) {
            logger.error("Failed to get task status for ID: {}", taskId, e);
            return Result.failed(ResultCode.FAILED, "查询任务状态失败: " + e.getMessage());
        }
    }

    /**
     * 根据BVID查询任务
     * 
     * @param bvid 视频BVID
     * @return 任务信息
     */
    @GetMapping("/task")
    public Result<AnalysisTask> getTaskByBvid(@RequestParam String bvid) {
        logger.debug("Received task query for BVID: {}", bvid);

        try {
            AnalysisTask task = analysisTaskService.getTaskByBvid(bvid);

            if (task == null) {
                return Result.failed(ResultCode.FAILED, "未找到该视频的分析任务");
            }

            return Result.success(task);

        } catch (Exception e) {
            logger.error("Failed to get task by BVID: {}", bvid, e);
            return Result.failed(ResultCode.FAILED, "查询任务失败: " + e.getMessage());
        }
    }

    /**
     * 获取最近的任务列表
     * 
     * @param limit 限制数量,默认20
     * @return 任务列表
     */
    @GetMapping("/recent")
    public Result<List<AnalysisTask>> getRecentTasks(@RequestParam(defaultValue = "20") int limit) {
        logger.debug("Received request for recent tasks, limit: {}", limit);

        try {
            List<AnalysisTask> tasks = analysisTaskService.getRecentTasks(limit, getCurrentUserId());
            return Result.success(tasks);

        } catch (Exception e) {
            logger.error("Failed to get recent tasks", e);
            return Result.failed(ResultCode.FAILED, "获取最近任务失败: " + e.getMessage());
        }
    }

    /**
     * 获取分析结果概览
     * 
     * @param taskId 任务ID
     * @return 包含任务信息、统计、时间轴的概览数据
     */
    @GetMapping("/result/{taskId}")
    public Result<Map<String, Object>> getAnalysisResult(@PathVariable String taskId) {
        logger.info("Received complete result query for task ID: {}", taskId);

        try {
            User currentUser = getCurrentUser();
            if (currentUser == null) {
                return Result.failed(ResultCode.UNAUTHORIZED, "用户未登录");
            }

            Map<String, Object> result = analysisTaskService.getAnalysisResult(taskId, currentUser.getId());

            if (result == null || result.isEmpty()) {
                return Result.failed(ResultCode.FAILED, "分析结果不存在");
            }

            return Result.success(result);

        } catch (RuntimeException e) {
            logger.error("Permission denied or task not found: {}", e.getMessage());
            return Result.failed(ResultCode.UNAUTHORIZED, e.getMessage());
        } catch (Exception e) {
            logger.error("Failed to get analysis result for task ID: {}", taskId, e);
            return Result.failed(ResultCode.FAILED, "获取分析结果失败: " + e.getMessage());
        }
    }

    /**
     * 获取评论列表（分页）
     * 
     * @param taskId    任务ID
     * @param sentiment 情感标签(可选: POSITIVE/NEGATIVE/NEUTRAL)
     * @param aspect    切面(可选: 外观/性能/续航等)
     * @param page      页码，从1开始
     * @param size      每页大小
     * @return 分页评论列表
     */
    @GetMapping("/comments/{taskId}")
    public Result<Map<String, Object>> getComments(
            @PathVariable String taskId,
            @RequestParam(required = false) String sentiment,
            @RequestParam(required = false) String aspect,
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "20") int size) {

        logger.debug("Fetching comments for task {}: sentiment={}, aspect={}", taskId, sentiment, aspect);

        try {
            // 验证sentiment参数
            if (sentiment != null && !sentiment.matches("^(POSITIVE|NEGATIVE|NEUTRAL)$")) {
                return Result.failed(ResultCode.FAILED, "无效的情感标签");
            }

            // 验证aspect参数
            if (aspect != null && !aspect.matches("^[a-zA-Z0-9_\\u4e00-\\u9fff]{1,50}$")) {
                return Result.failed(ResultCode.FAILED, "无效的切面参数");
            }

            User currentUser = getCurrentUser();
            if (currentUser == null) {
                return Result.failed(ResultCode.UNAUTHORIZED, "用户未登录");
            }

            Map<String, Object> comments = analysisTaskService.getCommentsPage(
                    taskId,
                    currentUser.getId(),
                    sentiment,
                    aspect,
                    page,
                    size
            );
            return Result.success(comments);

        } catch (RuntimeException e) {
            logger.error("Failed to get comments for task ID: {}", taskId, e);
            return Result.failed(ResultCode.UNAUTHORIZED, e.getMessage());
        } catch (Exception e) {
            logger.error("Failed to get comments for task ID: {}", taskId, e);
            return Result.failed(ResultCode.FAILED, "获取评论失败");
        }
    }

    /**
     * 获取弹幕列表（分页）
     * 
     * @param taskId    任务ID
     * @param sentiment 情感标签(可选: POSITIVE/NEGATIVE/NEUTRAL)
     * @param page      页码，从1开始
     * @param size      每页大小
     * @return 分页弹幕列表
     */
    @GetMapping("/danmakus/{taskId}")
    public Result<Map<String, Object>> getDanmakus(
            @PathVariable String taskId,
            @RequestParam(required = false) String sentiment,
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "50") int size) {

        logger.debug("Fetching danmakus for task {}: sentiment={}", taskId, sentiment);

        try {
            User currentUser = getCurrentUser();
            if (currentUser == null) {
                return Result.failed(ResultCode.UNAUTHORIZED, "用户未登录");
            }

            Map<String, Object> danmakus = analysisTaskService.getDanmakusPage(
                    taskId,
                    currentUser.getId(),
                    sentiment,
                    page,
                    size
            );
            return Result.success(danmakus);

        } catch (RuntimeException e) {
            logger.error("Failed to get danmakus for task ID: {}", taskId, e);
            return Result.failed(ResultCode.UNAUTHORIZED, e.getMessage());
        } catch (Exception e) {
            logger.error("Failed to get danmakus for task ID: {}", taskId, e);
            return Result.failed(ResultCode.FAILED, "获取弹幕失败: " + e.getMessage());
        }
    }

    /**
     * 获取情绪时间轴
     * 
     * @param taskId 任务ID
     * @return 时间轴JSON数据
     */
    @GetMapping("/timeline/{taskId}")
    public Result<SentimentTimeline> getTimeline(@PathVariable String taskId) {
        logger.debug("Fetching timeline for task ID: {}", taskId);

        try {
            SentimentTimeline timeline = analysisTaskService.getTimeline(taskId);

            if (timeline == null) {
                return Result.failed(ResultCode.FAILED, "时间轴数据不存在");
            }

            return Result.success(timeline);

        } catch (Exception e) {
            logger.error("Failed to get timeline for task ID: {}", taskId, e);
            return Result.failed(ResultCode.FAILED, "获取时间轴失败: " + e.getMessage());
        }
    }
}
