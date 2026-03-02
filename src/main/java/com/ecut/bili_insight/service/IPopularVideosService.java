package com.ecut.bili_insight.service;

import com.ecut.bili_insight.entity.VideoInfo;

import java.util.List;
import java.util.Map;

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

    /**
     * 查询热门抓取任务状态
     * @return Python服务返回的状态信息
     */
    Map<String, Object> getPopularFetchStatus();
}
