package com.ecut.bili_insight.controller;

import com.ecut.bili_insight.constant.Result;
import com.ecut.bili_insight.constant.ResultCode;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.JdbcTemplate;
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
    private JdbcTemplate jdbcTemplate;

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

            // Total videos count
            String videoCountSql = "SELECT COUNT(*) FROM popular_videos";
            Integer totalVideos = jdbcTemplate.queryForObject(videoCountSql, Integer.class);
            stats.put("total_videos", totalVideos != null ? totalVideos : 0);

            // Total comments count (from all analysis tasks)
            String commentCountSql = "SELECT COUNT(*) FROM video_comment";
            Integer totalComments = jdbcTemplate.queryForObject(commentCountSql, Integer.class);
            stats.put("total_comments", totalComments != null ? totalComments : 0);

            // Average sentiment score
            String avgSentimentSql = "SELECT AVG(CASE " +
                    "WHEN sentiment_label = 'POSITIVE' THEN 1.0 " +
                    "WHEN sentiment_label = 'NEGATIVE' THEN -1.0 " +
                    "ELSE 0 " +
                    "END) as avg_sentiment " +
                    "FROM video_comment";
            Double avgSentiment = jdbcTemplate.queryForObject(avgSentimentSql, Double.class);
            stats.put("avg_sentiment", avgSentiment != null ? avgSentiment : 0.0);

            // Total analysis tasks
            String taskCountSql = "SELECT COUNT(*) FROM analysis_task";
            Integer totalTasks = jdbcTemplate.queryForObject(taskCountSql, Integer.class);
            stats.put("total_tasks", totalTasks != null ? totalTasks : 0);

            // Completed tasks
            String completedTasksSql = "SELECT COUNT(*) FROM analysis_task WHERE status = 'COMPLETED'";
            Integer completedTasks = jdbcTemplate.queryForObject(completedTasksSql, Integer.class);
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
    public Result<Map<String, Object>> getSentimentDistribution() {
        try {
            String sql = "SELECT sentiment_label, COUNT(*) as count FROM video_comment GROUP BY sentiment_label";
            List<Map<String, Object>> list = jdbcTemplate.queryForList(sql);

            Map<String, Object> result = new HashMap<>();
            for (Map<String, Object> map : list) {
                result.put((String) map.get("sentiment_label"), map.get("count"));
            }
            return Result.success(result);
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
            String sql = "SELECT aspect, COUNT(*) as count FROM video_comment WHERE aspect != '' AND aspect IS NOT NULL GROUP BY aspect ORDER BY count DESC LIMIT 10";
            List<Map<String, Object>> list = jdbcTemplate.queryForList(sql);
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
            String sql = "SELECT DATE(created_at) as date, COUNT(*) as count " +
                    "FROM analysis_task " +
                    "WHERE created_at >= DATE_SUB(CURDATE(), INTERVAL 7 DAY) " +
                    "GROUP BY DATE(created_at) " +
                    "ORDER BY date ASC";
            List<Map<String, Object>> list = jdbcTemplate.queryForList(sql);
            return Result.success(list);
        } catch (Exception e) {
            return Result.failed(ResultCode.FAILED, e.getMessage());
        }
    }
}
