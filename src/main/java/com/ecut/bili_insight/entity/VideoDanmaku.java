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
    private Long taskId;

    /**
     * 弹幕内容
     */
    private String content;

    /**
     * 弹幕时间点(秒)
     */
    private BigDecimal dmTime;

    /**
     * 情感分数 (0-1)
     */
    private BigDecimal sentimentScore;

    /**
     * 情感标签: POSITIVE/NEUTRAL/NEGATIVE
     */
    private String sentimentLabel;

    /**
     * 爬取时间
     */
    private LocalDateTime scrapedAt;
}
