package com.ecut.bili_insight.mapper;

import com.ecut.bili_insight.entity.VideoDanmaku;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import java.util.List;

/**
 * 视频弹幕数据访问层
 */
@Mapper
public interface VideoDanmakuMapper {

    /**
     * 批量插入弹幕
     * @param danmakus 弹幕列表
     * @return 受影响的行数
     */
    int batchInsert(@Param("danmakus") List<VideoDanmaku> danmakus);

    /**
     * 根据任务ID查询弹幕
     * @param taskId 任务ID
     * @return 弹幕列表
     */
    List<VideoDanmaku> findByTaskId(@Param("taskId") String taskId);

    /**
     * 根据任务ID和情感标签筛选弹幕
     * @param taskId 任务ID
     * @param sentimentLabel 情感标签 (POSITIVE/NEGATIVE/NEUTRAL)
     * @return 弹幕列表
     */
    List<VideoDanmaku> findByTaskIdAndSentiment(@Param("taskId") String taskId,
                                               @Param("sentimentLabel") String sentimentLabel);

    /**
     * 统计任务的弹幕总数
     * @param taskId 任务ID
     * @return 弹幕总数
     */
    int countByTaskId(@Param("taskId") String taskId);
}
