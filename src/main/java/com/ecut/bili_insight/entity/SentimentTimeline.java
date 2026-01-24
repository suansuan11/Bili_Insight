package com.ecut.bili_insight.entity;

import lombok.Data;
import java.math.BigDecimal;

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
    private Long taskId;

    /**
     * 时间点(秒)
     */
    private BigDecimal timePoint;

    /**
     * 平均情感值 (0-1)
     */
    private BigDecimal avgSentiment;

    /**
     * 弹幕数量
     */
    private Integer danmakuCount;
}
