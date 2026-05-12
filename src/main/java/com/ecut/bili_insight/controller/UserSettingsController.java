package com.ecut.bili_insight.controller;

import com.ecut.bili_insight.constant.Result;
import com.ecut.bili_insight.constant.ResultCode;
import com.ecut.bili_insight.entity.User;
import com.ecut.bili_insight.entity.UserSettings;
import com.ecut.bili_insight.mapper.DashboardMapper;
import com.ecut.bili_insight.mapper.UserMapper;
import com.ecut.bili_insight.service.UserSettingsService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDate;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/insight/settings")
public class UserSettingsController {

    @Autowired
    private UserMapper userMapper;

    @Autowired
    private UserSettingsService settingsService;

    @Autowired
    private DashboardMapper dashboardMapper;

    private User getCurrentUser() {
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        if (auth == null || !auth.isAuthenticated()) {
            return null;
        }
        return userMapper.findByUsername(auth.getName());
    }

    @GetMapping
    public Result<UserSettings> getSettings() {
        User user = getCurrentUser();
        if (user == null) {
            return Result.failed(ResultCode.UNAUTHORIZED, "用户未登录");
        }
        return Result.success(settingsService.getOrDefault(user.getId()));
    }

    @PutMapping
    public Result<UserSettings> saveSettings(@RequestBody UserSettings settings) {
        User user = getCurrentUser();
        if (user == null) {
            return Result.failed(ResultCode.UNAUTHORIZED, "用户未登录");
        }
        return Result.success(settingsService.save(user.getId(), settings));
    }

    @GetMapping("/weekly-report")
    public Result<Map<String, Object>> getWeeklyReport() {
        User user = getCurrentUser();
        if (user == null) {
            return Result.failed(ResultCode.UNAUTHORIZED, "用户未登录");
        }

        Long userId = user.getId();
        Map<String, Object> report = new HashMap<>();
        report.put("username", user.getUsername());
        report.put("period_start", LocalDate.now().minusDays(6).toString());
        report.put("period_end", LocalDate.now().toString());
        report.put("total_videos", defaultNumber(dashboardMapper.getTotalVideos(userId)));
        report.put("total_comments", defaultNumber(dashboardMapper.getTotalComments(userId)));
        report.put("avg_sentiment", defaultDouble(dashboardMapper.getAvgSentiment(userId)));
        report.put("total_tasks", defaultNumber(dashboardMapper.getTotalTasks(userId)));
        report.put("completed_tasks", defaultNumber(dashboardMapper.getCompletedTasks(userId)));
        report.put("sentiment_distribution", dashboardMapper.getSentimentDistribution(userId));
        List<Map<String, Object>> topAspects = dashboardMapper.getTopAspects(userId);
        report.put("top_aspects", topAspects);
        return Result.success(report);
    }

    private int defaultNumber(Integer value) {
        return value == null ? 0 : value;
    }

    private double defaultDouble(Double value) {
        return value == null ? 0.0 : value;
    }
}
