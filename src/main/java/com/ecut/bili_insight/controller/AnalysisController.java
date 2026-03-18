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

    /** 获取当前用户绑定的 B站 SESSDATA（可为null） */
    private String getCurrentUserSessdata() {
        User user = getCurrentUser();
        return user != null ? user.getBiliSessdata() : null;
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
            // 参数校验
            if (bvid == null || bvid.trim().isEmpty()) {
                return Result.failed(ResultCode.FAILED, "BVID不能为空");
            }

            // 提交任务，携带当前用户的B站凭证（若已绑定）
            String taskId = analysisTaskService.submitAnalysisTask(bvid, getCurrentUserId(), getCurrentUserSessdata());

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
     * 获取完整的分析结果
     * 
     * @param taskId 任务ID
     * @return 包含评论、弹幕、时间轴的完整数据
     */
    @GetMapping("/result/{taskId}")
    public Result<Map<String, Object>> getAnalysisResult(@PathVariable String taskId) {
        logger.info("Received complete result query for task ID: {}", taskId);

        try {
            Map<String, Object> result = analysisTaskService.getAnalysisResult(taskId);

            if (result == null || result.isEmpty()) {
                return Result.failed(ResultCode.FAILED, "分析结果不存在");
            }

            return Result.success(result);

        } catch (Exception e) {
            logger.error("Failed to get analysis result for task ID: {}", taskId, e);
            return Result.failed(ResultCode.FAILED, "获取分析结果失败: " + e.getMessage());
        }
    }

    /**
     * 获取评论列表
     * 
     * @param taskId    任务ID
     * @param sentiment 情感标签(可选: POSITIVE/NEGATIVE/NEUTRAL)
     * @param aspect    切面(可选: 外观/性能/续航等)
     * @return 评论列表
     */
    @GetMapping("/comments/{taskId}")
    public Result<List<VideoComment>> getComments(
            @PathVariable String taskId,
            @RequestParam(required = false) String sentiment,
            @RequestParam(required = false) String aspect) {

        logger.debug("Fetching comments for task {}: sentiment={}, aspect={}", taskId, sentiment, aspect);

        try {
            List<VideoComment> comments = analysisTaskService.getComments(taskId, sentiment, aspect);
            return Result.success(comments);

        } catch (Exception e) {
            logger.error("Failed to get comments for task ID: {}", taskId, e);
            return Result.failed(ResultCode.FAILED, "获取评论失败: " + e.getMessage());
        }
    }

    /**
     * 获取弹幕列表
     * 
     * @param taskId    任务ID
     * @param sentiment 情感标签(可选: POSITIVE/NEGATIVE/NEUTRAL)
     * @return 弹幕列表
     */
    @GetMapping("/danmakus/{taskId}")
    public Result<List<VideoDanmaku>> getDanmakus(
            @PathVariable String taskId,
            @RequestParam(required = false) String sentiment) {

        logger.debug("Fetching danmakus for task {}: sentiment={}", taskId, sentiment);

        try {
            List<VideoDanmaku> danmakus = analysisTaskService.getDanmakus(taskId, sentiment);
            return Result.success(danmakus);

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
