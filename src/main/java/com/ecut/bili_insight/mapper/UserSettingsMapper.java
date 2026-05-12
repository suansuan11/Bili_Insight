package com.ecut.bili_insight.mapper;

import com.ecut.bili_insight.entity.UserSettings;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.time.LocalDateTime;
import java.util.List;

@Mapper
public interface UserSettingsMapper {
    UserSettings findByUserId(@Param("userId") Long userId);

    int upsert(UserSettings settings);

    List<UserSettings> findUsersWithRetention();

    List<UserSettings> findWeeklyReportUsers();

    int deleteTerminalTasksBefore(@Param("userId") Long userId, @Param("cutoff") LocalDateTime cutoff);
}
