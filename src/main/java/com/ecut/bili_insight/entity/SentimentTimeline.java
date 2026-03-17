package com.ecut.bili_insight.entity;

import lombok.Data;

/**
 * 情绪时间轴实体类
 */
@Data
public class SentimentTimeline {
    /**
     * 时间轴ID
     */
    private Long timelineId;

    /**
     * 视频BVID
     */
    private String bvid;

    /**
     * 任务ID
     */
    private String taskId;

    /**
     * 情绪时间轴JSON数据
     */
    private String timelineJson;

    /**
     * 切面情感分析JSON数据
     */
    private String aspectSentimentJson;
}
