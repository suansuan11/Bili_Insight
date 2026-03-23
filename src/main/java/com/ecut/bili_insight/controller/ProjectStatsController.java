package com.ecut.bili_insight.controller;

import com.ecut.bili_insight.constant.Result;
import com.ecut.bili_insight.constant.ResultCode;
import com.ecut.bili_insight.entity.User;
import com.ecut.bili_insight.mapper.UserMapper;
import com.ecut.bili_insight.service.ProjectAggregationService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/insight/project-stats")
public class ProjectStatsController {

    @Autowired
    private ProjectAggregationService aggregationService;

    @Autowired
    private UserMapper userMapper;

    private User getCurrentUser() {
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        if (auth == null) return null;
        return userMapper.findByUsername(auth.getName());
    }

    @GetMapping("/{projectId}")
    public Result<Map<String, Object>> getProjectStats(@PathVariable Long projectId) {
        User user = getCurrentUser();
        if (user == null) {
            return Result.failed(ResultCode.UNAUTHORIZED, "用户未登录");
        }

        try {
            Map<String, Object> stats = aggregationService.getProjectStatistics(projectId, user.getId());
            return Result.success(stats);
        } catch (Exception e) {
            return Result.failed(ResultCode.FAILED, e.getMessage());
        }
    }
}
