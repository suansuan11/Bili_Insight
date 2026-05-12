package com.ecut.bili_insight.entity;

import lombok.Data;

import java.time.LocalDateTime;

@Data
public class UserSettings {
    private Long id;
    private Long userId;
    private String language;
    private String dateFormat;
    private Boolean desktopNotify;
    private Boolean soundNotify;
    private Boolean weeklyReport;
    private String analysisEngine;
    private String dataRetention;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
