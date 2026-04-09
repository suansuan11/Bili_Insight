package com.ecut.bili_insight.service;

import com.ecut.bili_insight.entity.AnalysisTask;
import com.ecut.bili_insight.entity.Project;
import com.ecut.bili_insight.mapper.AnalysisTaskMapper;
import com.ecut.bili_insight.mapper.ProjectMapper;
import com.ecut.bili_insight.mapper.VideoCommentMapper;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.time.LocalDateTime;
import java.util.Arrays;
import java.util.Collections;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class ProjectAggregationServiceTest {

    @Mock
    private ProjectMapper projectMapper;

    @Mock
    private AnalysisTaskMapper taskMapper;

    @Mock
    private VideoCommentMapper commentMapper;

    @InjectMocks
    private ProjectAggregationService aggregationService;

    @Test
    void getProjectStatisticsShouldOnlyCountLatestTaskPerBvid() {
        Project project = new Project();
        project.setId(11L);
        project.setUserId(7L);
        project.setTargetBvids("[\"BV1abc\",\"BV2def\"]");

        AnalysisTask latestBv1 = completedTask("task-new", "BV1abc", LocalDateTime.now().minusHours(1));
        AnalysisTask olderBv1 = completedTask("task-old", "BV1abc", LocalDateTime.now().minusDays(3));
        AnalysisTask latestBv2 = completedTask("task-bv2", "BV2def", LocalDateTime.now().minusHours(2));

        when(projectMapper.findById(11L)).thenReturn(project);
        when(taskMapper.findProjectTaskCandidates(11L, 7L, "BV1abc")).thenReturn(Arrays.asList(latestBv1, olderBv1));
        when(taskMapper.findProjectTaskCandidates(11L, 7L, "BV2def")).thenReturn(Collections.singletonList(latestBv2));

        when(commentMapper.countByTaskId("task-new")).thenReturn(4);
        when(commentMapper.countByTaskIdAndSentiment("task-new", "POSITIVE")).thenReturn(1);
        when(commentMapper.countByTaskIdAndSentiment("task-new", "NEGATIVE")).thenReturn(1);

        when(commentMapper.countByTaskId("task-bv2")).thenReturn(2);
        when(commentMapper.countByTaskIdAndSentiment("task-bv2", "POSITIVE")).thenReturn(1);
        when(commentMapper.countByTaskIdAndSentiment("task-bv2", "NEGATIVE")).thenReturn(0);

        Map<String, Object> stats = aggregationService.getProjectStatistics(11L, 7L);

        assertEquals(2, stats.get("total_tasks"));
        assertEquals(2L, stats.get("completed_tasks"));
        assertEquals(6, stats.get("total_comments"));
        assertEquals(2d / 6d, (Double) stats.get("positive_ratio"), 0.0001);
        assertEquals(1d / 6d, (Double) stats.get("negative_ratio"), 0.0001);
    }

    @Test
    void getProjectStatisticsShouldPreferLatestCompletedTaskWhenNewestAttemptFailed() {
        Project project = new Project();
        project.setId(11L);
        project.setUserId(7L);
        project.setTargetBvids("[\"BV1abc\"]");

        AnalysisTask failedNewest = new AnalysisTask();
        failedNewest.setTaskId("task-failed");
        failedNewest.setBvid("BV1abc");
        failedNewest.setStatus("FAILED");
        failedNewest.setCreatedAt(LocalDateTime.now().minusHours(1));

        AnalysisTask olderCompleted = completedTask("task-ok", "BV1abc", LocalDateTime.now().minusDays(1));

        when(projectMapper.findById(11L)).thenReturn(project);
        when(taskMapper.findProjectTaskCandidates(11L, 7L, "BV1abc")).thenReturn(Arrays.asList(failedNewest, olderCompleted));
        when(commentMapper.countByTaskId("task-ok")).thenReturn(5);
        when(commentMapper.countByTaskIdAndSentiment("task-ok", "POSITIVE")).thenReturn(3);
        when(commentMapper.countByTaskIdAndSentiment("task-ok", "NEGATIVE")).thenReturn(1);

        Map<String, Object> stats = aggregationService.getProjectStatistics(11L, 7L);

        assertEquals(1, stats.get("total_tasks"));
        assertEquals(1L, stats.get("completed_tasks"));
        assertEquals(5, stats.get("total_comments"));
        assertEquals(3d / 5d, (Double) stats.get("positive_ratio"), 0.0001);
        assertEquals(1d / 5d, (Double) stats.get("negative_ratio"), 0.0001);
    }

    private AnalysisTask completedTask(String taskId, String bvid, LocalDateTime completedAt) {
        AnalysisTask task = new AnalysisTask();
        task.setTaskId(taskId);
        task.setBvid(bvid);
        task.setStatus("COMPLETED");
        task.setCreatedAt(completedAt.minusMinutes(5));
        task.setCompletedAt(completedAt);
        return task;
    }
}
