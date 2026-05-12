package com.ecut.bili_insight.service;

import com.ecut.bili_insight.entity.UserSettings;
import com.ecut.bili_insight.mapper.UserSettingsMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

@Service
public class UserSettingsService {

    private static final String DEFAULT_LANGUAGE = "zh-CN";
    private static final String DEFAULT_DATE_FORMAT = "1";
    private static final String DEFAULT_ENGINE = "transformer";
    private static final String DEFAULT_RETENTION = "90";

    @Autowired
    private UserSettingsMapper mapper;

    public UserSettings getOrDefault(Long userId) {
        UserSettings existing = mapper.findByUserId(userId);
        if (existing != null) {
            return normalize(existing, userId);
        }
        return defaultSettings(userId);
    }

    public UserSettings save(Long userId, UserSettings input) {
        UserSettings normalized = normalize(input == null ? new UserSettings() : input, userId);
        mapper.upsert(normalized);
        return getOrDefault(userId);
    }

    public String getAnalysisEngine(Long userId) {
        return getOrDefault(userId).getAnalysisEngine();
    }

    private UserSettings defaultSettings(Long userId) {
        UserSettings settings = new UserSettings();
        settings.setUserId(userId);
        settings.setLanguage(DEFAULT_LANGUAGE);
        settings.setDateFormat(DEFAULT_DATE_FORMAT);
        settings.setDesktopNotify(Boolean.FALSE);
        settings.setSoundNotify(Boolean.FALSE);
        settings.setWeeklyReport(Boolean.FALSE);
        settings.setAnalysisEngine(DEFAULT_ENGINE);
        settings.setDataRetention(DEFAULT_RETENTION);
        return settings;
    }

    private UserSettings normalize(UserSettings settings, Long userId) {
        UserSettings defaults = defaultSettings(userId);
        settings.setUserId(userId);
        settings.setLanguage(validLanguage(settings.getLanguage()) ? settings.getLanguage() : defaults.getLanguage());
        settings.setDateFormat(validDateFormat(settings.getDateFormat()) ? settings.getDateFormat() : defaults.getDateFormat());
        settings.setDesktopNotify(Boolean.TRUE.equals(settings.getDesktopNotify()));
        settings.setSoundNotify(Boolean.TRUE.equals(settings.getSoundNotify()));
        settings.setWeeklyReport(Boolean.TRUE.equals(settings.getWeeklyReport()));
        settings.setAnalysisEngine(validEngine(settings.getAnalysisEngine()) ? settings.getAnalysisEngine() : defaults.getAnalysisEngine());
        settings.setDataRetention(validRetention(settings.getDataRetention()) ? settings.getDataRetention() : defaults.getDataRetention());
        return settings;
    }

    private boolean validLanguage(String value) {
        return "zh-CN".equals(value) || "en-US".equals(value);
    }

    private boolean validDateFormat(String value) {
        return "1".equals(value) || "2".equals(value) || "3".equals(value);
    }

    private boolean validEngine(String value) {
        return "transformer".equals(value) || "snownlp".equals(value);
    }

    private boolean validRetention(String value) {
        return "30".equals(value) || "90".equals(value) || "permanent".equals(value);
    }
}
