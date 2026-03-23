package com.ecut.bili_insight.service;

import com.ecut.bili_insight.entity.AnalysisTask;
import com.ecut.bili_insight.entity.Project;
import com.ecut.bili_insight.mapper.AnalysisTaskMapper;
import com.ecut.bili_insight.mapper.ProjectMapper;
import com.ecut.bili_insight.mapper.VideoCommentMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
public class ProjectAggregationService {

    @Autowired
    private ProjectMapper projectMapper;

    @Autowired
    private AnalysisTaskMapper taskMapper;

    @Autowired
    private VideoCommentMapper commentMapper;

    public Map<String, Object> getProjectStatistics(Long projectId, Long userId) {
        Project project = projectMapper.findById(projectId);
        if (project == null || !project.getUserId().equals(userId)) {
            throw new RuntimeException("项目不存在或无权访问");
        }

        Map<String, Object> stats = new HashMap<>();
        stats.put("project", project);

        // 统计任务数量
        List<AnalysisTask> tasks = taskMapper.findByProjectId(projectId);
        stats.put("total_tasks", tasks.size());
        stats.put("completed_tasks", tasks.stream().filter(t -> "COMPLETED".equals(t.getStatus())).count());

        // 统计评论情感分布
        int totalComments = 0;
        int positiveComments = 0;
        int negativeComments = 0;

        for (AnalysisTask task : tasks) {
            if ("COMPLETED".equals(task.getStatus())) {
                int count = commentMapper.countByTaskId(task.getTaskId());
                totalComments += count;
                positiveComments += commentMapper.countByTaskIdAndSentiment(task.getTaskId(), "POSITIVE");
                negativeComments += commentMapper.countByTaskIdAndSentiment(task.getTaskId(), "NEGATIVE");
            }
        }

        stats.put("total_comments", totalComments);
        stats.put("positive_ratio", totalComments > 0 ? (double) positiveComments / totalComments : 0);
        stats.put("negative_ratio", totalComments > 0 ? (double) negativeComments / totalComments : 0);

        return stats;
    }
}
