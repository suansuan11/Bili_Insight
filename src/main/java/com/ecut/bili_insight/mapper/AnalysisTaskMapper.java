package com.ecut.bili_insight.mapper;

import com.ecut.bili_insight.entity.AnalysisTask;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

/**
 * 分析任务数据访问层
 */
@Mapper
public interface AnalysisTaskMapper {

    /**
     * 插入新任务
     * 
     * @param task 任务实体
     * @return 受影响的行数
     */
    int insert(AnalysisTask task);

    /**
     * 根据ID查询任务
     * 
     * @param taskId 任务ID
     * @return 任务实体
     */
    AnalysisTask findById(@Param("taskId") String taskId);

    /**
     * 根据BVID查询任务
     * 
     * @param bvid 视频BVID
     * @return 任务实体
     */
    AnalysisTask findByBvid(@Param("bvid") String bvid);

    AnalysisTask findLatestByProjectIdAndBvid(@Param("projectId") Long projectId, @Param("bvid") String bvid);

    java.util.List<AnalysisTask> findProjectTaskCandidates(@Param("projectId") Long projectId,
                                                           @Param("userId") Long userId,
                                                           @Param("bvid") String bvid);

    /**
     * 更新任务状态
     * 
     * @param taskId       任务ID
     * @param status       新状态
     * @param errorMessage 错误信息(可选)
     * @return 受影响的行数
     */
    int updateStatus(@Param("taskId") String taskId,
            @Param("status") String status,
            @Param("errorMessage") String errorMessage);

    /**
     * 更新任务进度
     * 
     * @param taskId      任务ID
     * @param progress    进度百分比(0-100)
     * @param currentStep 当前步骤
     * @return 受影响的行数
     */
    int updateProgress(@Param("taskId") String taskId,
            @Param("progress") Integer progress,
            @Param("currentStep") String currentStep);

    /**
     * 查询最近的任务（按用户过滤）
     *
     * @param userId 用户ID，null 时返回全局
     * @param limit  限制数量
     * @return 任务列表
     */
    java.util.List<AnalysisTask> findRecent(@Param("userId") Long userId, @Param("limit") int limit);

    /**
     * 根据项目ID查询任务
     *
     * @param projectId 项目ID
     * @return 任务列表
     */
    java.util.List<AnalysisTask> findByProjectId(@Param("projectId") Long projectId);

    /**
     * 标记超时任务为失败
     *
     * @param timeoutThreshold 超时时间阈值
     * @return 受影响的行数
     */
    int markTimeoutTasks(@Param("timeoutThreshold") java.time.LocalDateTime timeoutThreshold);
}
