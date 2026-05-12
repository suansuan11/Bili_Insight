package com.ecut.bili_insight.task;

import com.ecut.bili_insight.entity.AnalysisTask;
import com.ecut.bili_insight.entity.Project;
import com.ecut.bili_insight.entity.User;
import com.ecut.bili_insight.mapper.AnalysisTaskMapper;
import com.ecut.bili_insight.mapper.ProjectMapper;
import com.ecut.bili_insight.mapper.UserMapper;
import com.ecut.bili_insight.service.IAnalysisTaskService;
import com.ecut.bili_insight.service.BiliCredentialService;
import com.ecut.bili_insight.service.UserSettingsService;
import com.ecut.bili_insight.util.ProjectTargetBvidsCodec;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import java.time.LocalDateTime;
import java.util.Collections;
import java.util.List;

/**
 * 竞品监测定时调度器
 *
 * 每小时扫描所有项目的 target_bvids，对超过7天未分析的视频自动触发重新分析。
 */
@Component
public class ProjectMonitorScheduler {

    private static final Logger logger = LoggerFactory.getLogger(ProjectMonitorScheduler.class);

    /** 超过此天数则视为数据过期，需要重新分析 */
    private static final int STALE_DAYS = 7;

    @Autowired
    private ProjectMapper projectMapper;

    @Autowired
    private AnalysisTaskMapper analysisTaskMapper;

    @Autowired
    private IAnalysisTaskService analysisTaskService;

    @Autowired
    private UserMapper userMapper;

    @Autowired
    private BiliCredentialService biliCredentialService;

    @Autowired
    private UserSettingsService userSettingsService;

    /**
     * 每小时整点触发一次监测扫描
     */
    @Scheduled(cron = "0 0 * * * *")
    public void scanProjectTargets() {
        logger.info("[监测调度] 开始扫描所有项目的 target_bvids...");

        // 获取所有项目（findByUserId(null) 返回全部）
        List<Project> projects = projectMapper.findByUserId(null);
        if (projects == null || projects.isEmpty()) {
            logger.info("[监测调度] 暂无项目，跳过本轮扫描");
            return;
        }

        int triggered = 0;
        int skipped = 0;

        for (Project project : projects) {
            List<String> bvids = ProjectTargetBvidsCodec.parse(project.getTargetBvids());
            if (bvids.isEmpty()) {
                continue;
            }

            User user = userMapper.findById(project.getUserId());
            BiliCredentialService.CredentialStatus credentialStatus = biliCredentialService.checkCredential(user);
            if (credentialStatus.hasCredential() && credentialStatus.isExpired()) {
                logger.warn("[监测调度] 用户 {} 的 B站凭证已过期，跳过项目 {}",
                        project.getUserId(), project.getId());
                skipped += bvids.size();
                continue;
            }

            logger.info("[监测调度] 项目[{}] userId={} 共 {} 个监测目标",
                    project.getName(), project.getUserId(), bvids.size());

            for (String bvid : bvids) {
                if (needsAnalysis(project.getId(), project.getUserId(), bvid)) {
                    logger.info("[监测调度] 触发分析: bvid={}, projectId={}", bvid, project.getId());
                    submitProjectAnalysis(project, user, bvid);
                    triggered++;
                } else {
                    skipped++;
                }
            }
        }

        logger.info("[监测调度] 本轮扫描完成：触发 {} 个，跳过 {} 个", triggered, skipped);
    }

    /**
     * 判断某个 bvid 是否需要重新分析：
     * 没有已完成的任务，或最近完成的任务超过 STALE_DAYS 天
     */
    private boolean needsAnalysis(Long projectId, Long userId, String bvid) {
        AnalysisTask latest = latestCandidate(projectId, userId, bvid);
        if (latest == null) {
            return true;
        }

        String status = latest.getStatus();
        if ("PENDING".equals(status) || "RUNNING".equals(status)) {
            // 正在进行中则不重复提交
            return false;
        }

        if (!"COMPLETED".equals(status)) {
            // FAILED 等终态允许后续扫描重试
            return true;
        }

        // 已完成但数据过期
        LocalDateTime staleThreshold = LocalDateTime.now().minusDays(STALE_DAYS);
        LocalDateTime freshnessTime = latest.getCompletedAt() != null ? latest.getCompletedAt() : latest.getCreatedAt();
        return freshnessTime != null && freshnessTime.isBefore(staleThreshold);
    }

    private String getAnalysisEngine(Long userId) {
        return userSettingsService == null ? "transformer" : userSettingsService.getAnalysisEngine(userId);
    }

    private void submitProjectAnalysis(Project project, User user, String bvid) {
        String engine = getAnalysisEngine(project.getUserId());
        String sessdata = user != null ? user.getBiliSessdata() : null;
        String biliJct = user != null ? user.getBiliJct() : null;
        String buvid3 = user != null ? user.getBiliBuvid3() : null;
        String cookieJson = user != null ? user.getBiliCookieJson() : null;
        if ("snownlp".equals(engine)) {
            analysisTaskService.forceSubmitAnalysisTask(
                    bvid, project.getUserId(), project.getId(),
                    sessdata, biliJct, buvid3, cookieJson, engine
            );
        } else {
            analysisTaskService.forceSubmitAnalysisTask(
                    bvid, project.getUserId(), project.getId(),
                    sessdata, biliJct, buvid3, cookieJson
            );
        }
    }

    private AnalysisTask latestCandidate(Long projectId, Long userId, String bvid) {
        List<AnalysisTask> candidates = analysisTaskMapper.findProjectTaskCandidates(projectId, userId, bvid);
        if (candidates == null || candidates.isEmpty()) {
            return null;
        }
        return candidates.get(0);
    }
}
