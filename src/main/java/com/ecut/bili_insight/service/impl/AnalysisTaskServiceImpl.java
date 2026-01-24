package com.ecut.bili_insight.service.impl;

import com.ecut.bili_insight.entity.AnalysisTask;
import com.ecut.bili_insight.entity.VideoComment;
import com.ecut.bili_insight.entity.VideoDanmaku;
import com.ecut.bili_insight.entity.SentimentTimeline;
import com.ecut.bili_insight.mapper.AnalysisTaskMapper;
import com.ecut.bili_insight.mapper.VideoCommentMapper;
import com.ecut.bili_insight.mapper.VideoDanmakuMapper;
import com.ecut.bili_insight.mapper.SentimentTimelineMapper;
import com.ecut.bili_insight.service.IAnalysisTaskService;
import com.ecut.bili_insight.service.PythonApiClient;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 视频分析任务服务实现
 */
@Service
public class AnalysisTaskServiceImpl implements IAnalysisTaskService {

    private static final Logger logger = LoggerFactory.getLogger(AnalysisTaskServiceImpl.class);

    @Autowired
    private AnalysisTaskMapper taskMapper;

    @Autowired
    private VideoCommentMapper commentMapper;

    @Autowired
    private VideoDanmakuMapper danmakuMapper;

    @Autowired
    private SentimentTimelineMapper timelineMapper;

    @Autowired
    private PythonApiClient pythonApiClient;

    /**
     * 提交视频分析任务
     * 1. 在数据库创建任务记录(状态PENDING)
     * 2. 提交事务后异步调用Python服务
     * 3. 立即返回任务ID给前端
     */
    @Override
    public Long submitAnalysisTask(String bvid) {
        logger.info("Submitting analysis task for BVID: {}", bvid);

        // 检查是否已有相同BVID的任务
        AnalysisTask existingTask = taskMapper.findByBvid(bvid);
        if (existingTask != null && "COMPLETED".equals(existingTask.getStatus())) {
            logger.info("Task already completed for BVID: {}, returning existing task ID: {}",
                    bvid, existingTask.getTaskId());
            return existingTask.getTaskId();
        }

        // 在事务中创建新任务
        Long taskId = createTaskInTransaction(bvid);
        logger.info("Created task with ID: {}", taskId);

        // 事务提交后，异步调用Python服务
        callPythonServiceAsync(bvid, taskId);

        return taskId;
    }

    /**
     * 在事务中创建任务
     */
    @Transactional
    protected Long createTaskInTransaction(String bvid) {
        AnalysisTask task = new AnalysisTask();
        task.setBvid(bvid);
        task.setStatus("PENDING");
        task.setProgress(0);
        task.setCurrentStep("Task submitted");

        taskMapper.insert(task);
        return task.getTaskId();
    }

    /**
     * 异步调用Python分析服务
     */
    @Async
    protected void callPythonServiceAsync(String bvid, Long taskId) {
        try {
            logger.info("Calling Python service asynchronously for task {}", taskId);

            boolean success = pythonApiClient.submitAnalysisTask(bvid, taskId);

            if (!success) {
                // 如果调用失败,更新任务状态为FAILED
                taskMapper.updateStatus(taskId, "FAILED", "Failed to call Python service");
                logger.error("Python service call failed for task {}", taskId);
            }

        } catch (Exception e) {
            logger.error("Error in async Python service call: {}", e.getMessage(), e);
            taskMapper.updateStatus(taskId, "FAILED", e.getMessage());
        }
    }

    /**
     * 查询任务状态
     */
    @Override
    public AnalysisTask getTaskStatus(Long taskId) {
        logger.debug("Fetching task status for ID: {}", taskId);
        return taskMapper.findById(taskId);
    }

    /**
     * 根据BVID查询最新任务
     */
    @Override
    public AnalysisTask getTaskByBvid(String bvid) {
        logger.debug("Fetching task by BVID: {}", bvid);
        return taskMapper.findByBvid(bvid);
    }

