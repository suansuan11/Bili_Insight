package com.ecut.bili_insight.entity;

import lombok.Data;
import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * 视频评论实体类
 */
@Data
public class VideoComment {
    /**
     * 评论ID
     */
    private Long commentId;

    /**
     * 视频BVID
     */
    private String bvid;

    /**
     * 任务ID
     */
    private String taskId;

    /**
     * 用户昵称
     */
    private String username;

    /**
     * 性别
     */
    private String gender;

    /**
     * 评论内容
     */
    private String content;

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
     * 分析来源: transformer_comment_v1 / fallback_rule_v1
     */
    private String sentimentSource;

    /**
     * 模型版本
     */
    private String sentimentVersion;

    /**
     * 情绪标签JSON: ["complaint","sarcasm"]
     */
    private String emotionTagsJson;

    /**
     * 切面情感详情JSON
     */
    private String aspectDetailsJson;

    /**
     * 点赞数
     */
    private Integer likeCount;

    /**
     * 回复数
     */
    private Integer replyCount;

    /**
     * ABSA切面标签
     */
    private String aspect;

    /**
     * 发布时间
     */
    private LocalDateTime publishTime;

    /**
     * 爬取时间
     */
    private LocalDateTime scrapedAt;
}
