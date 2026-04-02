package com.ecut.bili_insight.entity;

import lombok.Data;
import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * 视频弹幕实体类
 */
@Data
public class VideoDanmaku {
    /**
     * 弹幕ID
     */
    private Long danmakuId;

    /**
     * 视频BVID
     */
    private String bvid;

    /**
     * 任务ID
     */
    private String taskId;

    /**
     * 弹幕内容
     */
    private String content;

    /**
     * 弹幕时间点(秒)
     */
    private BigDecimal dmTime;

    /**
     * 标准化后的文本
     */
    private String normalizedContent;

    /**
     * 文本类型: comment / danmaku
     */
    private String textType;

    /**
     * 情感分数 [-1.0000, 1.0000]
     */
    private BigDecimal sentimentScore;

    /**
     * 情感标签: POSITIVE/NEUTRAL/NEGATIVE
     */
    private String sentimentLabel;

    /**
     * 情感置信度 [0.0000, 1.0000]
     */
    private BigDecimal sentimentConfidence;

    /**
     * 情感强度: WEAK/MEDIUM/STRONG
     */
    private String sentimentIntensity;

    /**
     * 分析来源: transformer_danmaku_v1 / fallback_rule_v1
     */
    private String sentimentSource;

    /**
     * 模型版本
     */
    private String sentimentVersion;

    /**
     * 情绪标签JSON: ["sarcasm","mocking"]
     */
    private String emotionTagsJson;

    /**
     * 爬取时间
     */
    private LocalDateTime scrapedAt;
}
