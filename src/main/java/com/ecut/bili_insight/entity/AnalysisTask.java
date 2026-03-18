package com.ecut.bili_insight.entity;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;
import java.time.LocalDateTime;

/**
 * 分析任务实体类
 */
@Data
public class AnalysisTask {
    /**
     * 任务ID
     */
    @JsonProperty("id")
    private String taskId;

    /**
     * 提交任务的用户ID
     */
    private Long userId;

    /**
     * 视频BVID
     */
    private String bvid;

    /**
     * 任务状态: PENDING/RUNNING/SUCCESS/FAILED
     */
    private String status;

    /**
     * 任务类型
     */
    private String taskType;

    /**
     * 错误信息
     */
    private String errorMessage;

    /**
     * 进度百分比 (0-100)
     */
    private Integer progress;

    /**
     * 当前步骤描述
     */
    private String currentStep;

    /**
     * 创建时间
     */
    private LocalDateTime createdAt;

    /**
     * 完成时间
     */
    private LocalDateTime completedAt;

    /**
     * 更新时间
     */
    private LocalDateTime updatedAt;
}
