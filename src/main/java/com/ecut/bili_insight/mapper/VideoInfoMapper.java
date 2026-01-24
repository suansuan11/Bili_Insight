// com.ecut.bili_insight.mapper.VideoInfoMapper.java

package com.ecut.bili_insight.mapper;

import com.ecut.bili_insight.entity.VideoInfo;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import java.util.List;

@Mapper
public interface VideoInfoMapper {
    /**
     * 批量插入或更新视频信息到主表
     * @param videoList 视频信息列表
     * @return 受影响的行数
     */
    int batchInsertOrUpdate(@Param("videoList") List<VideoInfo> videoList);

    /**
     * 查询所有视频信息
     * @return 视频信息列表
     */
    List<VideoInfo> findAll();
}