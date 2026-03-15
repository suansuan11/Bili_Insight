package com.ecut.bili_insight.mapper;

import org.apache.ibatis.annotations.Mapper;
import java.util.List;
import java.util.Map;

@Mapper
public interface DashboardMapper {
    Integer getTotalVideos();
    Integer getTotalComments();
    Double getAvgSentiment();
    Integer getTotalTasks();
    Integer getCompletedTasks();
    
    List<Map<String, Object>> getSentimentDistribution();
    List<Map<String, Object>> getTopAspects();
    List<Map<String, Object>> getTaskTrend();
}
