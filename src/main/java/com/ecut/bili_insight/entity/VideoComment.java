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
    private Long taskId;

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
     * 情感分数 (0-1)
     */
    private BigDecimal sentimentScore;

    /**
     * 情感标签: POSITIVE/NEUTRAL/NEGATIVE
     */
    private String sentimentLabel;

    /**
     * 点赞数
     */
    private Integer likeCount;

    /**
     * 回复数
     */
    private Integer replyCount;

    /**
     * 爬取时间
     */
    private LocalDateTime scrapedAt;
}
