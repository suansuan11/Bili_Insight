package com.ecut.bili_insight.controller;

import com.ecut.bili_insight.constant.Result;
import com.ecut.bili_insight.constant.ResultCode;
import com.ecut.bili_insight.mapper.DashboardMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Dashboard statistics controller
 */
@RestController
@RequestMapping("/insight/dashboard")
public class DashboardController {

    private static final Logger logger = LoggerFactory.getLogger(DashboardController.class);

    @Autowired
    private DashboardMapper dashboardMapper;

    /**
     * Get dashboard statistics
     *
     * @return statistics data
     */
    @GetMapping("/stats")
    public Result<Map<String, Object>> getDashboardStats() {
        logger.info("Fetching dashboard statistics");

        try {
            Map<String, Object> stats = new HashMap<>();

            Integer totalVideos = dashboardMapper.getTotalVideos();
            stats.put("total_videos", totalVideos != null ? totalVideos : 0);

            Integer totalComments = dashboardMapper.getTotalComments();
            stats.put("total_comments", totalComments != null ? totalComments : 0);

            Double avgSentiment = dashboardMapper.getAvgSentiment();
            stats.put("avg_sentiment", avgSentiment != null ? avgSentiment : 0.0);

            Integer totalTasks = dashboardMapper.getTotalTasks();
            stats.put("total_tasks", totalTasks != null ? totalTasks : 0);

            Integer completedTasks = dashboardMapper.getCompletedTasks();
            stats.put("completed_tasks", completedTasks != null ? completedTasks : 0);

            logger.info("Dashboard statistics fetched successfully");
            return Result.success(stats);

        } catch (Exception e) {
            logger.error("Failed to fetch dashboard statistics", e);
            return Result.failed(ResultCode.FAILED, "Failed to fetch statistics: " + e.getMessage());
        }
    }

    /**
     * Get sentiment distribution across all analyzed comments
     */
    @GetMapping("/sentiment-distribution")
    public Result<List<Map<String, Object>>> getSentimentDistribution() {
        try {
            List<Map<String, Object>> list = dashboardMapper.getSentimentDistribution();
            return Result.success(list);
        } catch (Exception e) {
            return Result.failed(ResultCode.FAILED, e.getMessage());
        }
    }

    /**
     * Get top aspects/keywords
     */
    @GetMapping("/top-aspects")
    public Result<List<Map<String, Object>>> getTopAspects() {
        try {
            List<Map<String, Object>> list = dashboardMapper.getTopAspects();
            return Result.success(list);
        } catch (Exception e) {
            return Result.failed(ResultCode.FAILED, e.getMessage());
        }
    }

    /**
     * Get analysis task trend for the last 7 days
     */
    @GetMapping("/task-trend")
    public Result<List<Map<String, Object>>> getTaskTrend() {
        try {
            List<Map<String, Object>> list = dashboardMapper.getTaskTrend();
            return Result.success(list);
        } catch (Exception e) {
            return Result.failed(ResultCode.FAILED, e.getMessage());
        }
    }
}
