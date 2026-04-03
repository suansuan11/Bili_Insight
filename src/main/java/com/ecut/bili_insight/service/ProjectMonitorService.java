package com.ecut.bili_insight.service;

import com.ecut.bili_insight.entity.Project;
import com.ecut.bili_insight.entity.User;
import com.ecut.bili_insight.mapper.ProjectMapper;
import com.ecut.bili_insight.mapper.UserMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class ProjectMonitorService {
    private static final Logger logger = LoggerFactory.getLogger(ProjectMonitorService.class);

    @Autowired
    private ProjectMapper projectMapper;

    @Autowired
    private IAnalysisTaskService analysisTaskService;

    @Autowired
    private UserMapper userMapper;

    @Autowired
    private BiliCredentialService biliCredentialService;

    @Scheduled(cron = "0 0 */6 * * ?") // 每6小时执行一次
    public void monitorProjects() {
        logger.info("开始执行项目自动监测任务");

        List<Project> allProjects = projectMapper.findAll();

        for (Project project : allProjects) {
            if (project.getTargetBvids() != null && !project.getTargetBvids().isEmpty()) {
                User user = userMapper.findById(project.getUserId());
                BiliCredentialService.CredentialStatus credentialStatus = biliCredentialService.checkCredential(user);
                if (credentialStatus.hasCredential() && credentialStatus.isExpired()) {
                    logger.warn("项目 {} 所属用户 {} 的 B站凭证已过期，跳过自动监测任务",
                            project.getId(), project.getUserId());
                    continue;
                }

                String[] bvids = project.getTargetBvids().split(",");
                for (String bvid : bvids) {
                    try {
                        analysisTaskService.submitAnalysisTask(
                                bvid.trim(),
                                project.getUserId(),
                                user != null ? user.getBiliSessdata() : null,
                                user != null ? user.getBiliJct() : null,
                                user != null ? user.getBiliBuvid3() : null,
                                user != null ? user.getBiliCookieJson() : null
                        );
                        logger.info("项目 {} 自动提交分析任务: {}", project.getName(), bvid);
                    } catch (Exception e) {
                        logger.error("项目监测失败: project={}, bvid={}", project.getId(), bvid, e);
                    }
                }
            }
        }
    }
}
