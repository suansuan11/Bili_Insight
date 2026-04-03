package com.ecut.bili_insight.controller;

import com.ecut.bili_insight.constant.Result;
import com.ecut.bili_insight.constant.ResultCode;
import com.ecut.bili_insight.entity.User;
import com.ecut.bili_insight.mapper.DashboardMapper;
import com.ecut.bili_insight.mapper.UserMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.time.LocalDate;
import java.util.ArrayList;

/**
 * Dashboard statistics controller
 */
@RestController
@RequestMapping("/insight/dashboard")
public class DashboardController {

    private static final Logger logger = LoggerFactory.getLogger(DashboardController.class);

    @Autowired
    private DashboardMapper dashboardMapper;

    @Autowired
    private UserMapper userMapper;

    private Long getCurrentUserId() {
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        if (auth == null || !auth.isAuthenticated()) {
            return null;
        }
        User user = userMapper.findByUsername(auth.getName());
        return user != null ? user.getId() : null;
    }

    /**
     * Get dashboard statistics for current user
     */
    @GetMapping("/stats")
    public Result<Map<String, Object>> getDashboardStats() {
        logger.info("Fetching dashboard statistics");

        try {
            Long userId = getCurrentUserId();
            Map<String, Object> stats = new HashMap<>();

            Integer totalVideos = dashboardMapper.getTotalVideos(userId);
            stats.put("total_videos", totalVideos != null ? totalVideos : 0);

            Integer totalComments = dashboardMapper.getTotalComments(userId);
            stats.put("total_comments", totalComments != null ? totalComments : 0);

            Double avgSentiment = dashboardMapper.getAvgSentiment(userId);
            stats.put("avg_sentiment", avgSentiment != null ? avgSentiment : 0.0);

            Integer totalTasks = dashboardMapper.getTotalTasks(userId);
            stats.put("total_tasks", totalTasks != null ? totalTasks : 0);

            Integer completedTasks = dashboardMapper.getCompletedTasks(userId);
            stats.put("completed_tasks", completedTasks != null ? completedTasks : 0);

            logger.info("Dashboard statistics fetched successfully");
            return Result.success(stats);

        } catch (Exception e) {
            logger.error("Failed to fetch dashboard statistics", e);
            return Result.failed(ResultCode.FAILED, "Failed to fetch statistics: " + e.getMessage());
        }
    }

    /**
     * Get sentiment distribution for current user's analyzed comments.
     * 返回格式:
     * {
     *   "counts": { "POSITIVE": 100, "NEUTRAL": 50, "NEGATIVE": 30 },
     *   "intensityBreakdown": {
     *     "POSITIVE": { "WEAK": 10, "MEDIUM": 40, "STRONG": 50 },
     *     "NEUTRAL": { "WEAK": 50, "MEDIUM": 0, "STRONG": 0 },
     *     "NEGATIVE": { "WEAK": 5, "MEDIUM": 10, "STRONG": 15 }
     *   },
     *   "total": 180
     * }
     */
    @GetMapping("/sentiment-distribution")
    public Result<Map<String, Object>> getSentimentDistribution() {
        try {
            List<Map<String, Object>> list = dashboardMapper.getSentimentDistribution(getCurrentUserId());
            Map<String, Object> result = new HashMap<>();
            Map<String, Integer> counts = new HashMap<>();
            counts.put("POSITIVE", 0);
            counts.put("NEUTRAL", 0);
            counts.put("NEGATIVE", 0);

            Map<String, Map<String, Integer>> intensityBreakdown = new HashMap<>();
            intensityBreakdown.put("POSITIVE", createEmptyIntensityMap());
            intensityBreakdown.put("NEUTRAL", createEmptyIntensityMap());
            intensityBreakdown.put("NEGATIVE", createEmptyIntensityMap());

            int total = 0;
            for (Map<String, Object> row : list) {
                String label = String.valueOf(row.get("sentiment_label"));
                String intensity = row.get("sentiment_intensity") == null ? "WEAK" : String.valueOf(row.get("sentiment_intensity"));
                Object count = row.get("count");
                if (label != null && count instanceof Number && counts.containsKey(label)) {
                    int countValue = ((Number) count).intValue();
                    total += countValue;
                    counts.put(label, counts.get(label) + countValue);

                    Map<String, Integer> labelBreakdown = intensityBreakdown.get(label);
                    if (labelBreakdown != null) {
                        labelBreakdown.put(intensity, labelBreakdown.getOrDefault(intensity, 0) + countValue);
                    }
                }
            }

            result.put("counts", counts);
            result.put("intensityBreakdown", intensityBreakdown);
            result.put("total", total);
            return Result.success(result);
        } catch (Exception e) {
            return Result.failed(ResultCode.FAILED, e.getMessage());
        }
    }

    /**
     * Get top aspects for current user's analyzed comments
     */
    @GetMapping("/top-aspects")
    public Result<List<Map<String, Object>>> getTopAspects() {
        try {
            List<Map<String, Object>> list = dashboardMapper.getTopAspects(getCurrentUserId());
            return Result.success(list);
        } catch (Exception e) {
            return Result.failed(ResultCode.FAILED, e.getMessage());
        }
    }

    /**
     * Get analysis task trend for the last 7 days (current user)
     */
    @GetMapping("/task-trend")
    public Result<List<Map<String, Object>>> getTaskTrend() {
        try {
            List<Map<String, Object>> raw = dashboardMapper.getTaskTrend(getCurrentUserId());
            Map<String, Number> countByDate = new HashMap<>();
            for (Map<String, Object> row : raw) {
                if (row.get("date") != null && row.get("count") != null) {
                    countByDate.put(String.valueOf(row.get("date")), (Number) row.get("count"));
                }
            }

            List<Map<String, Object>> normalized = new ArrayList<>();
            LocalDate today = LocalDate.now();
            for (int i = 6; i >= 0; i--) {
                LocalDate date = today.minusDays(i);
                String dateStr = date.toString();
                Map<String, Object> item = new HashMap<>();
                item.put("date", dateStr);
                item.put("count", countByDate.getOrDefault(dateStr, 0));
                normalized.add(item);
            }

            return Result.success(normalized);
        } catch (Exception e) {
            return Result.failed(ResultCode.FAILED, e.getMessage());
        }
    }

    private Map<String, Integer> createEmptyIntensityMap() {
        Map<String, Integer> map = new HashMap<>();
        map.put("WEAK", 0);
        map.put("MEDIUM", 0);
        map.put("STRONG", 0);
        return map;
    }
}
