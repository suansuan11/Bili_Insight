package com.ecut.bili_insight.task;

import com.ecut.bili_insight.entity.UserSettings;
import com.ecut.bili_insight.mapper.UserSettingsMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import java.time.LocalDateTime;
import java.util.List;

@Component
public class DataRetentionCleanupScheduler {

    private static final Logger logger = LoggerFactory.getLogger(DataRetentionCleanupScheduler.class);

    @Autowired
    private UserSettingsMapper settingsMapper;

    @Scheduled(cron = "0 30 3 * * *")
    public void cleanupExpiredAnalysisData() {
        List<UserSettings> settings = settingsMapper.findUsersWithRetention();
        int deleted = 0;
        for (UserSettings item : settings) {
            Integer days = parseDays(item.getDataRetention());
            if (days == null) {
                continue;
            }
            LocalDateTime cutoff = LocalDateTime.now().minusDays(days);
            deleted += settingsMapper.deleteTerminalTasksBefore(item.getUserId(), cutoff);
        }
        if (deleted > 0) {
            logger.info("[数据保留] 已清理过期分析任务 {} 个", deleted);
        }
    }

    private Integer parseDays(String retention) {
        if ("30".equals(retention)) {
            return 30;
        }
        if ("90".equals(retention)) {
            return 90;
        }
        return null;
    }
}
