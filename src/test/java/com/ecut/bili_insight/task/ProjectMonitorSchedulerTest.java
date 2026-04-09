package com.ecut.bili_insight.task;

import com.ecut.bili_insight.entity.AnalysisTask;
import com.ecut.bili_insight.entity.Project;
import com.ecut.bili_insight.entity.User;
import com.ecut.bili_insight.mapper.AnalysisTaskMapper;
import com.ecut.bili_insight.mapper.ProjectMapper;
import com.ecut.bili_insight.mapper.UserMapper;
import com.ecut.bili_insight.service.BiliCredentialService;
import com.ecut.bili_insight.service.IAnalysisTaskService;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.time.LocalDateTime;
import java.util.Collections;

import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.isNull;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class ProjectMonitorSchedulerTest {

    @Mock
    private ProjectMapper projectMapper;

    @Mock
    private AnalysisTaskMapper analysisTaskMapper;

    @Mock
    private IAnalysisTaskService analysisTaskService;

    @Mock
    private UserMapper userMapper;

    @Mock
    private BiliCredentialService biliCredentialService;

    @InjectMocks
    private ProjectMonitorScheduler scheduler;

    @Test
    void scanProjectTargetsShouldRetryFailedTasks() {
        Project project = buildProject(11L, 7L, "[\"BV1abc\"]");
        User user = buildUser(7L);
        AnalysisTask failedTask = new AnalysisTask();
        failedTask.setStatus("FAILED");
        failedTask.setCreatedAt(LocalDateTime.now().minusHours(1));

        when(projectMapper.findByUserId(null)).thenReturn(Collections.singletonList(project));
        when(userMapper.findById(7L)).thenReturn(user);
        when(biliCredentialService.checkCredential(user)).thenReturn(new BiliCredentialService.CredentialStatus(user));
        when(analysisTaskMapper.findProjectTaskCandidates(11L, 7L, "BV1abc"))
                .thenReturn(Collections.singletonList(failedTask));

        scheduler.scanProjectTargets();

        verify(analysisTaskService).forceSubmitAnalysisTask("BV1abc", 7L, 11L, null, null, null, null);
    }

    @Test
    void scanProjectTargetsShouldUseCompletedAtForFreshTasks() {
        Project project = buildProject(11L, 7L, "[\"BV1abc\"]");
        User user = buildUser(7L);
        AnalysisTask completedTask = new AnalysisTask();
        completedTask.setStatus("COMPLETED");
        completedTask.setCreatedAt(LocalDateTime.now().minusDays(10));
        completedTask.setCompletedAt(LocalDateTime.now().minusHours(2));

        when(projectMapper.findByUserId(null)).thenReturn(Collections.singletonList(project));
        when(userMapper.findById(7L)).thenReturn(user);
        when(biliCredentialService.checkCredential(user)).thenReturn(new BiliCredentialService.CredentialStatus(user));
        when(analysisTaskMapper.findProjectTaskCandidates(11L, 7L, "BV1abc"))
                .thenReturn(Collections.singletonList(completedTask));

        scheduler.scanProjectTargets();

        verify(analysisTaskService, never()).forceSubmitAnalysisTask(anyString(), org.mockito.ArgumentMatchers.anyLong(), org.mockito.ArgumentMatchers.any(), isNull(), isNull(), isNull(), isNull());
    }

    @Test
    void scanProjectTargetsShouldRespectHistoricalUserTaskBeforeProjectBackfill() {
        Project project = buildProject(11L, 7L, "[\"BV1abc\"]");
        User user = buildUser(7L);
        AnalysisTask legacyCompletedTask = new AnalysisTask();
        legacyCompletedTask.setStatus("COMPLETED");
        legacyCompletedTask.setCreatedAt(LocalDateTime.now().minusDays(3));
        legacyCompletedTask.setCompletedAt(LocalDateTime.now().minusDays(1));

        when(projectMapper.findByUserId(null)).thenReturn(Collections.singletonList(project));
        when(userMapper.findById(7L)).thenReturn(user);
        when(biliCredentialService.checkCredential(user)).thenReturn(new BiliCredentialService.CredentialStatus(user));
        when(analysisTaskMapper.findProjectTaskCandidates(11L, 7L, "BV1abc"))
                .thenReturn(Collections.singletonList(legacyCompletedTask));

        scheduler.scanProjectTargets();

        verify(analysisTaskService, never()).forceSubmitAnalysisTask(anyString(), org.mockito.ArgumentMatchers.anyLong(), org.mockito.ArgumentMatchers.any(), isNull(), isNull(), isNull(), isNull());
    }

    private Project buildProject(Long projectId, Long userId, String targetBvids) {
        Project project = new Project();
        project.setId(projectId);
        project.setUserId(userId);
        project.setName("监测项目");
        project.setTargetBvids(targetBvids);
        return project;
    }

    private User buildUser(Long userId) {
        User user = new User();
        user.setId(userId);
        return user;
    }
}
