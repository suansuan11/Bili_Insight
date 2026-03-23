package com.ecut.bili_insight.mapper;

import com.ecut.bili_insight.entity.VideoComment;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import java.util.List;

/**
 * 视频评论数据访问层
 */
@Mapper
public interface VideoCommentMapper {

    /**
     * 批量插入评论
     * @param comments 评论列表
     * @return 受影响的行数
     */
    int batchInsert(@Param("comments") List<VideoComment> comments);

    /**
     * 根据任务ID查询评论
     * @param taskId 任务ID
     * @return 评论列表
     */
    List<VideoComment> findByTaskId(@Param("taskId") String taskId);

    /**
     * 根据任务ID和情感标签筛选评论
     * @param taskId 任务ID
     * @param sentimentLabel 情感标签 (POSITIVE/NEGATIVE/NEUTRAL)
     * @return 评论列表
     */
    List<VideoComment> findByTaskIdAndSentiment(@Param("taskId") String taskId,
                                                @Param("sentimentLabel") String sentimentLabel);

    /**
     * 根据任务ID和切面筛选评论
     * @param taskId 任务ID
     * @param aspect 切面名称
     * @return 评论列表
     */
    List<VideoComment> findByTaskIdAndAspect(@Param("taskId") String taskId,
                                            @Param("aspect") String aspect);

    /**
     * 统计任务的评论总数
     * @param taskId 任务ID
     * @return 评论总数
     */
    int countByTaskId(@Param("taskId") String taskId);

    /**
     * 统计任务指定情感的评论数
     * @param taskId 任务ID
     * @param sentimentLabel 情感标签
     * @return 评论数
     */
    int countByTaskIdAndSentiment(@Param("taskId") String taskId, @Param("sentimentLabel") String sentimentLabel);
}
