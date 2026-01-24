package com.ecut.bili_insight.mapper;

import com.ecut.bili_insight.entity.VideoInfo;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

@Mapper
public interface PopularVideoMapper {
    /**
     * 清空热门视频表
     */
    void truncateTable();

    /**
     * 批量插入新的热门视频数据
     * @param videoList 视频信息列表
     */
    void batchInsert(@Param("videoList") List<VideoInfo> videoList);

    /**
     * 查询所有热门视频，按热度（观看数）降序排列
     * @return 热门视频列表
     */
    List<VideoInfo> findAll();
}
