package com.ecut.bili_insight.mapper;

import com.ecut.bili_insight.entity.SentimentTimeline;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

/**
 * 情绪时间轴数据访问层
 */
@Mapper
public interface SentimentTimelineMapper {

    /**
     * 插入或更新时间轴数据
     * @param timeline 时间轴实体
     * @return 受影响的行数
     */
    int insertOrUpdate(SentimentTimeline timeline);

    /**
     * 根据任务ID查询时间轴
     * @param taskId 任务ID
     * @return 时间轴实体
     */
    SentimentTimeline findByTaskId(@Param("taskId") Long taskId);

    /**
     * 根据任务ID删除时间轴
     * @param taskId 任务ID
     * @return 受影响的行数
     */
    int deleteByTaskId(@Param("taskId") Long taskId);
}
