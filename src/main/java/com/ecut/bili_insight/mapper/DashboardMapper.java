package com.ecut.bili_insight.mapper;

import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import java.util.List;
import java.util.Map;

@Mapper
public interface DashboardMapper {
    Integer getTotalVideos(@Param("userId") Long userId);
    Integer getTotalComments(@Param("userId") Long userId);
    Double getAvgSentiment(@Param("userId") Long userId);
    Integer getTotalTasks(@Param("userId") Long userId);
    Integer getCompletedTasks(@Param("userId") Long userId);

    List<Map<String, Object>> getSentimentDistribution(@Param("userId") Long userId);
    List<Map<String, Object>> getTopAspects(@Param("userId") Long userId);
    List<Map<String, Object>> getTaskTrend(@Param("userId") Long userId);
}
