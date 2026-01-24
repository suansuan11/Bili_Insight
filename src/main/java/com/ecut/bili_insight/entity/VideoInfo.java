// src/main/java/com/ecut/bili_insight/entity/VideoInfo.java

package com.ecut.bili_insight.entity;

import com.fasterxml.jackson.annotation.JsonAlias;
import com.fasterxml.jackson.annotation.JsonFormat;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;
import java.util.Date;
import java.time.LocalDateTime;

/**
 * 通用视频信息实体类
 * 使用Jackson注解兼容多种JSON数据源
 */
@Data
@JsonIgnoreProperties(ignoreUnknown = true)
public class VideoInfo {

    @JsonProperty("bvid")
    private String bvid;

    @JsonProperty("aid")
    private long aid;

    @JsonProperty("title")
    private String title;

    @JsonProperty("author")
    @JsonAlias("owner.name")
    private String author;

    @JsonProperty("author_mid")
    @JsonAlias("owner.mid")
    private long authorMid;

    // ===== 【核心修正】 =====
    // 为 @JsonFormat 注解增加 shape 和 timezone 参数，使其更加明确和健壮
    @JsonProperty("publish_date")
    @JsonFormat(shape = JsonFormat.Shape.STRING, pattern = "yyyy-MM-dd HH:mm:ss", timezone = "GMT+8")
    private Date publishDate;

    // 当JSON中只有pubdate时，此setter会被调用以转换时间戳
    @JsonProperty("pubdate")
    private void setPubdate(long pubdate) {
        if (this.publishDate == null) {
            this.publishDate = new Date(pubdate * 1000L);
        }
    }

    @JsonProperty("duration")
    private int duration;

    @JsonProperty("view_count")
    private int viewCount;

    @JsonProperty("like_count")
    private int likeCount;

    @JsonProperty("coin_count")
    private int coinCount;

    @JsonProperty("favorite_count")
    private int favoriteCount;

    @JsonProperty("share_count")
    private int shareCount;

    @JsonProperty("danmaku_count")
    private int danmakuCount;

    @JsonProperty("description")
    private String description;

    @JsonProperty("cover_url")
    private String coverUrl;

    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    private LocalDateTime scrapedAt;
}
