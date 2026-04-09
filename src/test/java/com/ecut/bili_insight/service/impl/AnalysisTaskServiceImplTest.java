package com.ecut.bili_insight.service.impl;

import com.ecut.bili_insight.entity.AnalysisTask;
import com.ecut.bili_insight.mapper.AnalysisTaskMapper;
import com.ecut.bili_insight.mapper.SentimentTimelineMapper;
import com.ecut.bili_insight.mapper.VideoCommentMapper;
import com.ecut.bili_insight.mapper.VideoDanmakuMapper;
import com.ecut.bili_insight.service.PythonApiClient;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.mockito.ArgumentMatchers.isNull;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class AnalysisTaskServiceImplTest {

    @Mock
    private AnalysisTaskMapper taskMapper;

    @Mock
    private VideoCommentMapper commentMapper;

    @Mock
    private VideoDanmakuMapper danmakuMapper;

    @Mock
    private SentimentTimelineMapper timelineMapper;

    @Mock
    private PythonApiClient pythonApiClient;

    @InjectMocks
    private AnalysisTaskServiceImpl service;

    @Test
    void forceSubmitAnalysisTaskShouldPersistProjectIdForProjectTasks() {
        when(pythonApiClient.submitAnalysisTask(eq("BV1abc"), org.mockito.ArgumentMatchers.anyString(), isNull(), isNull(), isNull(), isNull()))
                .thenReturn(true);

        String taskId = service.forceSubmitAnalysisTask("BV1abc", 7L, 99L, null, null, null, null);

        ArgumentCaptor<AnalysisTask> captor = ArgumentCaptor.forClass(AnalysisTask.class);
        verify(taskMapper).insert(captor.capture());
        AnalysisTask inserted = captor.getValue();
        assertNotNull(taskId);
        assertEquals(taskId, inserted.getTaskId());
        assertEquals(Long.valueOf(99L), inserted.getProjectId());
    }

    @Test
    void submitAnalysisTaskShouldNotReuseCompletedStandaloneTaskForProjectTask() {
        when(pythonApiClient.submitAnalysisTask(eq("BV1abc"), org.mockito.ArgumentMatchers.anyString(), isNull(), isNull(), isNull(), isNull()))
                .thenReturn(true);

        String taskId = service.submitAnalysisTask("BV1abc", 7L, 99L, null, null, null, null);

        assertNotEquals("existing-task", taskId);
        ArgumentCaptor<AnalysisTask> captor = ArgumentCaptor.forClass(AnalysisTask.class);
        verify(taskMapper).insert(captor.capture());
        assertEquals(Long.valueOf(99L), captor.getValue().getProjectId());
    }
}
