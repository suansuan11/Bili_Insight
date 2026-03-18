package com.ecut.bili_insight.task;

import com.ecut.bili_insight.entity.AnalysisTask;
import com.ecut.bili_insight.entity.Project;
import com.ecut.bili_insight.mapper.AnalysisTaskMapper;
import com.ecut.bili_insight.mapper.ProjectMapper;
import com.ecut.bili_insight.service.IAnalysisTaskService;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
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
    private ObjectMapper objectMapper;

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
            List<String> bvids = parseBvids(project.getTargetBvids());
            if (bvids.isEmpty()) {
                continue;
            }

            logger.info("[监测调度] 项目[{}] userId={} 共 {} 个监测目标",
                    project.getName(), project.getUserId(), bvids.size());

            for (String bvid : bvids) {
                if (needsAnalysis(bvid)) {
                    logger.info("[监测调度] 触发分析: bvid={}, projectId={}", bvid, project.getId());
                    // 监控任务由系统触发，sessdata=null 使用 Python 全局凭证
                    analysisTaskService.forceSubmitAnalysisTask(bvid, project.getUserId(), null);
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
    private boolean needsAnalysis(String bvid) {
        AnalysisTask latest = analysisTaskMapper.findByBvid(bvid);
        if (latest == null) {
            return true;
        }
        if (!"COMPLETED".equals(latest.getStatus())) {
            // 正在进行中（PENDING/RUNNING）则不重复提交
            return false;
        }
        // 已完成但数据过期
        LocalDateTime staleThreshold = LocalDateTime.now().minusDays(STALE_DAYS);
        return latest.getCreatedAt() != null && latest.getCreatedAt().isBefore(staleThreshold);
    }

    /**
     * 解析 target_bvids JSON 字符串为列表，解析失败时返回空列表
     */
    private List<String> parseBvids(String targetBvidsJson) {
        if (targetBvidsJson == null || targetBvidsJson.trim().isEmpty()) {
            return Collections.emptyList();
        }
        try {
            return objectMapper.readValue(targetBvidsJson, new TypeReference<List<String>>() {});
        } catch (Exception e) {
            logger.warn("[监测调度] target_bvids JSON 解析失败: {}, 内容: {}", e.getMessage(), targetBvidsJson);
            return Collections.emptyList();
        }
    }
}
