package com.ecut.bili_insight.service;

import com.ecut.bili_insight.task.ProjectMonitorScheduler;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

@Service
public class ProjectMonitorService {
    private static final Logger logger = LoggerFactory.getLogger(ProjectMonitorService.class);

    @Autowired
    private ProjectMonitorScheduler projectMonitorScheduler;

    public void monitorProjects() {
        logger.info("ProjectMonitorService.monitorProjects 已委托给 ProjectMonitorScheduler.scanProjectTargets");
        projectMonitorScheduler.scanProjectTargets();
    }
}
