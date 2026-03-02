package com.ecut.bili_insight.service;

import com.ecut.bili_insight.entity.VideoInfo;

import java.util.List;

public interface IPopularVideosService {
    /**
     * 执行一次热门视频数据的刷新和存储任务
     */
    void refreshAndSavePopularVideos() throws Exception;

    /**
     * 获取当前存储在数据库中的热门视频列表
     * @return 热门视频列表
     */
    List<VideoInfo> getCurrentPopularVideos();

    /**
     * 触发Python服务后台抓取热门视频
     */
    void triggerPopularFetch();
}
