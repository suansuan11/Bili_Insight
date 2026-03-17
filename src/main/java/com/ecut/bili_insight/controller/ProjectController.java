package com.ecut.bili_insight.controller;

import com.ecut.bili_insight.constant.Result;
import com.ecut.bili_insight.constant.ResultCode;
import com.ecut.bili_insight.entity.Project;
import com.ecut.bili_insight.mapper.ProjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
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

    /**
     * 获取项目列表
     */
    @GetMapping("")
    public Result<List<Project>> listProjects() {
        try {
            // TODO: 后续从 SecurityContext 获取当前用户ID进行过滤
            List<Project> projects = projectMapper.findByUserId(null);
            return Result.success(projects);
        } catch (Exception e) {
            logger.error("获取项目列表失败", e);
            return Result.failed(ResultCode.FAILED, "获取项目列表失败: " + e.getMessage());
        }
    }

    /**
     * 获取单个项目详情
     */
    @GetMapping("/{id}")
    public Result<Project> getProject(@PathVariable Long id) {
        try {
            Project project = projectMapper.findById(id);
            if (project == null) {
                return Result.failed(ResultCode.FAILED, "项目不存在");
            }
            return Result.success(project);
        } catch (Exception e) {
            logger.error("获取项目详情失败, id={}", id, e);
            return Result.failed(ResultCode.FAILED, "获取项目详情失败: " + e.getMessage());
        }
    }

    /**
     * 创建项目
     */
    @PostMapping("")
    public Result<Project> createProject(@RequestBody Project project) {
        try {
            // TODO: 从 SecurityContext 获取当前用户ID
            projectMapper.insert(project);
            return Result.success(project);
        } catch (Exception e) {
            logger.error("创建项目失败", e);
            return Result.failed(ResultCode.FAILED, "创建项目失败: " + e.getMessage());
        }
    }

    /**
     * 更新项目
     */
    @PutMapping("/{id}")
    public Result<Project> updateProject(@PathVariable Long id, @RequestBody Project project) {
        try {
            Project existing = projectMapper.findById(id);
            if (existing == null) {
                return Result.failed(ResultCode.FAILED, "项目不存在");
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
     * 删除项目
     */
    @DeleteMapping("/{id}")
    public Result<Void> deleteProject(@PathVariable Long id) {
        try {
            Project existing = projectMapper.findById(id);
            if (existing == null) {
                return Result.failed(ResultCode.FAILED, "项目不存在");
            }
            projectMapper.deleteById(id);
            return Result.success();
        } catch (Exception e) {
            logger.error("删除项目失败, id={}", id, e);
            return Result.failed(ResultCode.FAILED, "删除项目失败: " + e.getMessage());
        }
    }
}
