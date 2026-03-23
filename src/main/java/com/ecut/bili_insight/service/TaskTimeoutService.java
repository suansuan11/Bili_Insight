package com.ecut.bili_insight.service;

import com.ecut.bili_insight.mapper.AnalysisTaskMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;

@Service
public class TaskTimeoutService {
    private static final Logger logger = LoggerFactory.getLogger(TaskTimeoutService.class);
    private static final int TIMEOUT_MINUTES = 30;

    @Autowired
    private AnalysisTaskMapper taskMapper;

    @Scheduled(fixedRate = 300000) // 每5分钟检查一次
    public void checkTimeoutTasks() {
        try {
            LocalDateTime timeoutThreshold = LocalDateTime.now().minusMinutes(TIMEOUT_MINUTES);
            int count = taskMapper.markTimeoutTasks(timeoutThreshold);
            if (count > 0) {
                logger.warn("Marked {} tasks as FAILED due to timeout", count);
            }
        } catch (Exception e) {
            logger.error("Error checking timeout tasks: {}", e.getMessage(), e);
        }
    }
}
