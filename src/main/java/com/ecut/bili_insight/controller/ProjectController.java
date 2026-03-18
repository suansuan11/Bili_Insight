package com.ecut.bili_insight.controller;

import com.ecut.bili_insight.constant.Result;
import com.ecut.bili_insight.constant.ResultCode;
import com.ecut.bili_insight.entity.Project;
import com.ecut.bili_insight.entity.User;
import com.ecut.bili_insight.mapper.ProjectMapper;
import com.ecut.bili_insight.mapper.UserMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * 品牌监测项目管理控制器
 */
@RestController
@RequestMapping("/insight/projects")
public class ProjectController {

    private static final Logger logger = LoggerFactory.getLogger(ProjectController.class);

    @Autowired
    private ProjectMapper projectMapper;

    @Autowired
    private UserMapper userMapper;

    /**
     * 从 SecurityContext 获取当前登录用户，查库取完整 User 对象
     */
    private User getCurrentUser() {
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        if (auth == null || !auth.isAuthenticated()) {
            return null;
        }
        return userMapper.findByUsername(auth.getName());
    }

    /**
     * 获取项目列表（仅返回当前用户的项目）
     */
    @GetMapping("")
    public Result<List<Project>> listProjects() {
        try {
            User currentUser = getCurrentUser();
            if (currentUser == null) {
                return Result.failed(ResultCode.UNAUTHORIZED, "用户未登录");
            }
            List<Project> projects = projectMapper.findByUserId(currentUser.getId());
            return Result.success(projects);
        } catch (Exception e) {
            logger.error("获取项目列表失败", e);
            return Result.failed(ResultCode.FAILED, "获取项目列表失败: " + e.getMessage());
        }
    }

    /**
     * 获取单个项目详情（仅允许访问自己的项目）
     */
    @GetMapping("/{id}")
    public Result<Project> getProject(@PathVariable Long id) {
        try {
            User currentUser = getCurrentUser();
            if (currentUser == null) {
                return Result.failed(ResultCode.UNAUTHORIZED, "用户未登录");
            }
            Project project = projectMapper.findById(id);
            if (project == null) {
                return Result.failed(ResultCode.FAILED, "项目不存在");
            }
            if (!project.getUserId().equals(currentUser.getId())) {
                return Result.failed(ResultCode.UNAUTHORIZED, "无权访问该项目");
            }
            return Result.success(project);
        } catch (Exception e) {
            logger.error("获取项目详情失败, id={}", id, e);
            return Result.failed(ResultCode.FAILED, "获取项目详情失败: " + e.getMessage());
        }
    }

    /**
     * 创建项目（自动绑定当前用户）
     */
    @PostMapping("")
    public Result<Project> createProject(@RequestBody Project project) {
        try {
            User currentUser = getCurrentUser();
            if (currentUser == null) {
                return Result.failed(ResultCode.UNAUTHORIZED, "用户未登录");
            }
            project.setUserId(currentUser.getId());
            projectMapper.insert(project);
            return Result.success(project);
        } catch (Exception e) {
            logger.error("创建项目失败", e);
            return Result.failed(ResultCode.FAILED, "创建项目失败: " + e.getMessage());
        }
    }

    /**
     * 更新项目（仅允许修改自己的项目）
     */
    @PutMapping("/{id}")
    public Result<Project> updateProject(@PathVariable Long id, @RequestBody Project project) {
        try {
            User currentUser = getCurrentUser();
            if (currentUser == null) {
                return Result.failed(ResultCode.UNAUTHORIZED, "用户未登录");
            }
            Project existing = projectMapper.findById(id);
            if (existing == null) {
                return Result.failed(ResultCode.FAILED, "项目不存在");
            }
            if (!existing.getUserId().equals(currentUser.getId())) {
                return Result.failed(ResultCode.UNAUTHORIZED, "无权修改该项目");
            }
            project.setId(id);
            projectMapper.update(project);
            return Result.success(project);
        } catch (Exception e) {
            logger.error("更新项目失败, id={}", id, e);
            return Result.failed(ResultCode.FAILED, "更新项目失败: " + e.getMessage());
        }
    }

    /**
     * 删除项目（仅允许删除自己的项目）
     */
    @DeleteMapping("/{id}")
    public Result<Void> deleteProject(@PathVariable Long id) {
        try {
            User currentUser = getCurrentUser();
            if (currentUser == null) {
                return Result.failed(ResultCode.UNAUTHORIZED, "用户未登录");
            }
            Project existing = projectMapper.findById(id);
            if (existing == null) {
                return Result.failed(ResultCode.FAILED, "项目不存在");
            }
            if (!existing.getUserId().equals(currentUser.getId())) {
                return Result.failed(ResultCode.UNAUTHORIZED, "无权删除该项目");
            }
            projectMapper.deleteById(id);
            return Result.success();
        } catch (Exception e) {
            logger.error("删除项目失败, id={}", id, e);
            return Result.failed(ResultCode.FAILED, "删除项目失败: " + e.getMessage());
        }
    }
}
