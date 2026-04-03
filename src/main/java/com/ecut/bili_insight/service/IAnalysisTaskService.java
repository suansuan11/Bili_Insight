package com.ecut.bili_insight.service;

import com.ecut.bili_insight.entity.AnalysisTask;
import com.ecut.bili_insight.entity.VideoComment;
import com.ecut.bili_insight.entity.VideoDanmaku;
import com.ecut.bili_insight.entity.SentimentTimeline;

import java.util.List;
import java.util.Map;

/**
 * 视频分析任务服务接口
 */
public interface IAnalysisTaskService {

    /**
     * 提交视频分析任务（若已有 COMPLETED 任务则复用）
     *
     * @param bvid      视频BVID
     * @param userId    提交用户ID
     * @param sessdata  用户的B站SESSDATA（可为null，Python将使用游客模式）
     * @param biliJct   用户绑定的 bili_jct
     * @param buvid3    用户绑定的 buvid3
     * @return 任务ID
     */
    String submitAnalysisTask(String bvid, Long userId, String sessdata, String biliJct, String buvid3);

    /**
     * 强制重新分析（忽略已有 COMPLETED 任务，始终创建新任务）
     *
     * @param bvid      视频BVID
     * @param userId    所属用户ID
     * @param sessdata  用户的B站SESSDATA（可为null）
     * @param biliJct   用户绑定的 bili_jct
     * @param buvid3    用户绑定的 buvid3
     * @return 新任务ID
     */
    String forceSubmitAnalysisTask(String bvid, Long userId, String sessdata, String biliJct, String buvid3);

    /**
     * 查询任务状态
     * 
     * @param taskId 任务ID
     * @return 任务实体
     */
    AnalysisTask getTaskStatus(String taskId);

    /**
     * 根据BVID查询任务
     * 
     * @param bvid 视频BVID
     * @return 任务实体
     */
    AnalysisTask getTaskByBvid(String bvid);

    /**
     * 获取完整的分析结果（带权限验证）
     *
     * @param taskId 任务ID
     * @param userId 请求用户ID
     * @return 包含评论、弹幕、时间轴的完整数据
     */
    Map<String, Object> getAnalysisResult(String taskId, Long userId);

    /**
     * 获取完整的分析结果（无权限验证，内部使用）
     *
     * @param taskId 任务ID
     * @return 包含评论、弹幕、时间轴的完整数据
     */
    Map<String, Object> getAnalysisResult(String taskId);

    /**
     * 获取视频评论列表
     * 
     * @param taskId         任务ID
     * @param sentimentLabel 情感标签(可选)
     * @param aspect         切面(可选)
     * @return 评论列表
     */
    List<VideoComment> getComments(String taskId, String sentimentLabel, String aspect);

    /**
     * 获取视频弹幕列表
     * 
     * @param taskId         任务ID
     * @param sentimentLabel 情感标签(可选)
     * @return 弹幕列表
     */
    List<VideoDanmaku> getDanmakus(String taskId, String sentimentLabel);

    /**
     * 获取情绪时间轴数据
     * 
     * @param taskId 任务ID
     * @return 时间轴实体
     */
    SentimentTimeline getTimeline(String taskId);

    /**
     * 获取最近的任务列表（按用户过滤）
     *
     * @param limit  限制数量
     * @param userId 用户ID，null 时返回全局
     * @return 任务列表
     */
    List<AnalysisTask> getRecentTasks(int limit, Long userId);
}
