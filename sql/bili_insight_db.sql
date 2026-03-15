-- Bili-Insight Database Schema
-- Last Updated: 2026-03-01

CREATE DATABASE IF NOT EXISTS bili_insight_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE bili_insight_db;

-- ----------------------------
-- Table structure for users (New)
-- ----------------------------
DROP TABLE IF EXISTS `user`;
CREATE TABLE `user` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `username` varchar(50) NOT NULL,
  `password_hash` varchar(100) NOT NULL,
  `email` varchar(100) DEFAULT NULL,
  `role` varchar(20) NOT NULL DEFAULT 'BRAND' COMMENT 'CREATOR (UP主) / BRAND (品牌方) / ADMIN',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for projects (New, for brand monitoring)
-- ----------------------------
DROP TABLE IF EXISTS `project`;
CREATE TABLE `project` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `user_id` bigint(20) NOT NULL,
  `name` varchar(100) NOT NULL,
  `description` varchar(500) DEFAULT NULL,
  `keywords` varchar(500) DEFAULT NULL COMMENT 'JSON array of tracked keywords, e.g. ["小米14", "续航"]',
  `target_bvids` text DEFAULT NULL COMMENT 'JSON array of target BV numbers',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_user_id` (`user_id`),
  CONSTRAINT `fk_project_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for analysis_task
