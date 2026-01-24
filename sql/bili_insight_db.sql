/*
 Navicat Premium Dump SQL

 Source Server         : local_database
 Source Server Type    : MySQL
 Source Server Version : 90100 (9.1.0)
 Source Host           : localhost:3306
 Source Schema         : bili_insight_db

 Target Server Type    : MySQL
 Target Server Version : 90100 (9.1.0)
 File Encoding         : 65001

 Date: 24/12/2025 18:12:45
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for analysis_task
-- ----------------------------
DROP TABLE IF EXISTS `analysis_task`;
CREATE TABLE `analysis_task`  (
  `task_id` bigint NOT NULL AUTO_INCREMENT COMMENT '任务ID',
  `bvid` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '视频BVID',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'PENDING' COMMENT '任务状态: PENDING/RUNNING/COMPLETED/FAILED',
  `task_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'VIDEO_REVIEW' COMMENT '任务类型',
  `progress` int NULL DEFAULT 0 COMMENT '进度百分比 0-100',
  `current_step` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '当前步骤描述',
  `error_message` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '错误信息',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `started_at` timestamp NULL DEFAULT NULL COMMENT '开始时间',
  `completed_at` timestamp NULL DEFAULT NULL COMMENT '完成时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`task_id`) USING BTREE,
  INDEX `idx_bvid`(`bvid` ASC) USING BTREE,
  INDEX `idx_status`(`status` ASC) USING BTREE,
  INDEX `idx_created`(`created_at` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 2 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '分析任务表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for popular_videos
-- ----------------------------
DROP TABLE IF EXISTS `popular_videos`;
CREATE TABLE `popular_videos`  (
  `bvid` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT 'B站视频BVID',
  `aid` bigint NOT NULL COMMENT 'B站视频AID',
  `title` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `author` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `author_mid` bigint NULL DEFAULT NULL,
  `publish_date` datetime NULL DEFAULT NULL,
  `duration` int NULL DEFAULT NULL,
  `view_count` int NULL DEFAULT NULL,
  `like_count` int NULL DEFAULT NULL,
  `coin_count` int NULL DEFAULT NULL,
  `favorite_count` int NULL DEFAULT NULL,
  `share_count` int NULL DEFAULT NULL,
  `danmaku_count` int NULL DEFAULT NULL,
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL,
  `cover_url` varchar(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `scraped_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '数据抓取时间',
  PRIMARY KEY (`bvid`) USING BTREE,
  UNIQUE INDEX `uk_aid`(`aid` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '热门视频快照表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for sentiment_timeline
-- ----------------------------
DROP TABLE IF EXISTS `sentiment_timeline`;
CREATE TABLE `sentiment_timeline`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `task_id` bigint NOT NULL COMMENT '任务ID',
  `timeline_json` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '情绪时间轴JSON数据 (格式: [{time:10,score:0.7},{time:20,score:0.8}])',
  `aspect_sentiment_json` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '切面情感分析JSON数据 (格式: {\"外观\":0.85,\"性能\":0.72})',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_task`(`task_id` ASC) USING BTREE,
  INDEX `idx_task_id`(`task_id` ASC) USING BTREE,
  CONSTRAINT `sentiment_timeline_ibfk_1` FOREIGN KEY (`task_id`) REFERENCES `analysis_task` (`task_id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 2 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '情绪时间轴表(JSON格式)' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for video_comment
-- ----------------------------
DROP TABLE IF EXISTS `video_comment`;
CREATE TABLE `video_comment`  (
  `comment_id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID(映射为Java的id字段)',
  `task_id` bigint NOT NULL COMMENT '任务ID',
  `bvid` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '视频BVID',
  `bilibili_comment_id` bigint NULL DEFAULT NULL COMMENT 'B站评论ID',
  `username` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '用户昵称(旧字段保留)',
  `author` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '评论作者(与username同义)',
  `author_mid` bigint NULL DEFAULT NULL COMMENT '作者UID(B站用户ID)',
  `gender` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '性别',
  `content` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '评论内容',
  `post_time` timestamp NULL DEFAULT NULL COMMENT '评论发布时间',
  `sentiment_score` decimal(5, 4) NULL DEFAULT NULL COMMENT '情感分数 0-1',
  `sentiment_label` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '情感标签: POSITIVE/NEUTRAL/NEGATIVE',
  `aspect` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT 'ABSA切面标签(如:外观/性能/价格/续航)',
  `like_count` int NULL DEFAULT 0 COMMENT '点赞数',
  `reply_count` int NULL DEFAULT 0 COMMENT '回复数',
  `scraped_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '爬取时间',
  PRIMARY KEY (`comment_id`) USING BTREE,
  INDEX `idx_bvid`(`bvid` ASC) USING BTREE,
  INDEX `idx_task`(`task_id` ASC) USING BTREE,
  INDEX `idx_sentiment`(`sentiment_score` ASC) USING BTREE,
  INDEX `idx_sentiment_label`(`sentiment_label` ASC) USING BTREE,
  INDEX `idx_aspect`(`aspect` ASC) USING BTREE,
  INDEX `idx_author_mid`(`author_mid` ASC) USING BTREE,
  INDEX `idx_bvid_sentiment`(`bvid` ASC, `sentiment_label` ASC, `sentiment_score` ASC) USING BTREE,
  CONSTRAINT `video_comment_ibfk_1` FOREIGN KEY (`task_id`) REFERENCES `analysis_task` (`task_id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 501 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '视频评论表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for video_danmaku
-- ----------------------------
DROP TABLE IF EXISTS `video_danmaku`;
CREATE TABLE `video_danmaku`  (
  `danmaku_id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID(映射为Java的id字段)',
  `task_id` bigint NOT NULL COMMENT '任务ID',
  `bvid` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '视频BVID',
  `content` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '弹幕内容',
  `dm_time` decimal(10, 3) NOT NULL COMMENT '弹幕时间点(秒)',
  `appear_time` decimal(10, 3) NOT NULL COMMENT '出现时间(秒,与dm_time同义)',
  `sentiment_score` decimal(5, 4) NULL DEFAULT NULL COMMENT '情感分数 0-1',
  `sentiment_label` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '情感标签: POSITIVE/NEUTRAL/NEGATIVE',
  `scraped_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '爬取时间',
  PRIMARY KEY (`danmaku_id`) USING BTREE,
  INDEX `idx_bvid`(`bvid` ASC) USING BTREE,
  INDEX `idx_task`(`task_id` ASC) USING BTREE,
  INDEX `idx_time`(`dm_time` ASC) USING BTREE,
  INDEX `idx_appear_time`(`appear_time` ASC) USING BTREE,
  INDEX `idx_sentiment_label`(`sentiment_label` ASC) USING BTREE,
  INDEX `idx_bvid_time`(`bvid` ASC, `dm_time` ASC) USING BTREE,
  CONSTRAINT `video_danmaku_ibfk_1` FOREIGN KEY (`task_id`) REFERENCES `analysis_task` (`task_id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 3389 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '视频弹幕表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for video_info
-- ----------------------------
DROP TABLE IF EXISTS `video_info`;
CREATE TABLE `video_info`  (
  `bvid` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT 'B站视频BVID',
  `aid` bigint NOT NULL COMMENT 'B站视频AID',
  `title` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '视频标题',
  `author` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '作者昵称',
  `author_mid` bigint NULL DEFAULT NULL COMMENT '作者MID',
  `publish_date` datetime NULL DEFAULT NULL COMMENT '发布日期',
  `duration` int NULL DEFAULT NULL COMMENT '视频时长（秒）',
  `view_count` int NULL DEFAULT NULL COMMENT '观看数',
  `like_count` int NULL DEFAULT NULL COMMENT '点赞数',
  `coin_count` int NULL DEFAULT NULL COMMENT '投币数',
  `favorite_count` int NULL DEFAULT NULL COMMENT '收藏数',
  `share_count` int NULL DEFAULT NULL COMMENT '分享数',
  `danmaku_count` int NULL DEFAULT NULL COMMENT '弹幕数',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '视频简介',
  `cover_url` varchar(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '封面图片URL',
  `scraped_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '数据更新时间',
  `last_analyzed_at` timestamp NULL DEFAULT NULL COMMENT '最后分析时间',
  `analysis_count` int NULL DEFAULT 0 COMMENT '分析次数',
  PRIMARY KEY (`bvid`) USING BTREE,
  UNIQUE INDEX `uk_aid`(`aid` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Triggers structure for table video_danmaku
-- ----------------------------
DROP TRIGGER IF EXISTS `sync_danmaku_time_insert`;
delimiter ;;
CREATE TRIGGER `sync_danmaku_time_insert` BEFORE INSERT ON `video_danmaku` FOR EACH ROW BEGIN
    -- 如果 appear_time 为空或为0，则从 dm_time 复制
    IF NEW.appear_time IS NULL OR NEW.appear_time = 0 THEN
        SET NEW.appear_time = NEW.dm_time;
    END IF;
    -- 如果 dm_time 为空或为0，则从 appear_time 复制
    IF NEW.dm_time IS NULL OR NEW.dm_time = 0 THEN
        SET NEW.dm_time = NEW.appear_time;
    END IF;
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table video_danmaku
-- ----------------------------
DROP TRIGGER IF EXISTS `sync_danmaku_time_update`;
delimiter ;;
CREATE TRIGGER `sync_danmaku_time_update` BEFORE UPDATE ON `video_danmaku` FOR EACH ROW BEGIN
    -- 如果更新了 dm_time，同步到 appear_time
    IF NEW.dm_time != OLD.dm_time THEN
        SET NEW.appear_time = NEW.dm_time;
    END IF;
    -- 如果更新了 appear_time，同步到 dm_time
    IF NEW.appear_time != OLD.appear_time THEN
        SET NEW.dm_time = NEW.appear_time;
    END IF;
END
;;
delimiter ;

SET FOREIGN_KEY_CHECKS = 1;
