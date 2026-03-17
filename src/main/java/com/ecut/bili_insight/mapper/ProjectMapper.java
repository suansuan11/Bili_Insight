package com.ecut.bili_insight.mapper;

import com.ecut.bili_insight.entity.Project;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

@Mapper
public interface ProjectMapper {
    List<Project> findByUserId(@Param("userId") Long userId);
    Project findById(@Param("id") Long id);
    int insert(Project project);
    int update(Project project);
    int deleteById(@Param("id") Long id);
}