-- ----------------------------
DROP TABLE IF EXISTS `analysis_task`;
CREATE TABLE `analysis_task` (
  `task_id` varchar(50) NOT NULL COMMENT 'UUID task identifier',
  `bvid` varchar(50) NOT NULL COMMENT 'Bilibili Video ID',
  `user_id` bigint(20) DEFAULT NULL COMMENT 'The user who created this task',
  `project_id` bigint(20) DEFAULT NULL COMMENT 'Associated project, if any',
  `status` varchar(20) NOT NULL DEFAULT 'PENDING' COMMENT 'PENDING, RUNNING, COMPLETED, FAILED',
  `task_type` varchar(20) NOT NULL DEFAULT 'FULL' COMMENT 'FULL, COMMENTS_ONLY, DANMAKU_ONLY',
  `progress` int(11) NOT NULL DEFAULT '0' COMMENT '0-100',
  `current_step` varchar(100) DEFAULT NULL COMMENT 'Description of current processing step',
  `error_message` text,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `completed_at` datetime DEFAULT NULL,
  PRIMARY KEY (`task_id`),
  KEY `idx_bvid` (`bvid`),
  KEY `idx_status` (`status`),
  KEY `idx_user_id` (`user_id`),
  CONSTRAINT `fk_task_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_task_project` FOREIGN KEY (`project_id`) REFERENCES `project` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for video_info
-- ----------------------------
DROP TABLE IF EXISTS `video_info`;
CREATE TABLE `video_info` (
  `bvid` varchar(50) NOT NULL,
  `aid` bigint(20) NOT NULL,
  `title` varchar(255) NOT NULL,
  `author` varchar(100) NOT NULL,
  `publish_date` datetime NOT NULL,
  `duration` int(11) DEFAULT NULL,
  `view_count` int(11) DEFAULT '0',
  `like_count` int(11) DEFAULT '0',
  `coin_count` int(11) DEFAULT '0',
  `fav_count` int(11) DEFAULT '0',
  `share_count` int(11) DEFAULT '0',
  `danmaku_count` int(11) DEFAULT '0',
  `reply_count` int(11) DEFAULT '0',
  `cover_url` varchar(500) DEFAULT NULL,
  `scraped_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `last_analyzed_at` datetime DEFAULT NULL,
  `analysis_count` int(11) DEFAULT '0',
  PRIMARY KEY (`bvid`),
  UNIQUE KEY `uk_aid` (`aid`),
  KEY `idx_author` (`author`),
  KEY `idx_publish_date` (`publish_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for video_comment
-- ----------------------------
DROP TABLE IF EXISTS `video_comment`;
CREATE TABLE `video_comment` (
  `comment_id` bigint(20) NOT NULL,
  `bvid` varchar(50) NOT NULL,
  `task_id` varchar(50) NOT NULL,
  `username` varchar(100) NOT NULL,
  `gender` varchar(10) DEFAULT '未知',
  `content` text NOT NULL,
  `sentiment_score` decimal(5,4) DEFAULT NULL COMMENT '0.0000 to 1.0000',
  `sentiment_label` varchar(10) DEFAULT NULL COMMENT 'POSITIVE, NEUTRAL, NEGATIVE',
  `like_count` int(11) DEFAULT '0',
  `reply_count` int(11) DEFAULT '0',
  `aspect` varchar(50) DEFAULT NULL COMMENT 'Aspect/Dimension (e.g., 外观, 性能, 价格)',
  `publish_time` datetime DEFAULT NULL,
  `scraped_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`comment_id`),
  KEY `idx_bvid` (`bvid`),
  KEY `idx_task_id` (`task_id`),
  KEY `idx_sentiment` (`sentiment_label`),
  KEY `idx_aspect` (`aspect`),
  CONSTRAINT `fk_comment_task` FOREIGN KEY (`task_id`) REFERENCES `analysis_task` (`task_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for video_danmaku
-- ----------------------------
DROP TABLE IF EXISTS `video_danmaku`;
CREATE TABLE `video_danmaku` (
  `danmaku_id` bigint(20) NOT NULL,
  `bvid` varchar(50) NOT NULL,
  `task_id` varchar(50) NOT NULL,
  `content` text NOT NULL,
  `dm_time` int(11) NOT NULL COMMENT 'Time in video (seconds)',
  `appear_time` int(11) DEFAULT '0' COMMENT 'Same as dm_time, duplicate for compatibility',
  `send_time` datetime DEFAULT NULL COMMENT 'When the danmaku was actually sent',
  `sentiment_score` decimal(5,4) DEFAULT NULL COMMENT '0.0000 to 1.0000',
  `sentiment_label` varchar(10) DEFAULT NULL COMMENT 'POSITIVE, NEUTRAL, NEGATIVE',
  `scraped_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`danmaku_id`),
  KEY `idx_bvid` (`bvid`),
  KEY `idx_task_id` (`task_id`),
  KEY `idx_dm_time` (`dm_time`),
  CONSTRAINT `fk_danmaku_task` FOREIGN KEY (`task_id`) REFERENCES `analysis_task` (`task_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Trigger to auto-sync appear_time with dm_time if not provided
DELIMITER //
DROP TRIGGER IF EXISTS `trg_danmaku_before_insert`//
CREATE TRIGGER `trg_danmaku_before_insert` BEFORE INSERT ON `video_danmaku`
FOR EACH ROW
BEGIN
    IF NEW.appear_time IS NULL OR NEW.appear_time = 0 THEN
        SET NEW.appear_time = NEW.dm_time;
    END IF;
END//

DROP TRIGGER IF EXISTS `trg_danmaku_before_update`//
CREATE TRIGGER `trg_danmaku_before_update` BEFORE UPDATE ON `video_danmaku`
FOR EACH ROW
BEGIN
    IF NEW.appear_time IS NULL OR NEW.appear_time = 0 THEN
        SET NEW.appear_time = NEW.dm_time;
    END IF;
END//
DELIMITER ;

-- ----------------------------
-- Table structure for sentiment_timeline
-- ----------------------------
DROP TABLE IF EXISTS `sentiment_timeline`;
CREATE TABLE `sentiment_timeline` (
  `timeline_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `bvid` varchar(50) NOT NULL,
  `task_id` varchar(50) NOT NULL,
  `timeline_json` json NOT NULL COMMENT 'ECharts compatible JSON array of [timeIndex, sentimentScore]',
  `aspect_sentiment_json` json DEFAULT NULL COMMENT 'JSON object of aspect -> average sentiment',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`timeline_id`),
  KEY `idx_bvid` (`bvid`),
  UNIQUE KEY `uk_task_id` (`task_id`),
  CONSTRAINT `fk_timeline_task` FOREIGN KEY (`task_id`) REFERENCES `analysis_task` (`task_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for popular_videos
-- ----------------------------
DROP TABLE IF EXISTS `popular_videos`;
CREATE TABLE `popular_videos` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `bvid` varchar(50) NOT NULL,
  `aid` bigint(20) NOT NULL,
  `title` varchar(255) NOT NULL,
  `author` varchar(100) NOT NULL,
  `tname` varchar(50) DEFAULT NULL COMMENT 'Category name',
  `cover_url` varchar(500) DEFAULT NULL,
  `view_count` int(11) DEFAULT '0',
  `danmaku_count` int(11) DEFAULT '0',
  `reply_count` int(11) DEFAULT '0',
  `comment_count` int(11) DEFAULT '0' COMMENT 'Fixed: was missing, causing Python driver errors',
  `favorite_count` int(11) DEFAULT '0',
  `coin_count` int(11) DEFAULT '0',
  `share_count` int(11) DEFAULT '0',
  `like_count` int(11) DEFAULT '0',
  `score` int(11) DEFAULT '0' COMMENT 'Hot score',
  `rcmd_reason` varchar(100) DEFAULT NULL,
  `scraped_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_bvid` (`bvid`),
  KEY `idx_tname` (`tname`),
  KEY `idx_score` (`score`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