    /**
     * 获取最近的任务列表
     */
    @Override
    public List<AnalysisTask> getRecentTasks(int limit) {
        logger.debug("Fetching recent tasks, limit: {}", limit);
        return taskMapper.findRecent(limit);
    }

    /**
     * 获取完整的分析结果
     * 包含评论、弹幕、时间轴、统计数据
     */
    @Override
    public Map<String, Object> getAnalysisResult(Long taskId) {
        logger.info("Fetching complete analysis result for task {}", taskId);

        Map<String, Object> result = new HashMap<>();

        // 1. 任务基本信息
        AnalysisTask task = taskMapper.findById(taskId);
        result.put("task", task);

        if (task == null || !"COMPLETED".equals(task.getStatus())) {
            logger.warn("Task {} is not completed or not found", taskId);
            return result;
        }

        // 2. 评论数据
        List<VideoComment> comments = commentMapper.findByTaskId(taskId);
        result.put("comments", comments);
        result.put("comment_count", commentMapper.countByTaskId(taskId));

        // 3. 弹幕数据
        List<VideoDanmaku> danmakus = danmakuMapper.findByTaskId(taskId);
        result.put("danmakus", danmakus);
        result.put("danmaku_count", danmakuMapper.countByTaskId(taskId));

        // 4. 情绪时间轴
        SentimentTimeline timeline = timelineMapper.findByTaskId(taskId);
        result.put("timeline", timeline);

        // 5. 统计数据
        result.put("statistics", calculateStatistics(comments));

        logger.info("Analysis result fetched successfully for task {}", taskId);
        return result;
    }

    /**
     * 获取评论列表(支持筛选)
     */
    @Override
    public List<VideoComment> getComments(Long taskId, String sentimentLabel, String aspect) {
        if (sentimentLabel != null && !sentimentLabel.isEmpty()) {
            logger.debug("Fetching comments by sentiment: {} for task {}", sentimentLabel, taskId);
            return commentMapper.findByTaskIdAndSentiment(taskId, sentimentLabel);
        } else if (aspect != null && !aspect.isEmpty()) {
            logger.debug("Fetching comments by aspect: {} for task {}", aspect, taskId);
            return commentMapper.findByTaskIdAndAspect(taskId, aspect);
        } else {
            logger.debug("Fetching all comments for task {}", taskId);
            return commentMapper.findByTaskId(taskId);
        }
    }

    /**
     * 获取弹幕列表(支持筛选)
     */
    @Override
    public List<VideoDanmaku> getDanmakus(Long taskId, String sentimentLabel) {
        if (sentimentLabel != null && !sentimentLabel.isEmpty()) {
            logger.debug("Fetching danmakus by sentiment: {} for task {}", sentimentLabel, taskId);
            return danmakuMapper.findByTaskIdAndSentiment(taskId, sentimentLabel);
        } else {
            logger.debug("Fetching all danmakus for task {}", taskId);
            return danmakuMapper.findByTaskId(taskId);
        }
    }

    /**
     * 获取情绪时间轴
     */
    @Override
    public SentimentTimeline getTimeline(Long taskId) {
        logger.debug("Fetching timeline for task {}", taskId);
        return timelineMapper.findByTaskId(taskId);
    }

    /**
     * 计算统计数据
     */
    private Map<String, Object> calculateStatistics(List<VideoComment> comments) {
        Map<String, Object> stats = new HashMap<>();

        if (comments == null || comments.isEmpty()) {
            return stats;
        }

        long positiveCount = comments.stream()
                .filter(c -> "POSITIVE".equals(c.getSentimentLabel()))
                .count();
        long negativeCount = comments.stream()
                .filter(c -> "NEGATIVE".equals(c.getSentimentLabel()))
                .count();
        long neutralCount = comments.stream()
                .filter(c -> "NEUTRAL".equals(c.getSentimentLabel()))
                .count();

        stats.put("positive_count", positiveCount);
        stats.put("negative_count", negativeCount);
        stats.put("neutral_count", neutralCount);
        stats.put("positive_ratio", (double) positiveCount / comments.size());
        stats.put("negative_ratio", (double) negativeCount / comments.size());

        return stats;
    }
}
